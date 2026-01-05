"""订单选择 - 分组模块

包含按金额分组订单的逻辑。
"""

from typing import Any, Dict, List


def _calculate_amount_ranges(min_amount: float, max_amount: float) -> List[tuple]:
    """计算金额范围

    Args:
        min_amount: 最小金额
        max_amount: 最大金额

    Returns:
        金额范围列表
    """
    return [
        (min_amount, min_amount + (max_amount - min_amount) * 0.25),  # 0-25%
        (
            min_amount + (max_amount - min_amount) * 0.25,
            min_amount + (max_amount - min_amount) * 0.5,
        ),  # 25-50%
        (
            min_amount + (max_amount - min_amount) * 0.5,
            min_amount + (max_amount - min_amount) * 0.75,
        ),  # 50-75%
        (min_amount + (max_amount - min_amount) * 0.75, max_amount + 1),  # 75-100%
    ]


def _distribute_orders_to_ranges(
    valid_orders: List[Dict], amount_ranges: List[tuple]
) -> list[list[dict[str, Any]]]:
    """将订单分配到金额范围

    Args:
        valid_orders: 有效订单列表
        amount_ranges: 金额范围列表

    Returns:
        分组后的订单列表
    """
    range_orders: list[list[dict[str, Any]]] = [[] for _ in range(4)]
    for order in valid_orders:
        amount = order.get("amount", 0)
        for i, (low, high) in enumerate(amount_ranges):
            if low <= amount < high:
                range_orders[i].append(order)
                break
    return range_orders


def _calculate_range_targets(
    range_orders: list[list[dict[str, Any]]], total_orders: int
) -> List[float]:
    """计算每个区间的目标金额

    Args:
        range_orders: 分组后的订单列表
        total_orders: 总订单数

    Returns:
        目标金额列表
    """
    range_targets = []
    for range_order_list in range_orders:
        if total_orders > 0 and range_order_list:
            range_targets.append(0)  # 将在调用处计算
        else:
            range_targets.append(0)
    return range_targets


def group_orders_by_amount_range(
    valid_orders: List[Dict],
) -> tuple[list[list[dict[str, Any]]], List[float]]:
    """按金额范围分组订单

    Args:
        valid_orders: 有效订单列表

    Returns:
        Tuple: (分组后的订单列表, 金额范围列表)
    """
    amounts = [o.get("amount", 0) for o in valid_orders]
    min_amount = min(amounts) if amounts else 0
    max_amount = max(amounts) if amounts else 0

    amount_ranges = _calculate_amount_ranges(min_amount, max_amount)
    range_orders = _distribute_orders_to_ranges(valid_orders, amount_ranges)
    range_targets = _calculate_range_targets(range_orders, len(valid_orders))

    return range_orders, range_targets
