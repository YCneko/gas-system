from flask import Flask, request, jsonify
from extensions import db
import pandas as pd
import numpy as np
from datetime import datetime
from models import EmissionData, EquipmentData, WeatherData
from data_cleaner import clean_dataframe

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost:3306/gas_system?charset=utf8mb4'
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
    """从数据库获取最新数据并构建 LSTM 输入序列"""
    LOOKBACK = 24
    from sqlalchemy import desc

    emission_records = (EmissionData.query
                        .order_by(desc(EmissionData.timestamp))
                        .limit(LOOKBACK + 12).all())
    if not emission_records:
        return None, "排放数据为空"

    emission_records = sorted(emission_records, key=lambda r: r.timestamp)
    min_ts = emission_records[0].timestamp.replace(minute=0, second=0, microsecond=0)
    max_ts = emission_records[-1].timestamp.replace(minute=0, second=0, microsecond=0) + pd.Timedelta(hours=1)

    # 批量查询气象和设备数据
    all_weather = (WeatherData.query
                   .filter(WeatherData.timestamp >= min_ts)
                   .filter(WeatherData.timestamp < max_ts)
                   .all())
    all_equipment = (EquipmentData.query
                     .filter(EquipmentData.timestamp >= min_ts)
                     .filter(EquipmentData.timestamp < max_ts)
                     .all())

    # 按小时分组取均值
    weather_by_hour = {}
    for w in all_weather:
        h = w.timestamp.replace(minute=0, second=0, microsecond=0)
        weather_by_hour.setdefault(h, []).append(w)
    weather_avg = {h: {
        'temperature': np.mean([r.temperature for r in recs if r.temperature is not None]) if recs else None,
        'humidity': np.mean([r.humidity for r in recs if r.humidity is not None]) if recs else None,
        'wind_speed': np.mean([r.wind_speed for r in recs if r.wind_speed is not None]) if recs else None,
    } for h, recs in weather_by_hour.items()}

    equipment_by_hour = {}
    for e in all_equipment:
        h = e.timestamp.replace(minute=0, second=0, microsecond=0)
        equipment_by_hour.setdefault(h, []).append(e)
    equipment_avg = {h: np.mean([r.operating_load for r in recs if r.operating_load is not None])
                     if recs else None for h, recs in equipment_by_hour.items()}

    rows = []
    for em in emission_records:
        hour_ts = em.timestamp.replace(minute=0, second=0, microsecond=0)
        w = weather_avg.get(hour_ts, {})
        eq_load = equipment_avg.get(hour_ts)

        rows.append({
            'hour': hour_ts,
            'voc_concentration': em.voc_concentration or 0,
            'temperature': w.get('temperature') or 0,
            'humidity': w.get('humidity') or 0,
            'wind_speed': w.get('wind_speed') or 0,
            'operating_load': eq_load if eq_load is not None else 0,
        })

    df = pd.DataFrame(rows).drop_duplicates(subset='hour').sort_values('hour').reset_index(drop=True)

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

# ---------- CSV 上传接口 ----------
ALLOWED_EXTENSIONS = {'csv'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/data/upload/csv', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({'error': '缺少文件'}), 400
    file = request.files['file']
    data_type = request.form.get('data_type', '').lower()
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': '无效文件，仅支持 .csv'}), 400
    if data_type not in ('emission', 'equipment', 'weather'):
        return jsonify({'error': '缺少或无效的 data_type，可选：emission, equipment, weather'}), 400

    try:
        df = pd.read_csv(file)
        if df.empty:
            return jsonify({'error': 'CSV 文件为空'}), 400

        if data_type == 'emission':
            value_cols = ['voc_concentration', 'nox_concentration', 'so2_concentration']
            model = EmissionData
        elif data_type == 'equipment':
            value_cols = ['operating_load']
            model = EquipmentData
        else:
            value_cols = ['temperature', 'humidity', 'wind_speed', 'wind_direction']
            model = WeatherData

        cleaned_df, before_pct, after_pct = clean_dataframe(df, value_cols=value_cols)

        records = []
        for _, row in cleaned_df.iterrows():
            record = {col: row[col] for col in cleaned_df.columns if col != 'id'}
            records.append(model(**record))

        db.session.add_all(records)
        db.session.commit()

        return jsonify({
            'message': '导入成功',
            'imported_rows': len(records),
            'before_completeness': round(before_pct, 2),
            'after_completeness': round(after_pct, 2)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'处理失败: {str(e)}'}), 500

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


if __name__ == '__main__':
    app.run(debug=True)