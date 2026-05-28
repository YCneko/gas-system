"""
VOCSPredictor — 模型服务封装类
- 初始化时加载训练好的 LSTM 模型
- predict(current_features) 返回未来6小时预测值
- 单次预测 < 2 秒
- 异常处理：预测失败时返回错误码而非崩溃
"""
import time
import numpy as np
import joblib
import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

ERROR_RESULT = {
    'error': True,
    'error_code': -1,
    'message': '预测失败',
    'predictions': None,
    'elapsed_ms': 0,
}


class VOCSPredictor:
    """VOCs 浓度预测器，封装 LSTM 模型的加载与推理"""

    def __init__(self, model_path='vocs_lstm_model.keras',
                 scaler_path='scaler.pkl',
                 feature_cols_path='feature_cols.npy'):
        self.model = None
        self.scaler = None
        self.feature_cols = None
        self.model_path = model_path
        self.scaler_path = scaler_path
        self.feature_cols_path = feature_cols_path
        self._load()

    def _load(self):
        """加载模型、标准化器和特征列名"""
        try:
            import tensorflow as tf
            self.model = tf.keras.models.load_model(self.model_path)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"模型文件未找到: {self.model_path}。请先运行 train_model.py 训练模型。"
            )
        except Exception as e:
            raise RuntimeError(f"模型加载失败: {str(e)}")

        try:
            self.scaler = joblib.load(self.scaler_path)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"标准化器未找到: {self.scaler_path}。请先运行 train_model.py 训练模型。"
            )

        if os.path.exists(self.feature_cols_path):
            self.feature_cols = np.load(self.feature_cols_path, allow_pickle=True).tolist()
        else:
            self.feature_cols = None

    def predict(self, current_features):
        """
        接收当前特征数组（形状: lookback × n_features），
        返回未来6小时的VOCs浓度预测值列表。

        参数:
            current_features: np.ndarray, shape = (lookback, n_features)
                             已标准化处理的特征序列

        返回:
            dict: {
                'error': False,
                'predictions': [float × 6],  # 未来6小时预测值
                'elapsed_ms': float           # 预测耗时(毫秒)
            }
            或
            dict: ERROR_RESULT (预测失败时)
        """
        start = time.perf_counter()

        try:
            if self.model is None:
                return {**ERROR_RESULT, 'message': '模型未加载'}

            features = np.asarray(current_features, dtype=np.float32)

            if features.ndim == 2:
                features = np.expand_dims(features, axis=0)

            if features.ndim != 3:
                return {**ERROR_RESULT, 'message': f'特征数组维度错误，期望 2D 或 3D，实际 {features.ndim}D'}

            predictions = self.model.predict(features, verbose=0)
            elapsed = (time.perf_counter() - start) * 1000

            pred_list = predictions[0].tolist()

            return {
                'error': False,
                'predictions': pred_list,
                'elapsed_ms': round(elapsed, 2),
            }

        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            return {
                **ERROR_RESULT,
                'message': str(e),
                'elapsed_ms': round(elapsed, 2),
            }
