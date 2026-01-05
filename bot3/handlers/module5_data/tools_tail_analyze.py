"""查找尾数订单 - 分析模块

包含分析订单尾数的逻辑。
"""

from typing import Any, Dict, List, Tuple


def analyze_order_tails(
    all_valid_orders: List[Dict[str, Any]],
) -> Tuple[
    List[Tuple[Dict[str, Any], int]],
    List[Dict[str, Any]],
    Dict[int, List[Dict[str, Any]]],
]:
    """分析订单尾数

    Args:
        all_valid_orders: 所有有效订单列表

    Returns:
        Tuple: (非整千数订单列表, 尾数为6的订单列表, 尾数分布字典)
    """
    non_thousand_orders = []
    tail_6_orders = []
    tail_distribution = {}  # 尾数分布统计

    for order in all_valid_orders:
        amount = order.get("amount", 0)
        if amount % 1000 != 0:
            tail = int(amount % 1000)
            non_thousand_orders.append((order, tail))
            if tail not in tail_distribution:
                tail_distribution[tail] = []
            tail_distribution[tail].append(order)
            if tail == 6:
                tail_6_orders.append(order)

    return non_thousand_orders, tail_6_orders, tail_distribution
