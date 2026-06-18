"""
刷新数据时间戳脚本
- 将所有数据表的时间戳平移到当前时间
- 清空旧预警记录
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))

from datetime import datetime, timedelta
from sqlalchemy import text
from extensions import db
from app import app

with app.app_context():
    # 1. 计算需要平移的小时数
    result = db.session.execute(text(
        "SELECT MAX(timestamp) FROM emission_data"
    )).fetchone()
    latest_ts = result[0]
    if not latest_ts:
        print("❌ 数据库无数据，请先导入数据")
        sys.exit(1)

    now = datetime.utcnow()
    # 让最新数据落在约 1 小时前（给预测留一点"历史"）
    target_latest = now - timedelta(hours=1)
    shift_hours = int((target_latest - latest_ts).total_seconds() / 3600)

    if shift_hours <= 0:
        print(f"✅ 数据已足够新鲜（最新: {latest_ts}, 现在: {now}）")
        sys.exit(0)

    print(f"📊 最新数据: {latest_ts}")
    print(f"🕐 当前时间: {now}")
    print(f"⏩ 平移 {shift_hours} 小时...")

    # 2. 更新各表时间戳
    interval = f"{shift_hours} HOUR"

    for table, time_col in [
        ('emission_data', 'timestamp'),
        ('weather_data', 'timestamp'),
        ('equipment_data', 'timestamp'),
    ]:
        result = db.session.execute(text(
            f"UPDATE {table} SET {time_col} = DATE_ADD({time_col}, INTERVAL {interval})"
        ))
        print(f"  ✅ {table}: {result.rowcount} 行已更新")

    # 3. 清空旧预警记录（基于旧数据产生的无意义）
    result = db.session.execute(text("DELETE FROM alert_records"))
    print(f"  ✅ alert_records: {result.rowcount} 行已清空")

    db.session.commit()

    # 4. 验证
    result = db.session.execute(text(
        "SELECT MIN(timestamp), MAX(timestamp) FROM emission_data"
    )).fetchone()
    print(f"\n🎉 完成！最新数据时间: {result[1]}")
    print(f"   数据跨度: {result[0]} ~ {result[1]}")
