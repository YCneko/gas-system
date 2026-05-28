from datetime import datetime
from extensions import db


class EmissionData(db.Model):
    __tablename__ = 'emission_data'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键ID')
    sensor_id = db.Column(db.String(50), nullable=False, comment='传感器ID')
    timestamp = db.Column(db.DateTime, nullable=False, comment='采样时间戳')
    voc_concentration = db.Column(db.Float, comment='VOCs浓度(μg/m³)')
    nox_concentration = db.Column(db.Float, comment='NOx浓度(μg/m³)')
    so2_concentration = db.Column(db.Float, comment='SO₂浓度(μg/m³)')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='记录创建时间')


class EquipmentData(db.Model):
    __tablename__ = 'equipment_data'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键ID')
    equipment_id = db.Column(db.String(50), nullable=False, comment='设备ID')
    timestamp = db.Column(db.DateTime, nullable=False, comment='记录时间戳')
    operating_load = db.Column(db.Float, comment='运行负荷(%)')
    production_phase = db.Column(db.String(50), comment='生产时段')
    status = db.Column(db.String(20), comment='设备状态')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='记录创建时间')


class WeatherData(db.Model):
    __tablename__ = 'weather_data'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键ID')
    station_id = db.Column(db.String(50), nullable=False, comment='气象站ID')
    timestamp = db.Column(db.DateTime, nullable=False, comment='观测时间戳')
    temperature = db.Column(db.Float, comment='温度(℃)')
    humidity = db.Column(db.Float, comment='相对湿度(%)')
    wind_speed = db.Column(db.Float, comment='风速(m/s)')
    wind_direction = db.Column(db.Float, comment='风向(度)')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='记录创建时间')


class AlertRecord(db.Model):
    """VOCs 预警记录表"""
    __tablename__ = 'alert_records'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键ID')
    alert_timestamp = db.Column(db.DateTime, default=datetime.utcnow, comment='预警生成时间戳')
    predicted_exceedance_time = db.Column(db.DateTime, nullable=False, comment='预测超标时间')
    predicted_value = db.Column(db.Float, nullable=False, comment='预测超标值(mg/m³)')
    alert_level = db.Column(db.String(10), nullable=False, comment='预警等级: 高/中/低')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='记录创建时间')