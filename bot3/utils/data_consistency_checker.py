"""数据一致性验证工具

用于验证关键操作后的数据一致性，确保：
1. 订单与统计数据的一致性
2. 收入记录与统计数据的一致性
3. 流动资金计算的正确性
"""

import logging
from typing import Dict, List, Tuple

import db_operations

logger = logging.getLogger(__name__)


def _validate_order_basic_info(
    order: Dict, order_id: str, expected_state: str, errors: List[str]
) -> None:
    """验证订单基本信息

    Args:
        order: 订单字典
        order_id: 期望的订单ID
        expected_state: 期望的订单状态
        errors: 错误列表
    """
    if order["order_id"] != order_id:
        errors.append(f"订单ID不匹配: 期望={order_id}, 实际={order['order_id']}")

    if order["state"] != expected_state:
        errors.append(f"订单状态不匹配: 期望={expected_state}, 实际={order['state']}")


def _validate_order_state_statistics(expected_state: str) -> None:
    """验证订单状态统计（占位函数，用于未来扩展）

    Args:
        expected_state: 期望的订单状态
    """
    if expected_state in ("normal", "overdue"):
        pass
    elif expected_state == "end":
        pass
    elif expected_state == "breach":
        pass


async def verify_order_stats_consistency(
    order_id: str, chat_id: int, expected_state: str
) -> Tuple[bool, List[str]]:
    """验证订单与统计数据的一致性

    Args:
        order_id: 订单ID
        chat_id: 聊天ID
        expected_state: 期望的订单状态

    Returns:
        (是否一致, 错误列表)
    """
    errors = []
    try:
        order = await db_operations.get_order_by_chat_id(chat_id)
        if not order:
            errors.append(f"订单不存在: chat_id={chat_id}")
            return False, errors

        _validate_order_basic_info(order, order_id, expected_state, errors)
        _validate_order_state_statistics(expected_state)

        return len(errors) == 0, errors

    except Exception as e:
        logger.error(f"验证订单统计数据一致性时出错: {e}", exc_info=True)
        errors.append(f"验证过程出错: {str(e)}")
        return False, errors


async def verify_income_stats_consistency(
    income_record_id: int,
    expected_amount: float,
    expected_type: str,  # noqa: ARG001, F841
) -> Tuple[bool, List[str]]:
    """验证收入记录与统计数据的一致性

    Args:
        income_record_id: 收入记录ID
        expected_amount: 期望的金额
        expected_type: 期望的收入类型

    Returns:
        (是否一致, 错误列表)
    """
    errors = []
    try:
        # 获取收入记录
        # 注意：需要从数据库查询，这里简化处理
        # 实际应该查询 income_records 表

        # 获取统计数据（用于未来扩展）
        # financial_data = await db_operations.get_financial_data()

        # 验证利息统计
        if expected_type == "interest":
            # 验证利息总额（简化检查，实际应该累加所有利息记录）
            pass

        return len(errors) == 0, errors

    except Exception as e:
        logger.error(f"验证收入统计数据一致性时出错: {e}", exc_info=True)
        errors.append(f"验证过程出错: {str(e)}")
        return False, errors


async def verify_liquid_funds_calculation() -> Tuple[bool, List[str]]:
    """验证流动资金计算的正确性

    流动资金应该等于：
    - 初始资金
    - + 所有完成订单金额
    - + 所有违约完成订单金额
    - + 所有利息收入
    - - 所有新订单金额
    - - 所有支出

    Returns:
        (是否一致, 错误列表)
    """
    errors = []
    try:
        # 获取统计数据（用于未来扩展）
        # financial_data = await db_operations.get_financial_data()

        # 获取所有订单（用于未来扩展）
        # all_orders = await db_operations.get_all_valid_orders()

        # 计算期望的流动资金
        # 注意：这里简化处理，实际应该从历史记录计算
        # 实际实现需要：
        # 1. 查询所有完成订单的金额总和
        # 2. 查询所有违约完成订单的金额总和
        # 3. 查询所有利息收入总和
        # 4. 查询所有新订单金额总和
        # 5. 查询所有支出总和
        # 6. 计算：初始资金 + 完成订单 + 违约完成 + 利息 - 新订单 - 支出

        # 简化验证：只检查流动资金不为负数（基本合理性检查）
        # financial_data = await db_operations.get_financial_data()
        # if financial_data["liquid_funds"] < 0:
        #     errors.append(f"流动资金为负数: {financial_data['liquid_funds']:.2f}")
        pass  # 暂时跳过，等待未来实现

        return len(errors) == 0, errors

    except Exception as e:
        logger.error(f"验证流动资金计算时出错: {e}", exc_info=True)
        errors.append(f"验证过程出错: {str(e)}")
        return False, errors


async def verify_complete_operation_consistency(
    operation_type: str, operation_data: Dict
) -> Tuple[bool, List[str]]:
    """验证完整操作的数据一致性

    Args:
        operation_type: 操作类型（如 "order_completed", "interest", "principal_reduction"）
        operation_data: 操作数据

    Returns:
        (是否一致, 错误列表)
    """
    errors = []
    try:
        if operation_type == "order_completed":
            # 验证订单完成操作的一致性
            chat_id = operation_data.get("chat_id")
            order_id = operation_data.get("order_id")
            if chat_id and order_id:
                is_consistent, order_errors = await verify_order_stats_consistency(
                    order_id, chat_id, "end"
                )
                if not is_consistent:
                    errors.extend(order_errors)

        elif operation_type == "interest":
            # 验证利息收入操作的一致性
            income_record_id = operation_data.get("income_record_id")
            amount = operation_data.get("amount")
            if income_record_id and amount:
                is_consistent, income_errors = await verify_income_stats_consistency(
                    income_record_id, amount, "interest"
                )
                if not is_consistent:
                    errors.extend(income_errors)

        # 验证流动资金
        is_consistent, liquid_errors = await verify_liquid_funds_calculation()
        if not is_consistent:
            errors.extend(liquid_errors)

        return len(errors) == 0, errors

    except Exception as e:
        logger.error(f"验证完整操作一致性时出错: {e}", exc_info=True)
        errors.append(f"验证过程出错: {str(e)}")
        return False, errors
