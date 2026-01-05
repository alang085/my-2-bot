"""金额助手 - 星期分组模块

包含按星期分组订单的逻辑。
"""

from typing import Any, Dict, List


def group_orders_by_weekday(
    orders: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """按星期分组订单

    Args:
        orders: 订单列表

    Returns:
        Dict: 按星期分组的订单字典
    """
    from constants import WEEKDAY_GROUP

    weekday_orders: dict[str, list[dict[str, Any]]] = {}
    for weekday_name in WEEKDAY_GROUP.values():
        weekday_orders[weekday_name] = []

    for order in orders:
        weekday_group = order.get("weekday_group")
        if weekday_group in weekday_orders:
            weekday_orders[weekday_group].append(order)

    return weekday_orders
