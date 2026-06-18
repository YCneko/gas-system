"""
真实数据导入脚本
===================
数据源: Dataset_TVOC_v2F.xlsx + Dataset_TVOC_v3.xlsx (2024-03 起的小时级数据)
目标: MySQL gas_system 数据库 (Docker gas_mysql 容器, 端口 13306)

功能:
  1. 合并两个 Excel 文件，统一列名映射
  2. 去重 (按 timestamp)、缺失值处理 (前向填充)
  3. 导入 EmissionData 和 WeatherData 表 (EquipmentData 不动)
  4. 避免插入重复数据 (按 sensor_id/station_id + timestamp 检查已存在记录)
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pymysql
from sqlalchemy import create_engine, text, Table, MetaData, select, and_
from sqlalchemy.orm import sessionmaker
import logging

# ============================================================
# 配置
# ============================================================
DATA_DIR = r"e:\文件\大二下作业\数据"
FILE_V2F = os.path.join(DATA_DIR, "Dataset_TVOC_v2F.xlsx")
FILE_V3 = os.path.join(DATA_DIR, "Dataset_TVOC_v3.xlsx")

DB_CONFIG = {
    "host": "localhost",
    "port": 13306,
    "user": "root",
    "password": "123456",
    "database": "gas_system",
    "charset": "utf8mb4",
}

SENSOR_ID = "SE3_real"
STATION_ID = "WS_real"

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ============================================================
# 1. 读取并合并两个 Excel 文件
# ============================================================
def load_and_merge():
    """读取两个 Excel 文件并合并为统一格式"""
    logger.info("=" * 60)
    logger.info("  读取 Excel 数据文件")
    logger.info("=" * 60)

    # --- 读取 V2F ---
    logger.info(f"读取 V2F: {FILE_V2F}")
    df_v2 = pd.read_excel(FILE_V2F)
    logger.info(f"  V2F: {len(df_v2)} 行, 列: {list(df_v2.columns)}")

    # V2F 列: DATE, HOUR, HEXANE, CH4, TOLUENE, NH4, ACETONE, CO, H2, TVOC, DV, VV, T, RH, PB, MONTH, WEEKEND, DAYTIME, SEASON
    df_v2 = df_v2.rename(columns={
        "DATE": "date_raw",
        "HOUR": "hour_raw",
        "TVOC": "tvoc",
        "T": "temperature",
        "RH": "humidity",
        "DV": "wind_direction",
        "VV": "wind_speed",
        "PB": "pressure",
    })
    # 只保留需要的列
    keep_cols = ["date_raw", "hour_raw", "tvoc", "temperature", "humidity",
                 "wind_direction", "wind_speed", "pressure"]
    df_v2 = df_v2[keep_cols].copy()
    df_v2["source"] = "v2f"

    # --- 读取 V3 ---
    logger.info(f"读取 V3: {FILE_V3}")
    df_v3 = pd.read_excel(FILE_V3)
    logger.info(f"  V3: {len(df_v3)} 行, 列: {list(df_v3.columns)}")

    # V3 列: Idsample, Date, Hour, Hexane, CH4, Toluene, NH4, Acetone, H2, TVOC, WD, WS, T, RH, BP, MONTH, WEEKEND, DAYTIME, SEASON
    df_v3 = df_v3.rename(columns={
        "Date": "date_raw",
        "Hour": "hour_raw",
        "TVOC": "tvoc",
        "T": "temperature",
        "RH": "humidity",
        "WD": "wind_direction",
        "WS": "wind_speed",
        "BP": "pressure",
    })
    df_v3 = df_v3[keep_cols].copy()
    df_v3["source"] = "v3"

    # --- 合并 ---
    df = pd.concat([df_v2, df_v3], ignore_index=True)
    logger.info(f"合并后总行数: {len(df)}")

    return df


# ============================================================
# 2. 数据清洗
# ============================================================
def clean_data(df):
    """处理 timestamp、去重、缺失值"""
    logger.info("=" * 60)
    logger.info("  数据清洗")
    logger.info("=" * 60)

    # 2.1 构建 timestamp
    # date_raw: datetime64 类型
    # hour_raw: 混合类型 —— 大部分是 datetime.time 对象，部分是 datetime.datetime (1900-01-01 ...)
    # 策略：统一转为字符串后只提取时间部分 (HH:MM:SS)，再与日期合并

    df["date_str"] = pd.to_datetime(df["date_raw"]).dt.strftime("%Y-%m-%d")

    # 将 hour_raw 统一转为字符串，提取时间部分
    hour_raw_str = df["hour_raw"].astype(str).str.strip()
    # 处理带日期的 datetime 字符串 (如 "1900-01-01 01:00:00")，只取时间部分
    df["hour_str"] = hour_raw_str.apply(
        lambda s: s.split()[-1] if " " in s else s
    )
    # 确保格式统一为 HH:MM:SS (处理 "1:00:00" 等变体)
    # 先尝试用 pd.to_timedelta 解析时间（最稳健）
    def _parse_time_str(s):
        """将时间字符串转为 HH:MM:SS 格式"""
        try:
            parts = s.strip().split(":")
            h = int(parts[0])
            m = int(parts[1]) if len(parts) > 1 else 0
            sec = int(parts[2]) if len(parts) > 2 else 0
            return f"{h:02d}:{m:02d}:{sec:02d}"
        except Exception:
            return "00:00:00"

    df["hour_str"] = df["hour_str"].apply(_parse_time_str)

    # 组合时间戳
    df["timestamp"] = pd.to_datetime(
        df["date_str"] + " " + df["hour_str"],
        format="%Y-%m-%d %H:%M:%S",
        errors="coerce"
    )

    # 检查解析失败的记录
    bad_ts = df["timestamp"].isna().sum()
    if bad_ts > 0:
        logger.warning(f"  {bad_ts} 条记录时间戳解析失败，已丢弃")
        df = df.dropna(subset=["timestamp"])

    df = df.drop(columns=["date_str", "hour_str", "date_raw", "hour_raw", "source"])

    # 2.2 排序
    df = df.sort_values("timestamp").reset_index(drop=True)

    # 2.3 去重 (按 timestamp，保留第一条)
    before_dedup = len(df)
    df = df.drop_duplicates(subset=["timestamp"], keep="first")
    logger.info(f"去重: {before_dedup} -> {len(df)} (减少 {before_dedup - len(df)} 条)")

    # 2.4 检查缺失值
    null_counts = df.isnull().sum()
    cols_with_null = null_counts[null_counts > 0]
    if len(cols_with_null) > 0:
        logger.info(f"缺失值统计:")
        for col, cnt in cols_with_null.items():
            logger.info(f"  {col}: {cnt} 个缺失值")

    # 2.5 前向填充 (forward fill) 处理缺失值
    df = df.ffill()
    # 如果开头有缺失，再后向填充
    df = df.bfill()

    still_null = df.isnull().sum().sum()
    if still_null > 0:
        logger.warning(f"  前向/后向填充后仍有 {still_null} 个缺失值，将填充为 0")
        df = df.fillna(0)

    logger.info(f"清洗后有效数据: {len(df)} 行")
    logger.info(f"时间范围: {df['timestamp'].min()} ~ {df['timestamp'].max()}")

    # 打印统计摘要
    for col in ["tvoc", "temperature", "humidity", "wind_speed", "wind_direction"]:
        if col in df.columns and not df[col].isna().all():
            logger.info(f"  {col:20s}: mean={df[col].mean():.2f}, "
                        f"min={df[col].min():.2f}, max={df[col].max():.2f}")

    return df


# ============================================================
# 3. 构建 EmissionData 和 WeatherData 格式
# ============================================================
def build_table_dataframes(df):
    """将合并后的数据拆分为 EmissionData 和 WeatherData 两个 DataFrame"""
    logger.info("=" * 60)
    logger.info("  构建目标表数据")
    logger.info("=" * 60)

    # --- EmissionData ---
    emission_df = pd.DataFrame({
        "sensor_id": SENSOR_ID,
        "timestamp": df["timestamp"],
        "voc_concentration": df["tvoc"].round(4),
        "nox_concentration": 0.0,
        "so2_concentration": 0.0,
    })
    logger.info(f"EmissionData: {len(emission_df)} 行")

    # --- WeatherData ---
    weather_df = pd.DataFrame({
        "station_id": STATION_ID,
        "timestamp": df["timestamp"],
        "temperature": df["temperature"].round(1),
        "humidity": df["humidity"].round(1),
        "wind_speed": df["wind_speed"].round(3),
        "wind_direction": df["wind_direction"].round(3),
    })
    logger.info(f"WeatherData:  {len(weather_df)} 行")

    return emission_df, weather_df


# ============================================================
# 4. 导入数据库
# ============================================================
def get_db_engine(db_config):
    """创建 SQLAlchemy engine，带重试"""
    conn_str = (
        f"mysql+pymysql://{db_config['user']}:{db_config['password']}"
        f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        f"?charset={db_config['charset']}"
    )

    max_retries = 5
    for attempt in range(1, max_retries + 1):
        try:
            engine = create_engine(
                conn_str,
                pool_pre_ping=True,
                pool_recycle=3600,
                connect_args={"connect_timeout": 10},
            )
            # 测试连接
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info(f"数据库连接成功 ({conn_str})")
            return engine
        except Exception as e:
            logger.warning(f"  第 {attempt}/{max_retries} 次连接失败: {e}")
            if attempt < max_retries:
                import time
                time.sleep(2)
            else:
                raise RuntimeError(f"无法连接数据库: {e}")


def get_existing_timestamps(engine, table_name, id_col, id_value):
    """查询数据库中已存在的 timestamp，避免重复插入"""
    query = text(
        f"SELECT timestamp FROM {table_name} WHERE {id_col} = :id_val"
    )
    with engine.connect() as conn:
        result = conn.execute(query, {"id_val": id_value})
        existing = {row[0] for row in result.fetchall()}
    return existing


def import_table(engine, df, table_name, id_col, id_value):
    """将 DataFrame 导入指定表，跳过已存在的 timestamp"""
    logger.info(f"\n导入 {table_name}...")

    # 查询已存在的 timestamp
    existing_ts = get_existing_timestamps(engine, table_name, id_col, id_value)
    logger.info(f"  数据库中已有 {len(existing_ts)} 条 {id_value} 记录")

    if existing_ts:
        # 过滤掉已存在的
        df_new = df[~df["timestamp"].isin(existing_ts)]
    else:
        df_new = df

    if len(df_new) == 0:
        logger.info(f"  所有数据已存在，无需导入")
        return 0

    logger.info(f"  待导入: {len(df_new)} 条 (新增)")

    # 批量插入 (每批 500 条)
    batch_size = 500
    total_inserted = 0

    for start in range(0, len(df_new), batch_size):
        batch = df_new.iloc[start:start + batch_size]
        try:
            batch.to_sql(
                table_name,
                engine,
                if_exists="append",
                index=False,
                method="multi",
                chunksize=batch_size,
            )
            total_inserted += len(batch)
            logger.info(f"    已插入 {total_inserted}/{len(df_new)} 条")
        except Exception as e:
            logger.error(f"    批量插入失败 (offset={start}): {e}")
            # 逐行回退尝试
            logger.info(f"    切换到单行插入模式...")
            for _, row in batch.iterrows():
                try:
                    row_df = row.to_frame().T
                    row_df.to_sql(
                        table_name,
                        engine,
                        if_exists="append",
                        index=False,
                    )
                    total_inserted += 1
                except Exception as row_err:
                    logger.warning(f"      跳过: timestamp={row['timestamp']}, 原因: {row_err}")

    return total_inserted


# ============================================================
# 5. 主流程
# ============================================================
def main():
    logger.info("=" * 60)
    logger.info("  真实数据导入工具")
    logger.info(f"  运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # Step 1: 检查 Docker 容器状态
    logger.info("\n检查 Docker 容器 gas_mysql 状态...")
    try:
        import subprocess
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=gas_mysql", "--format", "{{.Names}} {{.Status}}"],
            capture_output=True, text=True, timeout=10,
        )
        if "gas_mysql" in result.stdout:
            logger.info(f"  {result.stdout.strip()}")
        else:
            logger.warning("  gas_mysql 容器未在运行！请先启动容器")
            logger.warning("  尝试继续连接...")
    except FileNotFoundError:
        logger.warning("  未找到 docker 命令，跳过容器检查")
    except Exception as e:
        logger.warning(f"  容器检查异常: {e}")

    # Step 2: 加载数据
    try:
        df = load_and_merge()
    except FileNotFoundError as e:
        logger.error(f"数据文件不存在: {e}")
        logger.error(f"请确认以下文件存在:")
        logger.error(f"  - {FILE_V2F}")
        logger.error(f"  - {FILE_V3}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"数据加载失败: {e}")
        sys.exit(1)

    # Step 3: 清洗数据
    df = clean_data(df)

    if len(df) == 0:
        logger.error("清洗后无有效数据，终止")
        sys.exit(1)

    # Step 4: 构建表格式
    emission_df, weather_df = build_table_dataframes(df)

    # Step 5: 连接数据库并导入
    logger.info("\n" + "=" * 60)
    logger.info("  连接数据库并导入")
    logger.info("=" * 60)

    engine = get_db_engine(DB_CONFIG)

    try:
        # 导入 EmissionData
        n_emission = import_table(
            engine, emission_df, "emission_data", "sensor_id", SENSOR_ID
        )

        # 导入 WeatherData
        n_weather = import_table(
            engine, weather_df, "weather_data", "station_id", STATION_ID
        )

    except Exception as e:
        logger.error(f"导入过程发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        engine.dispose()

    # Step 6: 验证结果
    logger.info("\n" + "=" * 60)
    logger.info("  导入完成！验证结果:")
    logger.info("=" * 60)

    engine2 = get_db_engine(DB_CONFIG)
    with engine2.connect() as conn:
        # EmissionData 行数
        r = conn.execute(text(
            f"SELECT COUNT(*) FROM emission_data WHERE sensor_id = :sid"
        ), {"sid": SENSOR_ID}).fetchone()
        logger.info(f"  EmissionData ({SENSOR_ID}): {r[0]} 行")

        # WeatherData 行数
        r = conn.execute(text(
            f"SELECT COUNT(*) FROM weather_data WHERE station_id = :sid"
        ), {"sid": STATION_ID}).fetchone()
        logger.info(f"  WeatherData  ({STATION_ID}): {r[0]} 行")

        # 时间范围
        r = conn.execute(text(
            f"SELECT MIN(timestamp), MAX(timestamp) FROM emission_data WHERE sensor_id = :sid"
        ), {"sid": SENSOR_ID}).fetchone()
        logger.info(f"  排放数据时间范围: {r[0]} ~ {r[1]}")

        r = conn.execute(text(
            f"SELECT MIN(timestamp), MAX(timestamp) FROM weather_data WHERE station_id = :sid"
        ), {"sid": STATION_ID}).fetchone()
        logger.info(f"  气象数据时间范围: {r[0]} ~ {r[1]}")

    engine2.dispose()

    logger.info(f"\n新增导入: EmissionData {n_emission} 条, WeatherData {n_weather} 条")
    logger.info("完成！")


if __name__ == "__main__":
    main()
