from flask import Flask, request, jsonify
from extensions import db
import pandas as pd
import numpy as np
from datetime import datetime
from models import EmissionData, EquipmentData, WeatherData

import os

app = Flask(__name__)

_db_host = os.environ.get('DB_HOST', 'localhost')
_db_port = os.environ.get('DB_PORT', '3306')
_db_user = os.environ.get('DB_USER', 'root')
_db_pass = os.environ.get('DB_PASSWORD', '123456')
_db_name = os.environ.get('DB_NAME', 'gas_system')

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f'mysql+pymysql://{_db_user}:{_db_pass}@{_db_host}:{_db_port}/{_db_name}?charset=utf8mb4'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
}

db.init_app(app)

with app.app_context():
    db.create_all()

# 延迟加载预测器和告警模块（避免启动时因缺少模型文件而崩溃）
_predictor = None
_scaler = None
_feature_cols = None


def _get_predictor():
    global _predictor
    if _predictor is None:
        from predictor import VOCSPredictor
        _predictor = VOCSPredictor()
    return _predictor


def _get_scaler_and_cols():
    global _scaler, _feature_cols
    if _scaler is None:
        import joblib
        _scaler = joblib.load('scaler.pkl')
        _feature_cols = np.load('feature_cols.npy', allow_pickle=True).tolist()
    return _scaler, _feature_cols


def _build_feature_sequence():
    """从数据库获取最新数据并构建 LSTM 输入序列（分钟级对齐，≤1分钟误差）"""
    LOOKBACK = 24
    from sqlalchemy import desc

    # 基于最新记录时间，向前取 72 小时窗口（避免旧数据跨缺口混入）
    newest = EmissionData.query.order_by(desc(EmissionData.timestamp)).first()
    if not newest:
        return None, "排放数据为空"
    min_ts = newest.timestamp - pd.Timedelta(hours=72)

    emission_records = (EmissionData.query
                        .filter(EmissionData.timestamp >= min_ts)
                        .order_by(EmissionData.timestamp)
                        .all())
    if not emission_records:
        return None, "排放数据为空"

    max_ts = emission_records[-1].timestamp.replace(second=0, microsecond=0) + pd.Timedelta(minutes=1)

    # 批量查询气象和设备数据
    all_weather = (WeatherData.query
                   .filter(WeatherData.timestamp >= min_ts)
                   .filter(WeatherData.timestamp < max_ts)
                   .all())
    all_equipment = (EquipmentData.query
                     .filter(EquipmentData.timestamp >= min_ts)
                     .filter(EquipmentData.timestamp < max_ts)
                     .all())

    # 按分钟分组取均值（时序对齐误差 ≤1 分钟）
    def _minute_key(ts):
        return ts.replace(second=0, microsecond=0)

    # 排放数据按分钟预聚合（多传感器取均值，避免 drop_duplicates 丢数据）
    emission_by_min = {}
    for em in emission_records:
        k = _minute_key(em.timestamp)
        emission_by_min.setdefault(k, []).append(em)
    emission_avg = {k: np.mean([r.voc_concentration for r in recs if r.voc_concentration is not None])
                    if recs else 0 for k, recs in emission_by_min.items()}

    weather_by_min = {}
    for w in all_weather:
        k = _minute_key(w.timestamp)
        weather_by_min.setdefault(k, []).append(w)
    weather_avg = {k: {
        'temperature': np.mean([r.temperature for r in recs if r.temperature is not None]) if recs else None,
        'humidity': np.mean([r.humidity for r in recs if r.humidity is not None]) if recs else None,
        'wind_speed': np.mean([r.wind_speed for r in recs if r.wind_speed is not None]) if recs else None,
    } for k, recs in weather_by_min.items()}

    equipment_by_min = {}
    for e in all_equipment:
        k = _minute_key(e.timestamp)
        equipment_by_min.setdefault(k, []).append(e)
    equipment_avg = {k: np.mean([r.operating_load for r in recs if r.operating_load is not None])
                     if recs else None for k, recs in equipment_by_min.items()}

    # 收集所有分钟键，构建规整分钟级数据
    all_minutes = sorted(set(list(emission_avg.keys()) +
                             list(weather_avg.keys()) +
                             list(equipment_avg.keys())))

    rows = []
    for min_ts_key in all_minutes:
        w = weather_avg.get(min_ts_key, {})
        rows.append({
            'minute': min_ts_key,
            'voc_concentration': emission_avg.get(min_ts_key, 0),
            'temperature': w.get('temperature') or 0,
            'humidity': w.get('humidity') or 0,
            'wind_speed': w.get('wind_speed') or 0,
            'operating_load': equipment_avg.get(min_ts_key, 0),
        })

    df = pd.DataFrame(rows).sort_values('minute').reset_index(drop=True)

    # 降采样至小时级用于 LSTM（取小时均值）
    df['hour'] = pd.to_datetime(df['minute']).dt.floor('h')
    df = df.groupby('hour').agg({
        'voc_concentration': 'mean',
        'temperature': 'mean',
        'humidity': 'mean',
        'wind_speed': 'mean',
        'operating_load': 'mean',
    }).reset_index()

    if len(df) < LOOKBACK + 6:
        return None, f"有效数据不足（当前 {len(df)} 条，需要至少 {LOOKBACK + 6} 条）"

    ts = pd.to_datetime(df['hour'])
    df['hour_sin'] = np.sin(2 * np.pi * ts.dt.hour / 24)
    df['hour_cos'] = np.cos(2 * np.pi * ts.dt.hour / 24)
    df['day_of_week_sin'] = np.sin(2 * np.pi * ts.dt.dayofweek / 7)
    df['day_of_week_cos'] = np.cos(2 * np.pi * ts.dt.dayofweek / 7)
    df['is_workday'] = (ts.dt.dayofweek < 5).astype(int)

    for lag in [1, 3, 6]:
        df[f'voc_lag_{lag}h'] = df['voc_concentration'].shift(lag)

    df['voc_rolling_6h_mean'] = df['voc_concentration'].shift(1).rolling(6, min_periods=1).mean()
    df['voc_rolling_6h_std'] = df['voc_concentration'].shift(1).rolling(6, min_periods=1).std().fillna(0)

    raw_features = ['temperature', 'humidity', 'wind_speed', 'operating_load']
    all_features = (
        raw_features +
        ['hour_sin', 'hour_cos', 'day_of_week_sin', 'day_of_week_cos', 'is_workday'] +
        [f'voc_lag_{lag}h' for lag in [1, 3, 6]] +
        ['voc_rolling_6h_mean', 'voc_rolling_6h_std']
    )

    df = df.fillna(0)
    feature_data = df[all_features].values.astype(np.float32)

    scaler, _ = _get_scaler_and_cols()
    feature_data = scaler.transform(feature_data)

    sequence = feature_data[-LOOKBACK:]
    return sequence, None

# ---------- JSON 实时数据接口 ----------
@app.route('/api/data/realtime', methods=['POST'])
def realtime_data():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': '请求体必须是 JSON'}), 400

    data_type = data.get('data_type', '').lower()
    records = data.get('records', [])
    if data_type not in ('emission', 'equipment', 'weather'):
        return jsonify({'error': '缺少或无效的 data_type'}), 400
    if not isinstance(records, list) or len(records) == 0:
        return jsonify({'error': 'records 必须是非空列表'}), 400

    try:
        if data_type == 'emission':
            model = EmissionData
            required_fields = ['sensor_id', 'timestamp']
        elif data_type == 'equipment':
            model = EquipmentData
            required_fields = ['equipment_id', 'timestamp']
        else:
            model = WeatherData
            required_fields = ['station_id', 'timestamp']

        inserted = 0
        for idx, record in enumerate(records):
            missing = [f for f in required_fields if f not in record or record[f] is None]
            if missing:
                return jsonify({'error': f'第 {idx+1} 条记录缺少必填字段: {missing}'}), 400

            record['timestamp'] = pd.to_datetime(record['timestamp'])
            new_record = model(**{k: v for k, v in record.items() if k != 'id'})
            db.session.add(new_record)
            inserted += 1

        db.session.commit()
        return jsonify({'message': '实时数据接入成功', 'processed_records': inserted}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'数据处理失败: {str(e)}'}), 500

# ---------- VOCs 预测与预警接口 ----------
@app.route('/api/vocs/prediction', methods=['GET'])
def vocs_prediction():
    """获取未来6小时VOCs浓度预测及预警状态"""
    import time
    route_start = time.perf_counter()

    try:
        # 1. 构建特征序列
        sequence, err_msg = _build_feature_sequence()
        if sequence is None:
            return jsonify({'error': True, 'message': err_msg}), 400

        # 2. 调用预测器
        predictor = _get_predictor()
        pred_result = predictor.predict(sequence)

        if pred_result.get('error'):
            return jsonify({
                'error': True,
                'message': f"预测失败: {pred_result.get('message')}",
                'prediction_elapsed_ms': pred_result.get('elapsed_ms'),
            }), 500

        predictions = pred_result['predictions']

        # 3. 预警检查
        from alert import check_vocs_alert
        alert_result = check_vocs_alert(predictions)

        total_elapsed = round((time.perf_counter() - route_start) * 1000, 2)

        return jsonify({
            'error': False,
            'predictions': [
                {'hour': f'+{i + 1}h', 'voc_concentration': round(v, 2)}
                for i, v in enumerate(predictions)
            ],
            'prediction_elapsed_ms': pred_result.get('elapsed_ms'),
            'alert': {
                'triggered': alert_result.get('alert_triggered', False),
                'level': alert_result.get('alert_level'),
                'exceed_count': alert_result.get('exceed_count', 0),
                'records': alert_result.get('alert_records', []),
            },
            'total_elapsed_ms': total_elapsed,
        }), 200

    except FileNotFoundError as e:
        return jsonify({
            'error': True,
            'message': f"模型文件缺失: {str(e)}。请先运行 train_model.py 训练模型。",
        }), 503
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'服务器内部错误: {str(e)}',
        }), 500


# ---------- 前端兼容接口: GET /api/prediction ----------
@app.route('/api/prediction', methods=['GET'])
def prediction():
    """返回历史24小时 + 未来6小时预测数据（供 PredictionChart 使用）"""
    try:
        from sqlalchemy import desc

        # 获取最近 ~36 小时排放记录，按小时聚合（多传感器取均值，去重）
        newest = EmissionData.query.order_by(desc(EmissionData.timestamp)).first()
        if not newest:
            return jsonify({'history': [], 'prediction': [], 'alert': None}), 200

        since = newest.timestamp - pd.Timedelta(hours=36)
        raw = (EmissionData.query
               .filter(EmissionData.timestamp >= since)
               .order_by(EmissionData.timestamp)
               .all())

        # 按小时聚合（每小时一个点）
        hourly = {}
        for r in raw:
            h = r.timestamp.replace(minute=0, second=0, microsecond=0)
            hourly.setdefault(h, []).append(r.voc_concentration)

        history = [
            {'time': h.strftime('%m/%d %H:%M'), 'value': round(np.mean(vals), 1)}
            for h, vals in sorted(hourly.items())
            if vals and all(v is not None for v in vals)
        ][-24:]  # 最近24小时

        # 尝试预测，失败则返回空
        prediction = []
        alert_info = None
        try:
            sequence, _ = _build_feature_sequence()
            if sequence is not None:
                predictor = _get_predictor()
                pred_result = predictor.predict(sequence)
                if not pred_result.get('error'):
                    last_hour = sorted(hourly.keys())[-1] if hourly else newest.timestamp
                    for i, v in enumerate(pred_result['predictions']):
                        future_ts = last_hour + pd.Timedelta(hours=i + 1)
                        prediction.append({
                            'time': future_ts.strftime('%m/%d %H:%M'),
                            'value': round(v, 1),
                        })
                    # 触发预警检查（确保前端图表刷新时自动生成预警记录）
                    from alert import check_vocs_alert
                    alert_result = check_vocs_alert(pred_result['predictions'])
                    alert_info = {
                        'triggered': alert_result.get('alert_triggered', False),
                        'level': alert_result.get('alert_level'),
                        'exceed_count': alert_result.get('exceed_count', 0),
                    }
        except Exception:
            pass

        return jsonify({
            'history': history,
            'prediction': prediction,
            'alert': alert_info,
        }), 200

    except Exception as e:
        return jsonify({'error': True, 'message': str(e)}), 500


# ---------- 前端兼容接口: GET /api/realtime ----------
@app.route('/api/realtime', methods=['GET'])
def realtime():
    """返回最新的实时监测数据（供 DataCard 使用）"""
    try:
        from sqlalchemy import desc

        latest_em = EmissionData.query.order_by(desc(EmissionData.timestamp)).first()
        latest_weather = WeatherData.query.order_by(desc(WeatherData.timestamp)).first()

        return jsonify({
            'voc': round(latest_em.voc_concentration, 1) if latest_em and latest_em.voc_concentration else 0,
            'temp': round(latest_weather.temperature, 1) if latest_weather and latest_weather.temperature else 0,
            'humidity': round(latest_weather.humidity, 1) if latest_weather and latest_weather.humidity else 0,
            'wind': round(latest_weather.wind_speed, 1) if latest_weather and latest_weather.wind_speed else 0,
        }), 200

    except Exception as e:
        return jsonify({'error': True, 'message': str(e)}), 500


# ---------- 前端兼容接口: GET /api/alerts ----------
@app.route('/api/alerts', methods=['GET'])
def alerts():
    """返回预警记录列表（供 AlertList 使用）"""
    try:
        from sqlalchemy import desc
        from models import AlertRecord

        records = AlertRecord.query.order_by(desc(AlertRecord.alert_timestamp)).limit(50).all()

        level_map = {'高': 'error', '中': 'warn', '低': 'info'}

        now = datetime.utcnow()
        result = []
        for r in records:
            # 只返回预测超标时间在当前时间之后的预警（过滤已过期的历史预警）
            if r.predicted_exceedance_time and r.predicted_exceedance_time <= now:
                continue
            result.append({
                'id': r.id,
                'time': r.predicted_exceedance_time.strftime('%m/%d %H:%M') if r.predicted_exceedance_time else (r.alert_timestamp.strftime('%m/%d %H:%M') if r.alert_timestamp else ''),
                'metric': 'VOCs浓度',
                'level': level_map.get(r.alert_level, 'info'),
                'detail': f"预测超标时间: {r.predicted_exceedance_time.strftime('%m/%d %H:%M') if r.predicted_exceedance_time else ''}, 预测值: {r.predicted_value} mg/m³",
                'predicted_exceedance_time': r.predicted_exceedance_time.isoformat() if r.predicted_exceedance_time else '',
                'predicted_value': r.predicted_value or 0,
            })

        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': True, 'message': str(e)}), 500


# ---------- 前端兼容接口: GET /api/report/export ----------
@app.route('/api/report/export', methods=['GET'])
def report_export():
    """导出 CSV 报告（历史排放 + 气象数据）"""
    import io
    import csv

    try:
        from sqlalchemy import desc

        records = (EmissionData.query
                   .order_by(desc(EmissionData.timestamp))
                   .limit(500).all())
        records = sorted(records, key=lambda r: r.timestamp)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['时间', 'VOCs浓度(mg/m³)', 'NOx浓度(mg/m³)', 'SO2浓度(mg/m³)'])

        for r in records:
            writer.writerow([
                r.timestamp.strftime('%Y-%m-%d %H:%M:%S') if r.timestamp else '',
                r.voc_concentration or '',
                r.nox_concentration or '',
                r.so2_concentration or '',
            ])

        csv_content = output.getvalue()
        output.close()

        from flask import Response
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=gas_report.csv'},
        )

    except Exception as e:
        return jsonify({'error': True, 'message': str(e)}), 500




if __name__ == '__main__':
    # 启动时预热模型（避免首次请求冷启动超时）
    print("[init] 预加载模型...")
    try:
        _ = _get_predictor()
        _ = _get_scaler_and_cols()
        print("[init] 模型预加载完成")
    except Exception as e:
        print(f"[init] 模型预加载跳过: {e}")
    app.run(host='0.0.0.0', port=5000, debug=False)