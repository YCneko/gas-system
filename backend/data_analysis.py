"""
数据分析与特征工程脚本
- 从数据库读取过去3个月数据
- 计算VOCs浓度与温度、湿度、风速、设备负荷的皮尔逊相关系数
- 生成相关性热力图
- 提取时间特征、滞后特征、滚动统计特征
- 输出可用于模型训练的特征矩阵和标签向量
"""
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

DATABASE_URI = 'mysql+pymysql://root:123456@localhost:3306/gas_system?charset=utf8mb4'
LOOKBACK = 24
FORECAST_HORIZON = 6


def load_data():
    """从数据库读取过去3个月的数据并按小时合并多表"""
    engine = create_engine(DATABASE_URI)
    three_months_ago = datetime.now() - timedelta(days=90)

    emission_df = pd.read_sql(
        "SELECT timestamp, voc_concentration FROM emission_data WHERE timestamp >= %s",
        engine, params=(three_months_ago,)
    )
    weather_df = pd.read_sql(
        "SELECT timestamp, temperature, humidity, wind_speed FROM weather_data WHERE timestamp >= %s",
        engine, params=(three_months_ago,)
    )
    equipment_df = pd.read_sql(
        "SELECT timestamp, operating_load FROM equipment_data WHERE timestamp >= %s",
        engine, params=(three_months_ago,)
    )
    engine.dispose()

    if emission_df.empty:
        raise ValueError("排放数据为空，请确认数据库中包含过去3个月的 emission_data 记录")

    for df in [emission_df, weather_df, equipment_df]:
        df['hour'] = pd.to_datetime(df['timestamp']).dt.floor('h')

    emission_hourly = emission_df.groupby('hour')['voc_concentration'].mean().reset_index()

    if not weather_df.empty:
        weather_hourly = weather_df.groupby('hour').agg(
            {'temperature': 'mean', 'humidity': 'mean', 'wind_speed': 'mean'}
        ).reset_index()
    else:
        weather_hourly = pd.DataFrame(columns=['hour', 'temperature', 'humidity', 'wind_speed'])

    if not equipment_df.empty:
        equipment_hourly = equipment_df.groupby('hour')['operating_load'].mean().reset_index()
    else:
        equipment_hourly = pd.DataFrame(columns=['hour', 'operating_load'])

    merged = emission_hourly.copy()
    if not weather_hourly.empty:
        merged = merged.merge(weather_hourly, on='hour', how='left')
    else:
        for col in ['temperature', 'humidity', 'wind_speed']:
            merged[col] = np.nan
    if not equipment_hourly.empty:
        merged = merged.merge(equipment_hourly, on='hour', how='left')
    else:
        merged['operating_load'] = np.nan

    merged = merged.sort_values('hour').reset_index(drop=True)
    merged = merged.ffill().bfill().fillna(0)
    return merged


def correlation_analysis(df):
    """计算皮尔逊相关系数并生成热力图"""
    corr_vars = ['voc_concentration', 'temperature', 'humidity', 'wind_speed', 'operating_load']
    available = [c for c in corr_vars if c in df.columns]
    corr_matrix = df[available].corr()

    print("=" * 60)
    print("皮尔逊相关系数（与 VOCs 浓度）：")
    voc_corr = corr_matrix['voc_concentration'].drop('voc_concentration').sort_values(ascending=False)
    for var, val in voc_corr.items():
        direction = "正相关" if val > 0 else "负相关"
        strength = "强" if abs(val) > 0.6 else ("中等" if abs(val) > 0.3 else "弱")
        print(f"  {var:20s}: {val:+.4f}  ({direction}, {strength})")
    print("=" * 60)

    plt.figure(figsize=(9, 7))
    sns.heatmap(corr_matrix, annot=True, fmt='.3f', cmap='coolwarm',
                center=0, square=True, linewidths=0.5,
                vmin=-1, vmax=1)
    plt.title('VOCs浓度与气象/设备参数 — 皮尔逊相关性热力图', fontsize=14)
    plt.tight_layout()
    plt.savefig('correlation_heatmap.png', dpi=150, bbox_inches='tight')
    print("热力图已保存为 correlation_heatmap.png")
    return corr_matrix


def engineer_features(df):
    """
    特征工程：提取时间特征、滞后特征、滚动统计特征
    返回: X (3D array), y (2D array), scaler, feature_cols
    """
    from sklearn.preprocessing import StandardScaler

    df = df.copy()
    ts = pd.to_datetime(df['hour'])

    # 时间特征
    df['hour_sin'] = np.sin(2 * np.pi * ts.dt.hour / 24)
    df['hour_cos'] = np.cos(2 * np.pi * ts.dt.hour / 24)
    df['day_of_week_sin'] = np.sin(2 * np.pi * ts.dt.dayofweek / 7)
    df['day_of_week_cos'] = np.cos(2 * np.pi * ts.dt.dayofweek / 7)
    df['is_workday'] = (ts.dt.dayofweek < 5).astype(int)

    # 滞后特征：前1/3/6小时的VOCs浓度
    for lag in [1, 3, 6]:
        df[f'voc_lag_{lag}h'] = df['voc_concentration'].shift(lag)

    # 滚动统计特征：过去6小时的均值和标准差
    df['voc_rolling_6h_mean'] = df['voc_concentration'].shift(1).rolling(6, min_periods=1).mean()
    df['voc_rolling_6h_std'] = df['voc_concentration'].shift(1).rolling(6, min_periods=1).std().fillna(0)

    # 原始数值特征
    raw_features = ['temperature', 'humidity', 'wind_speed', 'operating_load']

    # 全部特征列
    feature_cols = (
        raw_features +
        ['hour_sin', 'hour_cos', 'day_of_week_sin', 'day_of_week_cos', 'is_workday'] +
        [f'voc_lag_{lag}h' for lag in [1, 3, 6]] +
        ['voc_rolling_6h_mean', 'voc_rolling_6h_std']
    )

    df = df.dropna().reset_index(drop=True)
    if len(df) < LOOKBACK + FORECAST_HORIZON + 10:
        raise ValueError(f"清洗后有效数据不足（仅 {len(df)} 行），需要至少 {LOOKBACK + FORECAST_HORIZON + 10} 行")

    # 构建标签（未来6小时VOCs浓度）
    for h in range(1, FORECAST_HORIZON + 1):
        df[f'target_{h}h'] = df['voc_concentration'].shift(-h)
    df = df.dropna().reset_index(drop=True)

    feature_data = df[feature_cols].values.astype(np.float32)
    target_cols = [f'target_{h}h' for h in range(1, FORECAST_HORIZON + 1)]
    target_data = df[target_cols].values.astype(np.float32)

    # 标准化
    scaler = StandardScaler()
    feature_data = scaler.fit_transform(feature_data)

    # 构建3D序列 (samples, lookback, features)
    X, y = [], []
    for i in range(len(df) - LOOKBACK + 1):
        X.append(feature_data[i:i + LOOKBACK])
        y.append(target_data[i + LOOKBACK - 1])
    X = np.array(X)
    y = np.array(y)

    print(f"特征矩阵 X 形状: {X.shape}  (样本数, 时间步, 特征数)")
    print(f"标签向量 y 形状: {y.shape}  (样本数, 预测步数)")
    print(f"特征列 ({len(feature_cols)}): {feature_cols}")
    return X, y, scaler, feature_cols


def main():
    print("=" * 60)
    print("  Gas System — 数据分析与特征工程")
    print("=" * 60)

    print("\n[1/3] 加载过去3个月数据...")
    df = load_data()
    print(f"  合并后数据量: {len(df)} 条小时记录")
    print(f"  时间范围: {df['hour'].min()} ~ {df['hour'].max()}")

    print("\n[2/3] 相关性分析...")
    correlation_analysis(df)

    print("\n[3/3] 特征工程...")
    X, y, scaler, feature_cols = engineer_features(df)
    print(f"  样本数: {X.shape[0]}, 时间步: {X.shape[1]}, 特征数: {X.shape[2]}")

    np.savez('engineered_features.npz', X=X, y=y, feature_cols=np.array(feature_cols, dtype=object))
    import joblib
    joblib.dump(scaler, 'scaler.pkl')
    print("\n特征矩阵和标签已保存到 engineered_features.npz")
    print("标准化器已保存到 scaler.pkl")


if __name__ == '__main__':
    main()
