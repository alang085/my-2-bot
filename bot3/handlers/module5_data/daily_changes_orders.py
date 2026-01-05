"""每日变更 - 订单模块

包含获取订单相关变更的逻辑。
"""

from typing import Any, Dict, List

import db_operations


def _calculate_new_orders_statistics(new_orders: List[Dict]) -> Dict[str, Any]:
    """计算新增订单统计信息

    Args:
        new_orders: 新增订单列表

    Returns:
        统计信息字典
    """
    new_clients_count = 0
    new_clients_amount = 0.0
    old_clients_count = 0
    old_clients_amount = 0.0

    for order in new_orders:
        customer = order.get("customer", "")
        amount = float(order.get("amount", 0) or 0)
        if customer == "A":
            new_clients_count += 1
            new_clients_amount += amount
        elif customer == "B":
            old_clients_count += 1
            old_clients_amount += amount

    return {
        "new_clients_count": new_clients_count,
        "new_clients_amount": new_clients_amount,
        "old_clients_count": old_clients_count,
        "old_clients_amount": old_clients_amount,
    }


def _calculate_orders_summary(orders: List[Dict]) -> Dict[str, Any]:
    """计算订单汇总信息

    Args:
        orders: 订单列表

    Returns:
        汇总信息字典
    """
    count = len(orders)
    amount = sum(float(order.get("amount", 0) or 0) for order in orders)
    return {"count": count, "amount": amount}


async def get_order_changes(date: str) -> dict:
    """获取订单相关变更

    Args:
        date: 日期字符串

    Returns:
        dict: 订单变更数据
    """
    new_orders = await db_operations.get_new_orders_by_date(date)
    new_stats = _calculate_new_orders_statistics(new_orders)

    completed_orders = await db_operations.get_completed_orders_by_date(date)
    completed_summary = _calculate_orders_summary(completed_orders)

    breach_orders = await db_operations.get_breach_orders_by_date(date)
    breach_summary = _calculate_orders_summary(breach_orders)

    breach_end_orders = await db_operations.get_breach_end_orders_by_date(date)
    breach_end_summary = _calculate_orders_summary(breach_end_orders)

    return {
        "new_orders": new_orders,
        "new_clients_count": new_stats["new_clients_count"],
        "new_clients_amount": new_stats["new_clients_amount"],
        "old_clients_count": new_stats["old_clients_count"],
        "old_clients_amount": new_stats["old_clients_amount"],
        "completed_orders": completed_orders,
        "completed_orders_count": completed_summary["count"],
        "completed_orders_amount": completed_summary["amount"],
        "breach_orders": breach_orders,
        "breach_orders_count": breach_summary["count"],
        "breach_orders_amount": breach_summary["amount"],
        "breach_end_orders": breach_end_orders,
        "breach_end_orders_count": breach_end_summary["count"],
        "breach_end_orders_amount": breach_end_summary["amount"],
    }
