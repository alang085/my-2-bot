"""订单选择 - 选择模块

包含从分组中选择订单的逻辑。
"""

from typing import Any, Dict, List, Tuple

from utils.amount_helpers import _greedy_select


def _round_robin_select_from_ranges(
    sorted_range_orders: List[List[Dict]], target_amount: float
) -> Tuple[List[Dict], float, List[int]]:
    """使用轮询方式从各个区间选择订单

    Args:
        sorted_range_orders: 按金额排序后的分组订单列表
        target_amount: 目标金额

    Returns:
        (选中的订单列表, 当前总金额, 区间索引列表)
    """
    selected = []
    current_total = 0.0
    max_iterations = 1000
    iteration = 0
    range_indices = [0] * 4

    while current_total < target_amount and iteration < max_iterations:
        iteration += 1
        added_any = False

        for i in range(4):
            if range_indices[i] >= len(sorted_range_orders[i]):
                continue

            order = sorted_range_orders[i][range_indices[i]]
            order_amount = order.get("amount", 0)

            if current_total + order_amount <= target_amount:
                selected.append(order)
                current_total += order_amount
                range_indices[i] += 1
                added_any = True
            elif current_total < target_amount:
                if current_total + order_amount - target_amount < target_amount * 0.1:
                    selected.append(order)
                    current_total += order_amount
                    range_indices[i] += 1
                    return selected, current_total, range_indices
                else:
                    range_indices[i] += 1

        if not added_any:
            break

    return selected, current_total, range_indices


def _greedy_fill_remaining(
    sorted_range_orders: List[List[Dict]],
    range_indices: List[int],
    selected: List[Dict],
    current_total: float,
    target_amount: float,
) -> Tuple[List[Dict], float]:
    """使用贪心算法补充剩余订单

    Args:
        sorted_range_orders: 按金额排序后的分组订单列表
        range_indices: 区间索引列表
        selected: 已选中的订单列表
        current_total: 当前总金额
        target_amount: 目标金额

    Returns:
        (更新后的订单列表, 更新后的总金额)
    """
    if current_total >= target_amount * 0.9:
        return selected, current_total

    remaining_orders = []
    for i, range_order_list in enumerate(sorted_range_orders):
        remaining_orders.extend(range_order_list[range_indices[i] :])

    remaining_selected = _greedy_select(remaining_orders, target_amount - current_total)
    selected.extend(remaining_selected)
    current_total += sum(o.get("amount", 0) for o in remaining_selected)

    return selected, current_total


def select_orders_from_ranges(
    sorted_range_orders: List[List[Dict]], target_amount: float
) -> tuple[List[Dict], float]:
    """从分组中选择订单

    Args:
        sorted_range_orders: 按金额排序后的分组订单列表
        target_amount: 目标金额

    Returns:
        Tuple: (选中的订单列表, 当前总金额)
    """
    selected, current_total, range_indices = _round_robin_select_from_ranges(
        sorted_range_orders, target_amount
    )
    return _greedy_fill_remaining(
        sorted_range_orders, range_indices, selected, current_total, target_amount
    )
