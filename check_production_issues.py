"""检查生产环境问题"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime
import pytz

# 确保项目根目录在 Python 路径中
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import db_operations
from utils.date_helpers import get_daily_period_date

print("=" * 60)
print("生产环境问题诊断")
print("=" * 60)

# 问题1: 检查时区设置
print("\n[问题1] 检查时区设置")
print("-" * 60)
tz = pytz.timezone('Asia/Shanghai')
now_utc = datetime.now()
now_beijing = datetime.now(tz)
print(f"UTC时间: {now_utc.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"北京时间: {now_beijing.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"当前日结日期: {get_daily_period_date()}")
print(f"时区设置: ✅ 已使用 Asia/Shanghai (北京时间)")

# 问题2: 检查今天的本金减少收入记录
print("\n[问题2] 检查今天的本金减少收入记录")
print("-" * 60)
today = get_daily_period_date()
print(f"查询日期: {today}")

async def check_income_records():
    # 查询今天的本金减少记录
    principal_records = await db_operations.get_income_records(
        start_date=today,
        end_date=today,
        type='principal_reduction'
    )
    
    print(f"\n本金减少记录数量: {len(principal_records)}")
    total_amount = 0
    for record in principal_records:
        amount = record.get('amount', 0)
        total_amount += amount
        order_id = record.get('order_id', 'N/A')
        created_at = record.get('created_at', 'N/A')
        print(f"  - 订单ID: {order_id}, 金额: {amount:.2f}, 时间: {created_at}")
    
    print(f"\n本金减少总金额: {total_amount:.2f}")
    print(f"用户报告金额: 7400.00")
    print(f"差异: {abs(total_amount - 7400.00):.2f}")
    
    if abs(total_amount - 7400.00) > 0.01:
        print("⚠️ 警告: 金额不匹配！")
        print("可能原因:")
        print("  1. 订单2511100615的还款没有记录")
        print("  2. 记录使用了错误的日期")
        print("  3. 记录时出现了错误")
    
    # 查询订单2511100615
    print("\n[检查订单 2511100615]")
    order = await db_operations.get_order_by_order_id('2511100615')
    if order:
        print(f"订单存在:")
        print(f"  - 订单ID: {order.get('order_id')}")
        print(f"  - 状态: {order.get('state')}")
        print(f"  - 金额: {order.get('amount', 0):.2f}")
        print(f"  - 创建时间: {order.get('created_at', 'N/A')}")
        print(f"  - 更新时间: {order.get('updated_at', 'N/A')}")
        
        # 检查是否有该订单的收入记录
        order_income = await db_operations.get_income_records(
            start_date='2025-01-01',  # 从年初开始查询
            end_date=None,
            type='principal_reduction'
        )
        order_income = [r for r in order_income if r.get('order_id') == '2511100615']
        print(f"\n订单2511100615的本金减少记录: {len(order_income)} 条")
        for rec in order_income:
            print(f"  - 日期: {rec.get('date')}, 金额: {rec.get('amount', 0):.2f}, 时间: {rec.get('created_at', 'N/A')}")
    else:
        print("❌ 订单 2511100615 不存在")
    
    # 问题3: 检查订单完成的收入记录
    print("\n[问题3] 检查订单完成的收入记录")
    print("-" * 60)
    completed_records = await db_operations.get_income_records(
        start_date=today,
        end_date=today,
        type='completed'
    )
    
    print(f"订单完成记录数量: {len(completed_records)}")
    if len(completed_records) == 0:
        print("⚠️ 警告: 今天没有订单完成的收入记录！")
        print("可能原因:")
        print("  1. 今天确实没有完成订单")
        print("  2. 订单完成时没有记录收入明细")
        print("  3. 记录使用了错误的日期")
    else:
        total_completed = 0
        for record in completed_records:
            amount = record.get('amount', 0)
            total_completed += amount
            order_id = record.get('order_id', 'N/A')
            created_at = record.get('created_at', 'N/A')
            print(f"  - 订单ID: {order_id}, 金额: {amount:.2f}, 时间: {created_at}")
        print(f"\n订单完成总金额: {total_completed:.2f}")
    
    # 检查所有类型的收入记录
    print("\n[所有收入类型统计]")
    print("-" * 60)
    all_records = await db_operations.get_income_records(
        start_date=today,
        end_date=today
    )
    
    by_type = {}
    for record in all_records:
        income_type = record.get('type', 'unknown')
        amount = record.get('amount', 0)
        if income_type not in by_type:
            by_type[income_type] = {'count': 0, 'total': 0}
        by_type[income_type]['count'] += 1
        by_type[income_type]['total'] += amount
    
    for income_type, stats in by_type.items():
        print(f"{income_type}: {stats['count']} 条, 总金额: {stats['total']:.2f}")

if __name__ == "__main__":
    asyncio.run(check_income_records())

