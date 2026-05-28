import pandas as pd
import numpy as np
from typing import Tuple, List

def clean_dataframe(df: pd.DataFrame,
                    timestamp_col: str = 'timestamp',
                    value_cols: List[str] = None,
                    fill_method: str = 'ffill') -> Tuple[pd.DataFrame, float, float]:
    total_cells = df.size
    before_nan = df.isna().sum().sum()
    before_completeness = (1 - before_nan / total_cells) * 100 if total_cells else 100.0

    if value_cols is None:
        value_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    # 1. 时间戳列统一转换为 Timestamp，并填充缺失值
    if timestamp_col in df.columns:
        df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors='coerce')
        # 前向填充，若仍有 NaT 则后向填充
        df[timestamp_col] = df[timestamp_col].ffill().bfill()
        # 删除仍为 NaT 的行（极少情况）
        df = df.dropna(subset=[timestamp_col])

    # 2. 数值列缺失值处理
    for col in value_cols:
        if col in df.columns:
            if fill_method == 'ffill':
                df[col] = df[col].ffill()          # 新用法，替换 fillna(method='ffill')
            else:
                df[col] = df[col].fillna(df[col].mean())
            # 如果 ffill 后仍有 NaN（例如第一行就是 NaN），用均值填充
            if fill_method == 'ffill' and df[col].isna().any():
                df[col] = df[col].fillna(df[col].mean())

    # 3. 异常值处理（负值 -> NaN -> 线性插值）
    for col in value_cols:
        if col in df.columns:
            df[col] = df[col].mask(df[col] < 0, np.nan)
            df[col] = df[col].interpolate(method='linear', limit_direction='both')
            if df[col].isna().any():
                df[col] = df[col].fillna(df[col].mean())

    after_nan = df.isna().sum().sum()
    after_completeness = (1 - after_nan / total_cells) * 100 if total_cells else 100.0
    print(f"[清洗] 前完整性: {before_completeness:.2f}% → 后完整性: {after_completeness:.2f}%")
    return df, before_completeness, after_completeness