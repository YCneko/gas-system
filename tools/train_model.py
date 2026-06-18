"""
LSTM 模型构建、训练与验证脚本
- 输入：多变量时间序列特征矩阵
- 输出：未来6小时VOCs浓度预测
- 2层LSTM + Dropout，MSE + Adam
- 时序划分：70%训练 / 15%验证 / 15%测试
- EarlyStopping + ModelCheckpoint
- 评估：MSE, MAE, R²，预测vs真实对比图
- 若 1-MAPE < 75%，输出调优建议
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import joblib
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from data_analysis import load_data, engineer_features

# 抑制 TensorFlow 冗余日志
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dropout, Dense
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.utils import plot_model

FORECAST_HORIZON = 6


def build_lstm_model(input_shape):
    """
    构建 LSTM 模型
    - 2层 LSTM + Dropout
    - 总参数量 < 50万
    """
    model = Sequential([
        LSTM(128, return_sequences=True, input_shape=input_shape, name='lstm_1'),
        Dropout(0.3, name='dropout_1'),
        LSTM(64, return_sequences=False, name='lstm_2'),
        Dropout(0.3, name='dropout_2'),
        Dense(32, activation='relu', name='dense_1'),
        Dense(FORECAST_HORIZON, name='output'),
    ])

    model.compile(loss='mse', optimizer=tf.keras.optimizers.Adam(learning_rate=0.001))
    return model


def split_time_series(X, y):
    """按时间顺序划分: 70% 训练 / 15% 验证 / 15% 测试"""
    n = len(X)
    train_end = int(n * 0.70)
    val_end = int(n * 0.85)

    X_train, y_train = X[:train_end], y[:train_end]
    X_val, y_val = X[train_end:val_end], y[train_end:val_end]
    X_test, y_test = X[val_end:], y[val_end:]

    print(f"数据划分: 训练集 {len(X_train)} | 验证集 {len(X_val)} | 测试集 {len(X_test)}")
    return X_train, y_train, X_val, y_val, X_test, y_test


def evaluate_model(model, X_test, y_test, scaler=None):
    """在测试集上评估，计算 MSE / MAE / R²"""
    y_pred = model.predict(X_test, verbose=0)

    mse = mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred.reshape(y_test.shape[0], -1))

    print("\n" + "=" * 60)
    print("  测试集评估结果")
    print("=" * 60)
    print(f"  MSE : {mse:.4f}")
    print(f"  MAE : {mae:.4f} mg/m³")
    print(f"  R²  : {r2:.4f}")
    print("=" * 60)

    # 计算 MAPE 及准确率
    y_test_nonzero = np.where(y_test == 0, 1e-6, y_test)
    mape = np.mean(np.abs((y_test - y_pred) / y_test_nonzero)) * 100
    accuracy = max(0, 1 - mape / 100)  # 1 - MAPE

    print(f"  MAPE     : {mape:.2f}%")
    print(f"  准确率   : {accuracy:.2%}")

    if accuracy < 0.75:
        print("\n" + "!" * 60)
        print("  模型准确率低于 75%，调优建议如下：")
        print("!" * 60)
        print("  1. 增加 LSTM 单元数（如 128 → 256），但需控制在 50 万参数内")
        print("  2. 加长回看窗口 LOOKBACK（如 24h → 48h / 72h）")
        print("  3. 添加更多滞后特征（前12h、前24h）")
        print("  4. 调整学习率（0.01 / 0.0005）或使用余弦衰减调度")
        print("  5. 使用 BatchNormalization + 更深的网络")
        print("  6. 扩充训练数据（若样本量不足）")
        print("  7. 对风速、负荷等特征单独做归一化处理")
        print("!" * 60)

    return y_pred, mse, mae, r2


def plot_predictions(y_test, y_pred, step=0):
    """绘制预测值与真实值对比图"""
    plt.figure(figsize=(12, 5))
    n_points = min(200, len(y_test))
    t = range(n_points)

    plt.plot(t, y_test[:n_points, step], 'b-', label=f'真实值 (t+{step + 1}h)', linewidth=1.5)
    plt.plot(t, y_pred[:n_points, step], 'r--', label=f'预测值 (t+{step + 1}h)', linewidth=1.2)
    plt.xlabel('测试样本序号')
    plt.ylabel('VOCs 浓度 (mg/m³)')
    plt.title(f'预测 vs 真实 — 未来第 {step + 1} 小时')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'prediction_vs_actual_t{step + 1}h.png', dpi=150, bbox_inches='tight')

    # 多步综合对比子图
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    for h in range(FORECAST_HORIZON):
        ax = axes[h // 3, h % 3]
        ax.plot(y_test[:n_points, h], 'b-', label='真实', linewidth=1)
        ax.plot(y_pred[:n_points, h], 'r--', label='预测', linewidth=1)
        ax.set_title(f'未来第 {h + 1} 小时')
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3)
    fig.suptitle('各预测步对比总览', fontsize=14)
    plt.tight_layout()
    plt.savefig('prediction_vs_actual_all.png', dpi=150, bbox_inches='tight')
    print("对比图已保存: prediction_vs_actual_t{1..6}h.png / prediction_vs_actual_all.png")


def main():
    print("=" * 60)
    print("  Gas System — LSTM 模型训练与验证")
    print("=" * 60)

    # 1. 加载数据 & 特征工程
    print("\n[1/5] 加载数据并执行特征工程...")
    df = load_data()
    X, y, scaler, feature_cols = engineer_features(df)

    # 2. 划分数据集
    print("\n[2/5] 按时间顺序划分数据集...")
    X_train, y_train, X_val, y_val, X_test, y_test = split_time_series(X, y)

    # 3. 构建模型
    print("\n[3/5] 构建 LSTM 模型...")
    input_shape = (X.shape[1], X.shape[2])
    model = build_lstm_model(input_shape)
    model.summary()

    total_params = model.count_params()
    print(f"总参数量: {total_params:,} {'[OK] (< 50万)' if total_params < 500000 else '[WARN] 超出 50 万!'}")

    # 模型结构可视化
    plot_model(model, to_file='model_architecture.png', show_shapes=True,
               show_layer_names=True, dpi=100)
    print("模型结构图已保存为 model_architecture.png")

    # 4. 训练
    print("\n[4/5] 开始训练...")
    callbacks = [
        EarlyStopping(monitor='val_loss', patience=15, restore_best_weights=True, verbose=1),
        ModelCheckpoint('best_model.keras', monitor='val_loss', save_best_only=True, verbose=1),
        tf.keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-6, verbose=1),
    ]

    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=200,
        batch_size=32,
        callbacks=callbacks,
        verbose=1,
    )

    # 训练曲线
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
    plt.tight_layout()
    plt.savefig('training_history.png', dpi=150, bbox_inches='tight')
    print("训练曲线图已保存为 training_history.png")

    # 加载最佳模型
    best_model = load_model('best_model.keras')

    # 5. 评估
    print("\n[5/5] 测试集评估...")
    y_pred, mse, mae, r2 = evaluate_model(best_model, X_test, y_test)
    plot_predictions(y_test, y_pred)

    # 保存模型和标准化器
    best_model.save('vocs_lstm_model.keras')
    joblib.dump(scaler, 'scaler.pkl')
    np.save('feature_cols.npy', np.array(feature_cols))
    print("\n模型已保存: vocs_lstm_model.keras / scaler.pkl / feature_cols.npy")


if __name__ == '__main__':
    main()
