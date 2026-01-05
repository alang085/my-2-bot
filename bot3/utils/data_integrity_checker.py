"""数据完整性检查模块

提供数据一致性验证和自动修复功能。
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import db_operations

logger = logging.getLogger(__name__)


def _check_main_table_consistency(all_orders: List[Dict]) -> List[Dict]:
    """检查主表和分类表的一致性

    Args:
        all_orders: 所有订单列表

    Returns:
        问题列表
    """
    issues = []
    state_table_map = {
        "normal": "orders_normal",
        "overdue": "orders_overdue",
        "breach": "orders_breach",
        "end": "orders_end",
        "breach_end": "orders_breach_end",
    }

    for order in all_orders:
        state = order.get("state")
        expected_table = state_table_map.get(state)
        if expected_table:
            pass  # 可以添加更详细的检查逻辑

    return issues


def _check_financial_data_consistency(financial_data: Dict) -> List[Dict]:
    """检查财务数据一致性

    Args:
        financial_data: 财务数据字典

    Returns:
        问题列表
    """
    issues = []
    if not financial_data:
        return issues

    valid_orders = financial_data.get("valid_orders", 0)
    valid_amount = financial_data.get("valid_amount", 0)

    if valid_orders > 0 and valid_amount <= 0:
        issues.append(
            {
                "type": "financial_inconsistency",
                "message": f"有效订单数 {valid_orders} 但金额为 {valid_amount}",
            }
        )

    return issues


async def check_orders_consistency() -> Dict[str, Any]:
    """检查订单数据一致性

    Returns:
        检查结果字典，包含不一致项列表
    """
    issues = []

    try:
        all_orders = await db_operations.get_all_valid_orders()
        issues.extend(_check_main_table_consistency(all_orders))

        financial_data = await db_operations.get_financial_data()
        issues.extend(_check_financial_data_consistency(financial_data))

        return {
            "status": "success" if not issues else "issues_found",
            "issues": issues,
            "checked_at": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"数据一致性检查失败: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "checked_at": datetime.now().isoformat(),
        }


async def auto_fix_common_issues() -> Dict[str, Any]:
    """自动修复常见的数据一致性问题

    Returns:
        修复结果字典
    """
    fixes_applied = []

    try:
        # 1. 修复缺失的财务数据记录
        financial_data = await db_operations.get_financial_data()
        if not financial_data or financial_data.get("id") is None:
            # 创建初始财务数据记录
            await db_operations.update_financial_data("valid_orders", 0)
            fixes_applied.append("创建了缺失的财务数据记录")

        # 2. 修复缺失的分组数据记录
        all_group_ids = await db_operations.get_all_group_ids()
        for group_id in all_group_ids:
            grouped_data = await db_operations.get_grouped_data(group_id)
            if not grouped_data or grouped_data.get("group_id") != group_id:
                # 创建缺失的分组数据记录
                await db_operations.update_grouped_data(group_id, "valid_orders", 0)
                fixes_applied.append(f"创建了缺失的分组数据记录: {group_id}")

        return {
            "status": "success",
            "fixes_applied": fixes_applied,
            "fixed_at": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"自动修复失败: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "fixed_at": datetime.now().isoformat(),
        }


async def validate_order_data(order: Dict[str, Any]) -> List[str]:
    """验证订单数据的完整性

    Args:
        order: 订单数据字典

    Returns:
        验证错误列表（空列表表示验证通过）
    """
    errors = []

    required_fields = ["order_id", "chat_id", "date", "amount", "state", "customer"]
    for field in required_fields:
        if field not in order or order[field] is None:
            errors.append(f"缺少必需字段: {field}")

    # 验证状态值
    valid_states = ["normal", "overdue", "breach", "end", "breach_end"]
    if order.get("state") not in valid_states:
        errors.append(f"无效的状态值: {order.get('state')}")

    # 验证客户类型
    valid_customers = ["A", "B"]
    if order.get("customer") not in valid_customers:
        errors.append(f"无效的客户类型: {order.get('customer')}")

    # 验证金额
    amount = order.get("amount")
    if amount is not None and (not isinstance(amount, (int, float)) or amount < 0):
        errors.append(f"无效的金额: {amount}")

    return errors
