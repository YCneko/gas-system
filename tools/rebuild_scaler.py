"""Rebuild scaler and feature_cols from current DB data"""
import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import StandardScaler
from extensions import db
from app import app
from models import EmissionData, WeatherData, EquipmentData

with app.app_context():
    newest = EmissionData.query.order_by(EmissionData.timestamp.desc()).first()
    if not newest:
        print("ERROR: no data")
        exit(1)
    min_ts = newest.timestamp - pd.Timedelta(hours=72)

    emissions = EmissionData.query.filter(EmissionData.timestamp >= min_ts).all()
    weathers = WeatherData.query.filter(WeatherData.timestamp >= min_ts).all()
    equipments = EquipmentData.query.filter(EquipmentData.timestamp >= min_ts).all()

    def mkey(ts):
        return ts.replace(second=0, microsecond=0)

    e_dict = {}
    for em in emissions:
        k = mkey(em.timestamp)
        e_dict.setdefault(k, []).append(em.voc_concentration or 0)
    e_avg = {k: np.mean(v) for k, v in e_dict.items()}

    w_dict = {}
    for w in weathers:
        k = mkey(w.timestamp)
        w_dict.setdefault(k, []).append(w)
    w_avg = {}
    for k, v in w_dict.items():
        w_avg[k] = {
            't': np.mean([r.temperature or 0 for r in v]),
            'h': np.mean([r.humidity or 0 for r in v]),
            'ws': np.mean([r.wind_speed or 0 for r in v]),
        }

    eq_dict = {}
    for eq in equipments:
        k = mkey(eq.timestamp)
        eq_dict.setdefault(k, []).append(eq.operating_load or 0)
    eq_avg = {k: np.mean(v) for k, v in eq_dict.items()}

    all_mins = sorted(set(list(e_dict.keys()) + list(w_dict.keys()) + list(eq_dict.keys())))

    rows = []
    for mk in all_mins:
        w = w_avg.get(mk, {})
        rows.append({
            'minute': mk,
            'voc_concentration': e_avg.get(mk, 0),
            'temperature': w.get('t', 0),
            'humidity': w.get('h', 0),
            'wind_speed': w.get('ws', 0),
            'operating_load': eq_avg.get(mk, 0),
        })

    df = pd.DataFrame(rows).sort_values('minute').reset_index(drop=True)
    df['hour'] = pd.to_datetime(df['minute']).dt.floor('h')
    df = df.groupby('hour').agg({
        'voc_concentration': 'mean',
        'temperature': 'mean',
        'humidity': 'mean',
        'wind_speed': 'mean',
        'operating_load': 'mean',
    }).reset_index()

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
        ['voc_lag_1h', 'voc_lag_3h', 'voc_lag_6h', 'voc_rolling_6h_mean', 'voc_rolling_6h_std']
    )

    df = df.fillna(0)
    feature_data = df[all_features].values.astype(np.float32)

    scaler = StandardScaler()
    scaler.fit(feature_data)
    joblib.dump(scaler, 'scaler.pkl')

    np.save('feature_cols.npy', np.array(all_features))

    print(f'OK: {len(df)} hourly rows, {feature_data.shape[1]} features')
    print(f'VOC range: {df["voc_concentration"].min():.1f} - {df["voc_concentration"].max():.1f}')
