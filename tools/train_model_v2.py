"""
LSTM 模型训练 V2 — 改进版
优化点（基于 2024-2025 年 LSTM 时间序列研究最佳实践）：
1. MAE 损失函数（对 MAPE 更友好，减少百分比误差）
2. 更长回看窗口 LOOKBACK=48（捕捉更长的时序依赖）
3. 更多滞后特征（12h, 24h）
4. BatchNormalization 加速收敛
5. 更大 LSTM 单元（128→192, 64→96）
6. Huber 损失备选（MSE 和 MAE 的折中）
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import joblib
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from data_analysis import load_data, engineer_features

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dropout, Dense, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.optimizers import Adam

FORECAST_HORIZON = 6
LOOKBACK = 48  # V2: 24 → 48


def engineer_features_v2(df):
    """
    增强特征工程 V2：
    - 原始 14 维 + 额外滞后特征（12h, 24h）+ 更长滚动窗口（12h）
    """
    from sklearn.preprocessing import StandardScaler

    df = df.copy()
    ts = pd.to_datetime(df['hour'])

    # 时间特征（同 V1）
    df['hour_sin'] = np.sin(2 * np.pi * ts.dt.hour / 24)
    df['hour_cos'] = np.cos(2 * np.pi * ts.dt.hour / 24)
    df['day_of_week_sin'] = np.sin(2 * np.pi * ts.dt.dayofweek / 7)
    df['day_of_week_cos'] = np.cos(2 * np.pi * ts.dt.dayofweek / 7)
    df['is_workday'] = (ts.dt.dayofweek < 5).astype(int)

    # 滞后特征：V1(1h/3h/6h) + V2(12h/24h)
    for lag in [1, 3, 6, 12, 24]:
        df[f'voc_lag_{lag}h'] = df['voc_concentration'].shift(lag)

    # 滚动统计：V1(6h) + V2(12h)
    df['voc_rolling_6h_mean'] = df['voc_concentration'].shift(1).rolling(6, min_periods=1).mean()
    df['voc_rolling_6h_std'] = df['voc_concentration'].shift(1).rolling(6, min_periods=1).std().fillna(0)
    df['voc_rolling_12h_mean'] = df['voc_concentration'].shift(1).rolling(12, min_periods=1).mean()
    df['voc_rolling_12h_std'] = df['voc_concentration'].shift(1).rolling(12, min_periods=1).std().fillna(0)

    raw_features = ['temperature', 'humidity', 'wind_speed', 'operating_load']
    feature_cols = (
        raw_features +
        ['hour_sin', 'hour_cos', 'day_of_week_sin', 'day_of_week_cos', 'is_workday'] +
        ['voc_lag_1h', 'voc_lag_3h', 'voc_lag_6h', 'voc_lag_12h', 'voc_lag_24h'] +
        ['voc_rolling_6h_mean', 'voc_rolling_6h_std', 'voc_rolling_12h_mean', 'voc_rolling_12h_std']
    )

    df = df.dropna().reset_index(drop=True)
    min_required = LOOKBACK + FORECAST_HORIZON + 10
    if len(df) < min_required:
        raise ValueError(f"清洗后有效数据不足（仅 {len(df)} 行），需要至少 {min_required} 行")

    for h in range(1, FORECAST_HORIZON + 1):
        df[f'target_{h}h'] = df['voc_concentration'].shift(-h)
    df = df.dropna().reset_index(drop=True)

    feature_data = df[feature_cols].values.astype(np.float32)
    target_cols = [f'target_{h}h' for h in range(1, FORECAST_HORIZON + 1)]
    target_data = df[target_cols].values.astype(np.float32)

    scaler = StandardScaler()
    feature_data = scaler.fit_transform(feature_data)

    X, y = [], []
    for i in range(len(df) - LOOKBACK + 1):
        X.append(feature_data[i:i + LOOKBACK])
        y.append(target_data[i + LOOKBACK - 1])
    X = np.array(X)
    y = np.array(y)

    print(f"特征矩阵 X: {X.shape}, y: {y.shape}")
    print(f"特征列 ({len(feature_cols)}): {feature_cols}")
    return X, y, scaler, feature_cols


def build_lstm_v2(input_shape, loss='mae'):
    """
    V2 LSTM: 更大单元 + BatchNormalization
    loss 可选 'mae' (推荐) / 'mse' / 'huber'
    """
    model = Sequential([
        LSTM(192, return_sequences=True, input_shape=input_shape, name='lstm_1'),
        BatchNormalization(name='bn_1'),
        Dropout(0.3, name='dropout_1'),
        LSTM(96, return_sequences=False, name='lstm_2'),
        BatchNormalization(name='bn_2'),
        Dropout(0.3, name='dropout_2'),
        Dense(48, activation='relu', name='dense_1'),
        Dense(FORECAST_HORIZON, name='output'),
    ])

    if loss == 'huber':
        loss_fn = tf.keras.losses.Huber(delta=1.0)
    else:
        loss_fn = loss

    model.compile(loss=loss_fn, optimizer=Adam(learning_rate=0.001))
    return model


def split_time_series(X, y):
    n = len(X)
    train_end = int(n * 0.70)
    val_end = int(n * 0.85)
    X_train, y_train = X[:train_end], y[:train_end]
    X_val, y_val = X[train_end:val_end], y[train_end:val_end]
    X_test, y_test = X[val_end:], y[val_end:]
    print(f"数据划分: 训练 {len(X_train)} | 验证 {len(X_val)} | 测试 {len(X_test)}")
    return X_train, y_train, X_val, y_val, X_test, y_test


def evaluate_model(model, X_test, y_test):
    y_pred = model.predict(X_test, verbose=0)
    mse = mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred.reshape(y_test.shape[0], -1))
    print(f"\n{'='*60}")
    print(f"  测试集评估")
    print(f"{'='*60}")
    print(f"  MSE : {mse:.4f}")
    print(f"  MAE : {mae:.4f} mg/m³")
    print(f"  R²  : {r2:.4f}")
    y_test_safe = np.where(y_test == 0, 1e-6, y_test)
    mape = np.mean(np.abs((y_test - y_pred) / y_test_safe)) * 100
    accuracy = max(0, 1 - mape / 100)
    print(f"  MAPE: {mape:.2f}%")
    print(f"  准确率: {accuracy:.2%}")
    if accuracy >= 0.75:
        print(f"  >>> 达标！准确率 >= 75% <<<")
    return y_pred, mse, mae, r2, accuracy


def main():
    print("=" * 60)
    print("  Gas System — LSTM V2 训练 (MAE + 48步 + BN)")
    print("=" * 60)

    print("\n[1/5] 加载数据...")
    df = load_data()
    print(f"  数据: {len(df)} 条小时记录")

    print("\n[2/5] 增强特征工程 V2...")
    X, y, scaler, feature_cols = engineer_features_v2(df)

    print("\n[3/5] 构建 LSTM V2...")
    X_train, y_train, X_val, y_val, X_test, y_test = split_time_series(X, y)
    input_shape = (X.shape[1], X.shape[2])
    model = build_lstm_v2(input_shape, loss='mae')
    model.summary()
    print(f"总参数量: {model.count_params():,}")

    print(f"\n[4/5] 训练 (max 200 epochs)...")
    callbacks = [
        EarlyStopping(monitor='val_loss', patience=20, restore_best_weights=True, verbose=1),
        ModelCheckpoint('best_model_v2.keras', monitor='val_loss', save_best_only=True, verbose=1),
        tf.keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=8, min_lr=1e-6, verbose=1),
    ]

    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=200, batch_size=32,
        callbacks=callbacks, verbose=1,
    )

    # 训练曲线
    fig, ax = plt.subplots(1, 1, figsize=(10, 5))
    ax.plot(history.history['loss'], label='train loss')
    ax.plot(history.history['val_loss'], label='val loss')
    ax.set_title('Training Curve (MAE Loss)')
    ax.set_xlabel('Epoch'); ax.set_ylabel('MAE')
    ax.legend(); ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('training_history_v2.png', dpi=150)
    print("训练曲线: training_history_v2.png")

    best_model = load_model('best_model_v2.keras')

    print("\n[5/5] 评估...")
    y_pred, mse, mae, r2, acc = evaluate_model(best_model, X_test, y_test)

    # 对比 V1 模型（如果存在）
    print(f"\n--- 模型对比 ---")
    print(f"  V2 (MAE+48步+BN): R²={r2:.4f}, MAE={mae:.2f}, MAPE准确率={acc:.2%}")
    try:
        v1_model = load_model('vocs_lstm_model.keras')
        v1_pred = v1_model.predict(X_test, verbose=0)
        v1_mae = mean_absolute_error(y_test, v1_pred)
        v1_r2 = r2_score(y_test, v1_pred.reshape(y_test.shape[0], -1))
        print(f"  V1 (MSE+24步)   : R²={v1_r2:.4f}, MAE={v1_mae:.2f}")
    except:
        print(f"  V1 模型不可用，跳过对比")

    # 保存
    best_model.save('vocs_lstm_model_v2.keras')
    joblib.dump(scaler, 'scaler_v2.pkl')
    np.save('feature_cols_v2.npy', np.array(feature_cols))
    print(f"\nV2 模型已保存: vocs_lstm_model_v2.keras / scaler_v2.pkl / feature_cols_v2.npy")


if __name__ == '__main__':
    import pandas as pd
    main()
