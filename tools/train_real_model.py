"""
基于真实数据库数据训练 LSTM 模型
- 数据来源: MySQL (localhost:13306, gas_system)
- 14 特征（与 app.py _build_feature_sequence() 完全一致）
- LOOKBACK=24, FORECAST_HORIZON=6
- LSTM(128→64) + Dropout(0.2), MSE loss, Adam(0.001)
- 70/15/15 时间序列划分
- 输出: vocs_lstm_model.keras, scaler.pkl, feature_cols.npy
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import joblib
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sqlalchemy import create_engine

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dropout, Dense
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.optimizers import Adam

# ==================== 配置 ====================
LOOKBACK = 24
FORECAST_HORIZON = 6
DATABASE_URI = 'mysql+pymysql://root:123456@localhost:13306/gas_system?charset=utf8mb4'

# 特征列顺序必须与 app.py _build_feature_sequence() 中的 all_features 完全一致
RAW_FEATURES = ['temperature', 'humidity', 'wind_speed', 'operating_load']
TIME_FEATURES = ['hour_sin', 'hour_cos', 'day_of_week_sin', 'day_of_week_cos', 'is_workday']
LAG_FEATURES = ['voc_lag_1h', 'voc_lag_3h', 'voc_lag_6h']
ROLLING_FEATURES = ['voc_rolling_6h_mean', 'voc_rolling_6h_std']

FEATURE_COLS = RAW_FEATURES + TIME_FEATURES + LAG_FEATURES + ROLLING_FEATURES
# 确保是 14 个特征
assert len(FEATURE_COLS) == 14, f"特征列数量应为14，实际为{len(FEATURE_COLS)}"
# =============================================


def load_data_from_db():
    """从 MySQL 数据库加载排放、气象、设备数据，并对齐到小时级"""
    engine = create_engine(DATABASE_URI)

    # 加载全部数据（不做时间过滤，用全部历史数据训练）
    emission_df = pd.read_sql(
        "SELECT timestamp, voc_concentration FROM emission_data ORDER BY timestamp",
        engine
    )
    weather_df = pd.read_sql(
        "SELECT timestamp, temperature, humidity, wind_speed FROM weather_data ORDER BY timestamp",
        engine
    )
    equipment_df = pd.read_sql(
        "SELECT timestamp, operating_load FROM equipment_data ORDER BY timestamp",
        engine
    )
    engine.dispose()

    print(f"  排放数据: {len(emission_df)} 条")
    print(f"  气象数据: {len(weather_df)} 条")
    print(f"  设备数据: {len(equipment_df)} 条")

    # 按分钟对齐（与 app.py 逻辑一致：floor 到分钟）
    for df in [emission_df, weather_df, equipment_df]:
        df['minute'] = pd.to_datetime(df['timestamp']).dt.floor('min')

    # 排放数据按分钟聚合（多传感器取均值）
    emission_min = emission_df.groupby('minute')['voc_concentration'].mean().reset_index()

    # 气象数据按分钟聚合
    if not weather_df.empty:
        weather_min = weather_df.groupby('minute').agg(
            {'temperature': 'mean', 'humidity': 'mean', 'wind_speed': 'mean'}
        ).reset_index()
    else:
        weather_min = pd.DataFrame(columns=['minute', 'temperature', 'humidity', 'wind_speed'])

    # 设备数据按分钟聚合
    if not equipment_df.empty:
        equipment_min = equipment_df.groupby('minute')['operating_load'].mean().reset_index()
    else:
        equipment_min = pd.DataFrame(columns=['minute', 'operating_load'])

    # 按分钟合并
    merged = emission_min.copy()
    if not weather_min.empty:
        merged = merged.merge(weather_min, on='minute', how='left')
    else:
        for col in ['temperature', 'humidity', 'wind_speed']:
            merged[col] = np.nan
    if not equipment_min.empty:
        merged = merged.merge(equipment_min, on='minute', how='left')
    else:
        merged['operating_load'] = np.nan

    merged = merged.sort_values('minute').reset_index(drop=True)
    merged = merged.ffill().bfill().fillna(0)

    # 降采样至小时级（取小时均值）
    merged['hour'] = merged['minute'].dt.floor('h')
    hourly = merged.groupby('hour').agg({
        'voc_concentration': 'mean',
        'temperature': 'mean',
        'humidity': 'mean',
        'wind_speed': 'mean',
        'operating_load': 'mean',
    }).reset_index()

    print(f"  分钟级对齐: {len(merged)} 条 → 小时级: {len(hourly)} 条")
    print(f"  时间范围: {hourly['hour'].min()} ~ {hourly['hour'].max()}")
    return hourly


def engineer_features(df):
    """
    特征工程（与 app.py _build_feature_sequence() 完全一致）
    返回: X (3D array), y (2D array), scaler, feature_cols
    """
    df = df.copy()
    ts = pd.to_datetime(df['hour'])

    # --- 时间特征 ---
    df['hour_sin'] = np.sin(2 * np.pi * ts.dt.hour / 24)
    df['hour_cos'] = np.cos(2 * np.pi * ts.dt.hour / 24)
    df['day_of_week_sin'] = np.sin(2 * np.pi * ts.dt.dayofweek / 7)
    df['day_of_week_cos'] = np.cos(2 * np.pi * ts.dt.dayofweek / 7)
    df['is_workday'] = (ts.dt.dayofweek < 5).astype(int)

    # --- 滞后特征：前1/3/6小时的VOCs浓度 ---
    for lag in [1, 3, 6]:
        df[f'voc_lag_{lag}h'] = df['voc_concentration'].shift(lag)

    # --- 滚动统计特征：过去6小时的均值和标准差 ---
    df['voc_rolling_6h_mean'] = df['voc_concentration'].shift(1).rolling(6, min_periods=1).mean()
    df['voc_rolling_6h_std'] = df['voc_concentration'].shift(1).rolling(6, min_periods=1).std().fillna(0)

    # 删除含 NaN 的行（滞后特征导致前几行有 NaN）
    df = df.dropna().reset_index(drop=True)

    min_required = LOOKBACK + FORECAST_HORIZON + 10
    if len(df) < min_required:
        raise ValueError(f"清洗后有效数据不足（仅 {len(df)} 行），需要至少 {min_required} 行")

    # --- 构建标签（未来6小时VOCs浓度）---
    for h in range(1, FORECAST_HORIZON + 1):
        df[f'target_{h}h'] = df['voc_concentration'].shift(-h)
    df = df.dropna().reset_index(drop=True)

    feature_data = df[FEATURE_COLS].values.astype(np.float32)
    target_cols = [f'target_{h}h' for h in range(1, FORECAST_HORIZON + 1)]
    target_data = df[target_cols].values.astype(np.float32)

    # --- 标准化 ---
    scaler = StandardScaler()
    feature_data = scaler.fit_transform(feature_data)

    # --- 构建3D序列 (samples, lookback, features) ---
    X, y = [], []
    for i in range(len(df) - LOOKBACK + 1):
        X.append(feature_data[i:i + LOOKBACK])
        y.append(target_data[i + LOOKBACK - 1])
    X = np.array(X)
    y = np.array(y)

    print(f"  特征矩阵 X: {X.shape}  (样本数, 时间步, 特征数)")
    print(f"  标签向量 y: {y.shape}  (样本数, 预测步数)")
    print(f"  特征列 ({len(FEATURE_COLS)}): {FEATURE_COLS}")
    return X, y, scaler


def build_lstm_model(input_shape):
    """构建 LSTM(128→64) + Dropout(0.2) 模型"""
    model = Sequential([
        LSTM(128, return_sequences=True, input_shape=input_shape, name='lstm_1'),
        Dropout(0.2, name='dropout_1'),
        LSTM(64, return_sequences=False, name='lstm_2'),
        Dropout(0.2, name='dropout_2'),
        Dense(32, activation='relu', name='dense_1'),
        Dense(FORECAST_HORIZON, name='output'),
    ])
    model.compile(loss='mse', optimizer=Adam(learning_rate=0.001))
    return model


def split_time_series(X, y):
    """按时间顺序划分: 70% 训练 / 15% 验证 / 15% 测试"""
    n = len(X)
    train_end = int(n * 0.70)
    val_end = int(n * 0.85)

    X_train, y_train = X[:train_end], y[:train_end]
    X_val, y_val = X[train_end:val_end], y[train_end:val_end]
    X_test, y_test = X[val_end:], y[val_end:]

    print(f"  数据划分: 训练集 {len(X_train)} | 验证集 {len(X_val)} | 测试集 {len(X_test)}")
    return X_train, y_train, X_val, y_val, X_test, y_test


def evaluate_model(model, X_test, y_test):
    """在测试集上评估，计算 MSE / MAE / R² / MAPE"""
    y_pred = model.predict(X_test, verbose=0)

    mse = mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred.reshape(y_test.shape[0], -1))

    # MAPE
    y_test_safe = np.where(y_test == 0, 1e-6, y_test)
    mape = np.mean(np.abs((y_test - y_pred) / y_test_safe)) * 100

    print("\n" + "=" * 60)
    print("  测试集评估结果")
    print("=" * 60)
    print(f"  MSE  : {mse:.4f}")
    print(f"  MAE  : {mae:.4f} mg/m3")
    print(f"  R²   : {r2:.4f}")
    print(f"  MAPE : {mape:.2f}%")
    print("=" * 60)

    # 分步评估
    print("\n  各预测步 MAE / R²:")
    for h in range(FORECAST_HORIZON):
        step_mae = mean_absolute_error(y_test[:, h], y_pred[:, h])
        step_r2 = r2_score(y_test[:, h], y_pred[:, h])
        print(f"    未来第{h+1}h: MAE={step_mae:.2f}, R²={step_r2:.4f}")

    return y_pred, mse, mae, r2, mape


def plot_predictions(y_test, y_pred):
    """绘制预测 vs 真实对比图"""
    n_points = min(200, len(y_test))

    # 多步综合对比子图
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    for h in range(FORECAST_HORIZON):
        ax = axes[h // 3, h % 3]
        ax.plot(y_test[:n_points, h], 'b-', label='真实值', linewidth=1)
        ax.plot(y_pred[:n_points, h], 'r--', label='预测值', linewidth=1)
        ax.set_title(f'未来第 {h + 1} 小时')
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3)
    fig.suptitle('各预测步对比总览 (真实数据训练)', fontsize=14)
    plt.tight_layout()
    plt.savefig('prediction_vs_actual_real.png', dpi=150, bbox_inches='tight')
    print("\n  对比图已保存: prediction_vs_actual_real.png")


def plot_training_history(history):
    """绘制训练曲线"""
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].plot(history.history['loss'], label='训练损失')
    axes[0].plot(history.history['val_loss'], label='验证损失')
    axes[0].set_title('训练 / 验证损失曲线')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('MSE Loss')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    if 'lr' in history.history:
        axes[1].plot(history.history['lr'])
        axes[1].set_title('学习率变化')
        axes[1].set_xlabel('Epoch')
        axes[1].set_ylabel('Learning Rate')
        axes[1].set_yscale('log')
        axes[1].grid(True, alpha=0.3)
    else:
        axes[1].text(0.5, 0.5, '无学习率记录', ha='center', va='center', transform=axes[1].transAxes)
        axes[1].set_title('学习率变化')
    plt.tight_layout()
    plt.savefig('training_history_real.png', dpi=150, bbox_inches='tight')
    print("  训练曲线已保存: training_history_real.png")


def main():
    print("=" * 60)
    print("  Gas System — LSTM 真实数据训练")
    print("=" * 60)
    print(f"  LOOKBACK={LOOKBACK}, FORECAST_HORIZON={FORECAST_HORIZON}")
    print(f"  特征数: {len(FEATURE_COLS)}")
    print(f"  数据库: localhost:13306/gas_system")
    print("=" * 60)

    # 1. 加载数据
    print("\n[1/5] 从数据库加载数据...")
    df = load_data_from_db()

    # 2. 特征工程
    print("\n[2/5] 特征工程（与 app.py _build_feature_sequence 一致）...")
    X, y, scaler = engineer_features(df)

    # 3. 划分数据集
    print("\n[3/5] 按时间顺序划分数据集 (70/15/15)...")
    X_train, y_train, X_val, y_val, X_test, y_test = split_time_series(X, y)

    # 4. 构建并训练模型
    print("\n[4/5] 构建 LSTM(128→64) + Dropout(0.2) 模型...")
    input_shape = (X.shape[1], X.shape[2])
    model = build_lstm_model(input_shape)
    model.summary()

    total_params = model.count_params()
    print(f"  总参数量: {total_params:,}")

    callbacks = [
        EarlyStopping(monitor='val_loss', patience=20, restore_best_weights=True, verbose=1),
        ModelCheckpoint('best_model_real.keras', monitor='val_loss', save_best_only=True, verbose=1),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss', factor=0.5, patience=8, min_lr=1e-6, verbose=1
        ),
    ]

    print("  开始训练 (max 200 epochs, batch_size=32)...")
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=200,
        batch_size=32,
        callbacks=callbacks,
        verbose=1,
    )

    # 训练曲线
    plot_training_history(history)

    # 加载最佳模型
    best_model = load_model('best_model_real.keras')

    # 5. 评估
    print("\n[5/5] 测试集评估...")
    y_pred, mse, mae, r2, mape = evaluate_model(best_model, X_test, y_test)
    plot_predictions(y_test, y_pred)

    # 保存最终模型和预处理文件
    best_model.save('vocs_lstm_model.keras')
    joblib.dump(scaler, 'scaler.pkl')
    np.save('feature_cols.npy', np.array(FEATURE_COLS))
    print("\n" + "=" * 60)
    print("  模型文件已保存:")
    print("    vocs_lstm_model.keras")
    print("    scaler.pkl")
    print("    feature_cols.npy")
    print("=" * 60)

    # 基准指标输出
    print("\n  最终指标汇总:")
    print(f"    R²   = {r2:.4f}")
    print(f"    MAE  = {mae:.4f} mg/m³")
    print(f"    MAPE = {mape:.2f}%")
    print(f"    MSE  = {mse:.4f}")

    return r2, mae, mape


if __name__ == '__main__':
    main()
