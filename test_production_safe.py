"""生产环境安全测试脚本 - 只读模式，不会修改任何数据"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# 确保项目根目录在 Python 路径中
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import db_operations
from utils.date_helpers import get_daily_period_date
import json
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 只读模式标志
READ_ONLY_MODE = True

# 测试数据（仅用于读取，不会使用这些ID进行写入）
TEST_USER_ID = 123456789
TEST_CHAT_ID_GROUP = -1001234567890
TEST_CHAT_ID_PRIVATE = 123456789


class TestResult:
    """测试结果类"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.warnings = []
    
    def add_pass(self, test_name: str):
        self.passed += 1
        print(f"[PASS] {test_name}")
    
    def add_fail(self, test_name: str, error: str):
        self.failed += 1
        self.errors.append(f"{test_name}: {error}")
        print(f"[FAIL] {test_name}: {error}")
    
    def add_warning(self, test_name: str, warning: str):
        self.warnings.append(f"{test_name}: {warning}")
        print(f"[WARN] {test_name}: {warning}")
    
    def summary(self):
        print("\n" + "=" * 80)
        print("测试总结")
        print("=" * 80)
        print(f"[PASS] 通过: {self.passed}")
        print(f"[FAIL] 失败: {self.failed}")
        print(f"[WARN] 警告: {len(self.warnings)}")
        
        if self.errors:
            print("\n错误列表:")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print("\n警告列表:")
            for warning in self.warnings[:10]:  # 只显示前10个警告
                print(f"  - {warning}")
        
        print("=" * 80)
        return self.failed == 0


async def verify_data_consistency_readonly(result: TestResult):
    """验证数据一致性（只读模式）"""
    print("\n" + "=" * 80)
    print("数据一致性验证（只读模式）")
    print("=" * 80)
    
    # 1. 验证财务数据一致性
    print("\n[1] 验证财务数据一致性...")
    try:
        financial_data = await db_operations.get_financial_data()
        
        if not financial_data:
            result.add_fail("财务数据一致性", "无法获取财务数据")
            return
        
        # 验证金额字段都是数字
        required_fields = [
            'valid_amount', 'liquid_funds', 'new_clients_amount',
            'old_clients_amount', 'interest', 'completed_amount',
            'breach_amount', 'breach_end_amount'
        ]
        
        all_valid = True
        for field in required_fields:
            value = financial_data.get(field, 0)
            if not isinstance(value, (int, float)):
                result.add_fail(f"财务数据字段 {field}", f"不是数字类型: {type(value)}")
                all_valid = False
            elif value < 0 and field != 'liquid_funds':  # liquid_funds 可以为负数
                result.add_warning(f"财务数据字段 {field}", f"值为负数: {value}")
        
        if all_valid:
            result.add_pass("财务数据一致性检查")
    except Exception as e:
        result.add_fail("财务数据一致性检查", str(e))
    
    # 2. 验证订单状态一致性
    print("\n[2] 验证订单状态一致性...")
    try:
        all_orders = await db_operations.search_orders_all()
        
        valid_states = ['normal', 'overdue', 'breach', 'end', 'breach_end']
        invalid_orders = [o for o in all_orders if o.get('state') not in valid_states]
        
        if invalid_orders:
            result.add_fail("订单状态一致性", f"发现 {len(invalid_orders)} 个无效状态的订单")
            for order in invalid_orders[:5]:  # 只显示前5个
                print(f"  - 订单 {order.get('order_id')}: 状态 {order.get('state')}")
        else:
            result.add_pass("订单状态一致性检查")
    except Exception as e:
        result.add_fail("订单状态一致性检查", str(e))
    
    # 3. 验证收入记录完整性
    print("\n[3] 验证收入记录完整性...")
    try:
        today = get_daily_period_date()
        income_records = await db_operations.get_income_records(
            start_date=today,
            end_date=today
        )
        
        # 验证每条记录都有必需的字段
        invalid_records = []
        for record in income_records:
            required_fields = ['type', 'amount', 'date']
            missing = [f for f in required_fields if not record.get(f)]
            if missing:
                invalid_records.append({
                    'id': record.get('id'),
                    'missing': missing
                })
        
        if invalid_records:
            result.add_fail("收入记录完整性", f"发现 {len(invalid_records)} 条不完整的记录")
        else:
            result.add_pass("收入记录完整性检查")
    except Exception as e:
        result.add_fail("收入记录完整性检查", str(e))


async def verify_data_correctness_readonly(result: TestResult):
    """验证数据正确性（只读模式）"""
    print("\n" + "=" * 80)
    print("数据正确性验证（只读模式）")
    print("=" * 80)
    
    # 1. 验证订单统计正确性
    print("\n[1] 验证订单统计正确性...")
    try:
        all_orders = await db_operations.search_orders_all()
        financial_data = await db_operations.get_financial_data()
        
        # 计算实际统计
        actual_valid = [o for o in all_orders if o.get('state') in ['normal', 'overdue']]
        actual_breach = [o for o in all_orders if o.get('state') == 'breach']
        actual_completed = [o for o in all_orders if o.get('state') == 'end']
        actual_breach_end = [o for o in all_orders if o.get('state') == 'breach_end']
        
        actual_valid_count = len(actual_valid)
        actual_valid_amount = sum(o.get('amount', 0) for o in actual_valid)
        actual_breach_count = len(actual_breach)
        actual_breach_amount = sum(o.get('amount', 0) for o in actual_breach)
        actual_completed_count = len(actual_completed)
        actual_completed_amount = sum(o.get('amount', 0) for o in actual_completed)
        actual_breach_end_count = len(actual_breach_end)
        actual_breach_end_amount = sum(o.get('amount', 0) for o in actual_breach_end)
        
        # 比较统计数据
        errors = []
        
        if financial_data.get('valid_orders') != actual_valid_count:
            errors.append(f"有效订单数不匹配: 统计={financial_data.get('valid_orders')}, 实际={actual_valid_count}")
        
        if abs(financial_data.get('valid_amount', 0) - actual_valid_amount) > 0.01:
            errors.append(f"有效订单金额不匹配: 统计={financial_data.get('valid_amount', 0):.2f}, 实际={actual_valid_amount:.2f}")
        
        if financial_data.get('breach_orders') != actual_breach_count:
            errors.append(f"违约订单数不匹配: 统计={financial_data.get('breach_orders')}, 实际={actual_breach_count}")
        
        if abs(financial_data.get('breach_amount', 0) - actual_breach_amount) > 0.01:
            errors.append(f"违约订单金额不匹配: 统计={financial_data.get('breach_amount', 0):.2f}, 实际={actual_breach_amount:.2f}")
        
        if financial_data.get('completed_orders') != actual_completed_count:
            errors.append(f"完成订单数不匹配: 统计={financial_data.get('completed_orders')}, 实际={actual_completed_count}")
        
        if abs(financial_data.get('completed_amount', 0) - actual_completed_amount) > 0.01:
            errors.append(f"完成订单金额不匹配: 统计={financial_data.get('completed_amount', 0):.2f}, 实际={actual_completed_amount:.2f}")
        
        if errors:
            for error in errors:
                result.add_warning("订单统计正确性", error)
        else:
            result.add_pass("订单统计正确性检查")
    except Exception as e:
        result.add_fail("订单统计正确性检查", str(e))
    
    # 2. 验证收入记录金额正确性
    print("\n[2] 验证收入记录金额正确性...")
    try:
        today = get_daily_period_date()
        income_records = await db_operations.get_income_records(
            start_date=today,
            end_date=today
        )
        
        # 验证金额都是正数
        negative_amounts = [r for r in income_records if r.get('amount', 0) <= 0]
        if negative_amounts:
            result.add_fail("收入记录金额正确性", f"发现 {len(negative_amounts)} 条金额非正数的记录")
        else:
            result.add_pass("收入记录金额正确性检查")
    except Exception as e:
        result.add_fail("收入记录金额正确性检查", str(e))


async def test_database_connection(result: TestResult):
    """测试数据库连接"""
    print("\n" + "=" * 80)
    print("数据库连接测试")
    print("=" * 80)
    
    try:
        # 显示数据库路径
        data_dir = os.getenv('DATA_DIR', os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(data_dir, 'loan_bot.db')
        print(f"\n数据库路径: {db_path}")
        print(f"数据库文件存在: {os.path.exists(db_path)}")
        
        # 测试获取财务数据
        financial_data = await db_operations.get_financial_data()
        if financial_data:
            result.add_pass("数据库连接测试")
            print(f"\n当前流动资金: {financial_data.get('liquid_funds', 0):,.2f} 元")
        else:
            result.add_fail("数据库连接测试", "无法获取财务数据")
    except Exception as e:
        result.add_fail("数据库连接测试", str(e))


async def check_database_info(result: TestResult):
    """检查数据库信息（只读）"""
    print("\n" + "=" * 80)
    print("数据库信息检查")
    print("=" * 80)
    
    try:
        # 获取所有订单
        all_orders = await db_operations.search_orders_all()
        print(f"\n总订单数: {len(all_orders)}")
        
        # 按状态统计
        by_state = {}
        for order in all_orders:
            state = order.get('state', 'unknown')
            by_state[state] = by_state.get(state, 0) + 1
        
        print("\n订单状态分布:")
        for state, count in sorted(by_state.items()):
            print(f"  {state}: {count} 个")
        
        # 获取财务数据
        financial_data = await db_operations.get_financial_data()
        print(f"\n财务数据概览:")
        print(f"  有效订单: {financial_data.get('valid_orders', 0)} 个")
        print(f"  有效金额: {financial_data.get('valid_amount', 0):,.2f} 元")
        print(f"  流动资金: {financial_data.get('liquid_funds', 0):,.2f} 元")
        print(f"  利息收入: {financial_data.get('interest', 0):,.2f} 元")
        
        # 获取今日收入
        today = get_daily_period_date()
        today_income = await db_operations.get_income_records(
            start_date=today,
            end_date=today
        )
        print(f"\n今日收入记录: {len(today_income)} 条")
        
        result.add_pass("数据库信息检查")
    except Exception as e:
        result.add_fail("数据库信息检查", str(e))


async def run_production_tests():
    """运行生产环境测试（只读模式）"""
    print("=" * 80)
    print("生产环境安全测试脚本（只读模式）")
    print("=" * 80)
    print()
    print("⚠️  警告: 此脚本运行在生产环境")
    print("✅ 安全: 只读模式，不会修改任何数据")
    print()
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试日期: {get_daily_period_date()}")
    
    # 确认环境
    data_dir = os.getenv('DATA_DIR', os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(data_dir, 'loan_bot.db')
    
    print(f"\n数据库路径: {db_path}")
    
    # 检查数据库文件
    if not os.path.exists(db_path):
        print(f"\n[FAIL] 数据库文件不存在: {db_path}")
        return False
    
    print(f"数据库文件大小: {os.path.getsize(db_path) / 1024 / 1024:.2f} MB")
    
    result = TestResult()
    
    # 运行所有测试（只读）
    await test_database_connection(result)
    await check_database_info(result)
    await verify_data_consistency_readonly(result)
    await verify_data_correctness_readonly(result)
    
    # 输出总结
    success = result.summary()
    
    print("\n" + "=" * 80)
    print("测试完成 - 生产环境只读模式")
    print("=" * 80)
    print("✅ 所有测试均为只读操作，未修改任何数据")
    print("=" * 80)
    
    return success


if __name__ == "__main__":
    try:
        # 显示警告
        print()
        print("=" * 80)
        print("⚠️  生产环境测试脚本")
        print("=" * 80)
        print("此脚本将连接到生产数据库进行只读测试")
        print("不会修改任何数据，但请确保：")
        print("  1. 数据库路径正确")
        print("  2. 有数据库访问权限")
        print("  3. 了解测试内容")
        print()
        
        # 可以添加确认提示（在生产环境可以取消）
        # response = input("是否继续？(yes/no): ")
        # if response.lower() != 'yes':
        #     print("测试已取消")
        #     sys.exit(0)
        
        success = asyncio.run(run_production_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n测试执行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

