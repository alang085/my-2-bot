"""完整的本地测试脚本 - 确保数据一致性和正确性"""
import asyncio
import sys
import os
from pathlib import Path

# 确保项目根目录在 Python 路径中
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import db_operations
from utils.date_helpers import get_daily_period_date
from utils.stats_helpers import update_all_stats, update_liquid_capital
import json
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 测试数据
TEST_USER_ID = 123456789
TEST_CHAT_ID_GROUP = -1001234567890
TEST_CHAT_ID_PRIVATE = 123456789
TEST_GROUP_ID = "S01"
TEST_DATE = get_daily_period_date()


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
            for warning in self.warnings:
                print(f"  - {warning}")
        
        print("=" * 80)
        return self.failed == 0


async def verify_data_consistency(result: TestResult):
    """验证数据一致性"""
    print("\n" + "=" * 80)
    print("数据一致性验证")
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
        today_income = await db_operations.get_income_records(
            start_date=TEST_DATE,
            end_date=TEST_DATE
        )
        
        # 验证每条记录都有必需的字段
        invalid_records = []
        for record in today_income:
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
    
    # 4. 验证操作历史一致性
    print("\n[4] 验证操作历史一致性...")
    try:
        # 获取最近的100条操作记录（如果用户ID存在）
        try:
            recent_operations = await db_operations.get_recent_operations(TEST_USER_ID, 100)
        except:
            # 如果没有该用户的操作，跳过
            recent_operations = []
        
        undone_operations = [op for op in recent_operations if op.get('is_undone') == 0]
        
        # 验证操作数据格式
        invalid_ops = []
        for op in undone_operations:
            try:
                op_data = op.get('operation_data', {})
                if isinstance(op_data, str):
                    op_data = json.loads(op_data)
                if not isinstance(op_data, dict):
                    invalid_ops.append(op.get('id'))
            except:
                invalid_ops.append(op.get('id'))
        
        if invalid_ops:
            result.add_fail("操作历史一致性", f"发现 {len(invalid_ops)} 条格式错误的操作记录")
        else:
            if recent_operations:
                result.add_pass(f"操作历史一致性检查 (检查了 {len(undone_operations)} 条未撤销操作)")
            else:
                result.add_warning("操作历史一致性", "没有找到操作记录进行验证")
    except Exception as e:
        result.add_fail("操作历史一致性检查", str(e))


async def verify_data_correctness(result: TestResult):
    """验证数据正确性"""
    print("\n" + "=" * 80)
    print("数据正确性验证")
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
        today_income = await db_operations.get_income_records(
            start_date=TEST_DATE,
            end_date=TEST_DATE
        )
        
        # 验证金额都是正数
        negative_amounts = [r for r in today_income if r.get('amount', 0) <= 0]
        if negative_amounts:
            result.add_fail("收入记录金额正确性", f"发现 {len(negative_amounts)} 条金额非正数的记录")
        else:
            result.add_pass("收入记录金额正确性检查")
    except Exception as e:
        result.add_fail("收入记录金额正确性检查", str(e))
    
    # 3. 验证操作历史完整性
    print("\n[3] 验证操作历史完整性...")
    try:
        # 只检查最近的操作，避免性能问题
        recent_operations = await db_operations.get_recent_operations(TEST_USER_ID, 50)
        
        # 检查是否有孤立操作（操作数据中引用的订单或记录不存在）
        invalid_ops = []
        for op in recent_operations:
            try:
                op_data = op.get('operation_data', {})
                if isinstance(op_data, str):
                    op_data = json.loads(op_data)
                op_type = op.get('operation_type')
                
                # 检查订单相关操作（只检查未撤销的操作）
                if op.get('is_undone') == 0 and op_type in ['order_created', 'order_completed', 'order_breach_end', 'order_state_change']:
                    order_id = op_data.get('order_id')
                    if order_id:
                        order = await db_operations.get_order_by_order_id(order_id)
                        if not order and op_type != 'order_created':  # order_created 本身可能已经撤销删除
                            invalid_ops.append(f"操作 {op.get('id')}: 订单 {order_id} 不存在")
            except Exception as e:
                invalid_ops.append(f"操作 {op.get('id')}: 解析失败 - {str(e)}")
        
        if invalid_ops:
            for error in invalid_ops[:5]:  # 只显示前5个
                result.add_warning("操作历史完整性", error)
        else:
            result.add_pass("操作历史完整性检查")
    except Exception as e:
        result.add_fail("操作历史完整性检查", str(e))


async def test_database_connection(result: TestResult):
    """测试数据库连接"""
    print("\n" + "=" * 80)
    print("数据库连接测试")
    print("=" * 80)
    
    try:
        # 测试获取财务数据
        financial_data = await db_operations.get_financial_data()
        if financial_data:
            result.add_pass("数据库连接测试")
        else:
            result.add_fail("数据库连接测试", "无法获取财务数据")
    except Exception as e:
        result.add_fail("数据库连接测试", str(e))


async def test_undo_isolation(result: TestResult):
    """测试撤销功能按聊天环境隔离"""
    print("\n" + "=" * 80)
    print("撤销功能隔离测试")
    print("=" * 80)
    
    # 1. 测试在不同聊天环境记录操作
    print("\n[1] 测试操作记录隔离...")
    try:
        # 在私聊中记录操作
        op1_id = await db_operations.record_operation(
            user_id=TEST_USER_ID,
            operation_type='expense',
            operation_data={'amount': 100, 'type': 'company'},
            chat_id=TEST_CHAT_ID_PRIVATE
        )
        
        # 在群聊中记录操作
        op2_id = await db_operations.record_operation(
            user_id=TEST_USER_ID,
            operation_type='interest',
            operation_data={'amount': 200},
            chat_id=TEST_CHAT_ID_GROUP
        )
        
        # 验证隔离
        private_op = await db_operations.get_last_operation(TEST_USER_ID, TEST_CHAT_ID_PRIVATE)
        group_op = await db_operations.get_last_operation(TEST_USER_ID, TEST_CHAT_ID_GROUP)
        
        if private_op and private_op['operation_type'] == 'expense':
            result.add_pass("私聊操作隔离")
        else:
            result.add_fail("私聊操作隔离", "无法获取私聊操作")
        
        if group_op and group_op['operation_type'] == 'interest':
            result.add_pass("群聊操作隔离")
        else:
            result.add_fail("群聊操作隔离", "无法获取群聊操作")
        
        # 验证不会跨环境获取
        if private_op and private_op['operation_type'] != 'interest':
            result.add_pass("操作环境隔离验证")
        else:
            result.add_fail("操作环境隔离验证", "私聊获取到了群聊操作")
            
    except Exception as e:
        result.add_fail("撤销功能隔离测试", str(e))


async def test_statistics_update(result: TestResult):
    """测试统计更新功能"""
    print("\n" + "=" * 80)
    print("统计更新功能测试")
    print("=" * 80)
    
    # 1. 测试更新利息统计
    print("\n[1] 测试更新利息统计...")
    try:
        # 获取更新前的数据
        before_data = await db_operations.get_financial_data()
        before_interest = before_data.get('interest', 0)
        
        # 更新利息
        test_amount = 100.0
        await update_all_stats('interest', test_amount, 0, None)
        
        # 获取更新后的数据
        after_data = await db_operations.get_financial_data()
        after_interest = after_data.get('interest', 0)
        
        # 验证更新
        expected_interest = before_interest + test_amount
        if abs(after_interest - expected_interest) < 0.01:
            result.add_pass("更新利息统计")
            
            # 恢复数据
            await update_all_stats('interest', -test_amount, 0, None)
        else:
            result.add_fail("更新利息统计", f"期望 {expected_interest:.2f}, 实际 {after_interest:.2f}")
    except Exception as e:
        result.add_fail("更新利息统计", str(e))
    
    # 2. 测试更新流动资金
    print("\n[2] 测试更新流动资金...")
    try:
        before_data = await db_operations.get_financial_data()
        before_liquid = before_data.get('liquid_funds', 0)
        
        test_amount = 50.0
        await update_liquid_capital(test_amount)
        
        after_data = await db_operations.get_financial_data()
        after_liquid = after_data.get('liquid_funds', 0)
        
        expected_liquid = before_liquid + test_amount
        if abs(after_liquid - expected_liquid) < 0.01:
            result.add_pass("更新流动资金")
            
            # 恢复数据
            await update_liquid_capital(-test_amount)
        else:
            result.add_fail("更新流动资金", f"期望 {expected_liquid:.2f}, 实际 {after_liquid:.2f}")
    except Exception as e:
        result.add_fail("更新流动资金", str(e))


async def test_income_records(result: TestResult):
    """测试收入记录功能"""
    print("\n" + "=" * 80)
    print("收入记录功能测试")
    print("=" * 80)
    
    # 1. 测试创建收入记录
    print("\n[1] 测试创建收入记录...")
    try:
        income_id = await db_operations.record_income(
            date=TEST_DATE,
            type='interest',
            amount=300.0,
            group_id=TEST_GROUP_ID,
            order_id=None,
            order_date=None,
            customer=None,
            weekday_group=None,
            note="测试利息收入",
            created_by=TEST_USER_ID
        )
        
        if income_id:
            result.add_pass("创建收入记录")
            
            # 验证记录存在
            records = await db_operations.get_income_records(
                start_date=TEST_DATE,
                end_date=TEST_DATE,
                type='interest'
            )
            
            found = False
            for record in records:
                if record.get('id') == income_id:
                    found = True
                    # 验证数据正确性
                    if abs(record.get('amount', 0) - 300.0) < 0.01:
                        result.add_pass("收入记录数据正确性")
                    else:
                        result.add_fail("收入记录数据正确性", f"金额不匹配: {record.get('amount')}")
                    break
            
            if not found:
                result.add_fail("创建收入记录", "记录创建后无法查询到")
        else:
            result.add_fail("创建收入记录", "返回的ID为空")
    except Exception as e:
        result.add_fail("创建收入记录", str(e))


async def run_all_tests():
    """运行所有测试"""
    print("=" * 80)
    print("完整本地测试脚本")
    print("=" * 80)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试日期: {TEST_DATE}")
    
    result = TestResult()
    
    # 运行所有测试
    await test_database_connection(result)
    await verify_data_consistency(result)
    await verify_data_correctness(result)
    await test_undo_isolation(result)
    await test_statistics_update(result)
    await test_income_records(result)
    
    # 输出总结
    success = result.summary()
    
    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n测试执行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

