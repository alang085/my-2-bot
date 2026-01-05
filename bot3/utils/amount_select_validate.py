"""订单选择 - 验证模块

包含验证订单和金额的逻辑。
"""

from typing import Dict, List


def validate_orders_and_amount(
    orders: List[Dict], target_amount: float
) -> tuple[bool, List[Dict]]:
    """验证订单列表和目标金额

    Args:
        orders: 订单列表
        target_amount: 目标金额

    Returns:
        Tuple: (是否有效, 有效订单列表)
    """
    if not orders or target_amount <= 0:
        return False, []

    # 过滤掉金额为0或负数的订单
    valid_orders = [o for o in orders if o.get("amount", 0) > 0]
    if not valid_orders:
        return False, []

    return True, valid_orders
