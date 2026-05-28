"""
预警触发逻辑
- 接收未来6小时VOCs预测值数组
- 检查是否超过 80 mg/m³ 阈值
- 生成预警记录并存入数据库
- 超过3个预测值超标 → 预警等级为"高"
- 整个过程在 10 秒内完成
"""
import time
from datetime import datetime, timedelta
from extensions import db
from models import AlertRecord


def check_vocs_alert(predictions, base_timestamp=None):
    """
    检查 VOCs 预测值是否超标并生成预警记录。

    参数:
        predictions: list[float] — 未来6小时VOCs浓度预测值（共6个）
        base_timestamp: datetime — 预测基准时间，默认为当前时间

    返回:
        dict: {
            'error': False,
            'alert_triggered': bool,
            'alert_records': [...],
            'max_predicted_value': float,
            'elapsed_ms': float,
        }
    """
    start = time.perf_counter()
    base_ts = base_timestamp or datetime.utcnow()

    try:
        if not isinstance(predictions, (list, tuple)) or len(predictions) != 6:
            return {
                'error': True,
                'message': f'预测值格式错误，期望6个元素的列表，实际收到 {len(predictions) if isinstance(predictions, (list, tuple)) else type(predictions).__name__}',
                'alert_triggered': False,
                'alert_records': [],
                'elapsed_ms': 0,
            }

        THRESHOLD = 80.0
        exceed_indices = [i for i, v in enumerate(predictions) if v > THRESHOLD]

        if not exceed_indices:
            elapsed = (time.perf_counter() - start) * 1000
            return {
                'error': False,
                'alert_triggered': False,
                'alert_records': [],
                'max_predicted_value': max(predictions),
                'elapsed_ms': round(elapsed, 2),
            }

        # 确定预警等级
        n_exceed = len(exceed_indices)
        if n_exceed > 3:
            alert_level = '高'
        elif n_exceed >= 2:
            alert_level = '中'
        else:
            alert_level = '低'

        alert_records = []
        for i in exceed_indices:
            record = AlertRecord(
                alert_timestamp=datetime.utcnow(),
                predicted_exceedance_time=base_ts + timedelta(hours=i + 1),
                predicted_value=round(predictions[i], 2),
                alert_level=alert_level,
            )
            db.session.add(record)
            alert_records.append({
                'predicted_exceedance_time': (base_ts + timedelta(hours=i + 1)).isoformat(),
                'predicted_value': round(predictions[i], 2),
                'alert_level': alert_level,
            })

        db.session.commit()

        elapsed = (time.perf_counter() - start) * 1000
        return {
            'error': False,
            'alert_triggered': True,
            'alert_level': alert_level,
            'exceed_count': n_exceed,
            'alert_records': alert_records,
            'max_predicted_value': max(predictions),
            'elapsed_ms': round(elapsed, 2),
        }

    except Exception as e:
        db.session.rollback()
        elapsed = (time.perf_counter() - start) * 1000
        return {
            'error': True,
            'message': str(e),
            'alert_triggered': False,
            'alert_records': [],
            'elapsed_ms': round(elapsed, 2),
        }
