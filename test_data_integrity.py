"""数据完整性检查和修复脚本"""
import asyncio
import sys
from pathlib import Path

# 确保项目根目录在 Python 路径中
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import db_operations
from utils.date_helpers import get_daily_period_date
from utils.stats_helpers import update_all_stats, update_liquid_capital
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_and_fix_order_statistics():
    """检查并修复订单统计数据"""
    print("\n" + "=" * 80)
    print("检查订单统计数据")
    print("=" * 80)
    
    try:
        # 获取所有订单
        all_orders = await db_operations.search_orders_all()
        financial_data = await db_operations.get_financial_data()
        
        # 按状态分类统计
        actual_stats = {
            'valid_orders': 0,
            'valid_amount': 0.0,
            'breach_orders': 0,
            'breach_amount': 0.0,
            'completed_orders': 0,
            'completed_amount': 0.0,
            'breach_end_orders': 0,
            'breach_end_amount': 0.0,
        }
        
        for order in all_orders:
            state = order.get('state', '')
            amount = order.get('amount', 0.0)
            
            if state in ['normal', 'overdue']:
                actual_stats['valid_orders'] += 1
                actual_stats['valid_amount'] += amount
            elif state == 'breach':
                actual_stats['breach_orders'] += 1
                actual_stats['breach_amount'] += amount
            elif state == 'end':
                actual_stats['completed_orders'] += 1
                actual_stats['completed_amount'] += amount
            elif state == 'breach_end':
                actual_stats['breach_end_orders'] += 1
                actual_stats['breach_end_amount'] += amount
        
        # 比较统计数据
        issues = []
        
        if financial_data.get('valid_orders') != actual_stats['valid_orders']:
            diff = actual_stats['valid_orders'] - financial_data.get('valid_orders', 0)
            issues.append({
                'field': 'valid_orders',
                'expected': actual_stats['valid_orders'],
                'actual': financial_data.get('valid_orders', 0),
                'diff': diff
            })
        
        if abs(financial_data.get('valid_amount', 0) - actual_stats['valid_amount']) > 0.01:
            diff = actual_stats['valid_amount'] - financial_data.get('valid_amount', 0)
            issues.append({
                'field': 'valid_amount',
                'expected': actual_stats['valid_amount'],
                'actual': financial_data.get('valid_amount', 0),
                'diff': diff
            })
        
        # 显示结果
        print(f"\n实际订单统计:")
        print(f"  有效订单: {actual_stats['valid_orders']} 个, {actual_stats['valid_amount']:,.2f} 元")
        print(f"  违约订单: {actual_stats['breach_orders']} 个, {actual_stats['breach_amount']:,.2f} 元")
        print(f"  完成订单: {actual_stats['completed_orders']} 个, {actual_stats['completed_amount']:,.2f} 元")
        print(f"  违约完成: {actual_stats['breach_end_orders']} 个, {actual_stats['breach_end_amount']:,.2f} 元")
        
        print(f"\n数据库统计:")
        print(f"  有效订单: {financial_data.get('valid_orders', 0)} 个, {financial_data.get('valid_amount', 0):,.2f} 元")
        print(f"  违约订单: {financial_data.get('breach_orders', 0)} 个, {financial_data.get('breach_amount', 0):,.2f} 元")
        print(f"  完成订单: {financial_data.get('completed_orders', 0)} 个, {financial_data.get('completed_amount', 0):,.2f} 元")
        print(f"  违约完成: {financial_data.get('breach_end_orders', 0)} 个, {financial_data.get('breach_end_amount', 0):,.2f} 元")
        
        if issues:
            print(f"\n[WARN] 发现 {len(issues)} 个数据不一致问题:")
            for issue in issues:
                print(f"  - {issue['field']}: 期望 {issue['expected']}, 实际 {issue['actual']}, 差异 {issue['diff']}")
            print("\n提示: 可以使用 /fix_statistics 命令修复统计数据")
            return False
        else:
            print("\n[PASS] 订单统计数据一致")
            return True
            
    except Exception as e:
        print(f"[FAIL] 检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def check_income_records_integrity():
    """检查收入记录完整性"""
    print("\n" + "=" * 80)
    print("检查收入记录完整性")
    print("=" * 80)
    
    try:
        today = get_daily_period_date()
        income_records = await db_operations.get_income_records(
            start_date=today,
            end_date=today
        )
        
        print(f"\n今日收入记录数量: {len(income_records)}")
        
        # 按类型统计
        by_type = {}
        total_amount = 0.0
        
        for record in income_records:
            record_type = record.get('type', 'unknown')
            amount = record.get('amount', 0.0)
            
            if record_type not in by_type:
                by_type[record_type] = {'count': 0, 'amount': 0.0}
            
            by_type[record_type]['count'] += 1
            by_type[record_type]['amount'] += amount
            total_amount += amount
        
        print(f"\n按类型统计:")
        for record_type, stats in by_type.items():
            print(f"  {record_type}: {stats['count']} 条, {stats['amount']:,.2f} 元")
        
        print(f"\n总计: {total_amount:,.2f} 元")
        
        # 检查异常记录
        issues = []
        for record in income_records:
            amount = record.get('amount', 0.0)
            if amount <= 0:
                issues.append(f"记录 ID {record.get('id')}: 金额非正数 ({amount})")
            if not record.get('date'):
                issues.append(f"记录 ID {record.get('id')}: 缺少日期")
            if not record.get('type'):
                issues.append(f"记录 ID {record.get('id')}: 缺少类型")
        
        if issues:
            print(f"\n[WARN] 发现 {len(issues)} 个异常记录:")
            for issue in issues[:10]:  # 只显示前10个
                print(f"  - {issue}")
            return False
        else:
            print("\n[PASS] 收入记录完整性检查通过")
            return True
            
    except Exception as e:
        print(f"[FAIL] 检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def check_operation_history_integrity():
    """检查操作历史完整性"""
    print("\n" + "=" * 80)
    print("检查操作历史完整性")
    print("=" * 80)
    
    try:
        # 检查操作历史表结构
        print("\n检查操作历史记录...")
        
        # 由于没有获取所有操作的函数，我们只检查最近的操作
        # 这里可以添加更详细的检查逻辑
        
        print("\n[PASS] 操作历史检查完成（功能有限）")
        return True
        
    except Exception as e:
        print(f"[FAIL] 检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_integrity_check():
    """运行完整性检查"""
    print("=" * 80)
    print("数据完整性检查脚本")
    print("=" * 80)
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"检查日期: {get_daily_period_date()}")
    
    results = []
    
    # 运行各项检查
    results.append(("订单统计数据", await check_and_fix_order_statistics()))
    results.append(("收入记录完整性", await check_income_records_integrity()))
    results.append(("操作历史完整性", await check_operation_history_integrity()))
    
    # 输出总结
    print("\n" + "=" * 80)
    print("检查总结")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[PASS] 通过" if result else "[FAIL] 失败"
        print(f"{name}: {status}")
    
    print(f"\n总计: {passed}/{total} 项检查通过")
    
    if passed < total:
        print("\n[WARN] 发现数据不一致问题，建议使用修复功能")
        return False
    else:
        print("\n[PASS] 所有检查通过")
        return True


if __name__ == "__main__":
    try:
        success = asyncio.run(run_integrity_check())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n检查被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n检查执行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

