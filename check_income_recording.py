"""检查收入记录问题"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pytz

# 确保项目根目录在 Python 路径中
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import db_operations
from utils.date_helpers import get_daily_period_date

async def check_all_issues():
    print("=" * 60)
    print("生产环境问题检查")
    print("=" * 60)
    
    # 问题1: 检查时区
    print("\n[问题1] 时区检查")
    print("-" * 60)
    tz = pytz.timezone('Asia/Shanghai')
    now_utc = datetime.now()
    now_beijing = datetime.now(tz)
    print(f"UTC时间: {now_utc.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"北京时间: {now_beijing.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"当前日结日期: {get_daily_period_date()}")
    
    # 检查最近7天的收入记录
    print("\n[问题2] 检查最近7天的收入记录")
    print("-" * 60)
    today = get_daily_period_date()
    start_date = (datetime.strptime(today, "%Y-%m-%d") - timedelta(days=7)).strftime("%Y-%m-%d")
    
    all_records = await db_operations.get_income_records(
        start_date=start_date,
        end_date=today
    )
    
    print(f"查询日期范围: {start_date} 至 {today}")
    print(f"总记录数: {len(all_records)}")
    
    # 按日期和类型分组
    by_date_type = {}
    for record in all_records:
        date_key = record.get('date', 'unknown')
        type_key = record.get('type', 'unknown')
        key = f"{date_key}_{type_key}"
        if key not in by_date_type:
            by_date_type[key] = []
        by_date_type[key].append(record)
    
    # 显示今天的记录
    print(f"\n今天的收入记录:")
    today_records = [r for r in all_records if r.get('date') == today]
    if today_records:
        by_type = {}
        for record in today_records:
            income_type = record.get('type', 'unknown')
            if income_type not in by_type:
                by_type[income_type] = []
            by_type[income_type].append(record)
        
        for income_type, records in by_type.items():
            total = sum(r.get('amount', 0) for r in records)
            print(f"  {income_type}: {len(records)} 条, 总金额: {total:.2f}")
            for r in records:
                print(f"    - 订单: {r.get('order_id', 'N/A')}, 金额: {r.get('amount', 0):.2f}, 时间: {r.get('created_at', 'N/A')}")
    else:
        print("  ❌ 今天没有任何收入记录！")
    
    # 检查订单2511100615的所有收入记录
    print(f"\n[检查订单 2511100615]")
    print("-" * 60)
    order_income = [r for r in all_records if r.get('order_id') == '2511100615']
    print(f"订单2511100615的收入记录: {len(order_income)} 条")
    if order_income:
        for r in order_income:
            print(f"  - 类型: {r.get('type')}, 金额: {r.get('amount', 0):.2f}, 日期: {r.get('date')}, 时间: {r.get('created_at', 'N/A')}")
    else:
        print("  ❌ 订单2511100615没有任何收入记录！")
        print("  可能原因:")
        print("    1. 本金减少操作时没有记录收入")
        print("    2. 记录时使用了错误的日期")
        print("    3. 记录时出现了错误")
    
    # 检查所有订单完成的记录
    print(f"\n[检查订单完成记录]")
    print("-" * 60)
    completed_records = [r for r in all_records if r.get('type') == 'completed']
    print(f"订单完成记录总数: {len(completed_records)}")
    if completed_records:
        # 按日期分组
        by_date = {}
        for r in completed_records:
            date_key = r.get('date', 'unknown')
            if date_key not in by_date:
                by_date[date_key] = []
            by_date[date_key].append(r)
        
        for date_key in sorted(by_date.keys(), reverse=True)[:5]:  # 显示最近5天
            records = by_date[date_key]
            total = sum(r.get('amount', 0) for r in records)
            print(f"  {date_key}: {len(records)} 条, 总金额: {total:.2f}")
    else:
        print("  ❌ 没有任何订单完成记录！")
        print("  可能原因:")
        print("    1. 订单完成时没有记录收入")
        print("    2. 记录时出现了错误")

if __name__ == "__main__":
    asyncio.run(check_all_issues())

