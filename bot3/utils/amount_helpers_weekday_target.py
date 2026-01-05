"""金额助手 - 星期目标计算模块

包含计算每天目标金额的逻辑。
"""

from typing import Dict


def _calculate_proportional_targets(
    weekday_available_amounts: Dict[str, float],
    target_total_amount: float,
    total_available: float,
) -> Dict[str, float]:
    """按比例分配目标金额（当总可用金额不足时）

    Args:
        weekday_available_amounts: 每天可用的订单总金额
        target_total_amount: 总目标金额
        total_available: 总可用金额

    Returns:
        每天的目标金额字典
    """
    daily_targets = {}
    for weekday_name in ["一", "二", "三", "四", "五", "六", "日"]:
        if total_available > 0:
            daily_targets[weekday_name] = (
                weekday_available_amounts[weekday_name] / total_available
            ) * target_total_amount
        else:
            daily_targets[weekday_name] = 0
    return daily_targets


def _allocate_balanced_targets_first_round(
    weekday_available_amounts: Dict[str, float],
    daily_target: float,
    target_total_amount: float,
) -> Tuple[Dict[str, float], float, List[str]]:
    """均衡分配目标金额的第一轮（基础分配）

    Args:
        weekday_available_amounts: 每天可用的订单总金额
        daily_target: 每天的基础目标金额
        target_total_amount: 总目标金额

    Returns:
        (每天的目标金额字典, 剩余目标金额, 不足天数列表)
    """
    daily_targets = {}
    remaining_target = target_total_amount
    remaining_days = []

    for weekday_name in ["一", "二", "三", "四", "五", "六", "日"]:
        available = weekday_available_amounts[weekday_name]
        if available >= daily_target:
            daily_targets[weekday_name] = daily_target
            remaining_target -= daily_target
        else:
            daily_targets[weekday_name] = available
            remaining_target -= available
            remaining_days.append(weekday_name)

    return daily_targets, remaining_target, remaining_days


def _allocate_remaining_targets(
    daily_targets: Dict[str, float],
    weekday_available_amounts: Dict[str, float],
    remaining_target: float,
    remaining_days: List[str],
) -> Dict[str, float]:
    """分配剩余的目标金额（第二轮）

    Args:
        daily_targets: 第一轮分配后的目标金额字典（会被修改）
        weekday_available_amounts: 每天可用的订单总金额
        remaining_target: 剩余目标金额
        remaining_days: 不足天数列表

    Returns:
        更新后的目标金额字典
    """
    if remaining_target <= 0:
        return daily_targets

    capable_days = [
        name
        for name in ["一", "二", "三", "四", "五", "六", "日"]
        if name not in remaining_days
        and weekday_available_amounts[name] > daily_targets[name]
    ]

    if not capable_days:
        return daily_targets

    total_capacity = sum(
        weekday_available_amounts[name] - daily_targets[name] for name in capable_days
    )

    if total_capacity > 0:
        for name in capable_days:
            capacity = weekday_available_amounts[name] - daily_targets[name]
            additional = (capacity / total_capacity) * remaining_target
            daily_targets[name] += min(additional, capacity)

    return daily_targets


def calculate_weekday_targets(
    weekday_available_amounts: Dict[str, float],
    target_total_amount: float,
    daily_target: float,
) -> Dict[str, float]:
    """计算每天的目标金额

    Args:
        weekday_available_amounts: 每天可用的订单总金额
        target_total_amount: 总目标金额
        daily_target: 每天的基础目标金额

    Returns:
        Dict: 每天的目标金额字典
    """
    total_available = sum(weekday_available_amounts.values())

    if total_available < target_total_amount:
        return _calculate_proportional_targets(
            weekday_available_amounts, target_total_amount, total_available
        )

    daily_targets, remaining_target, remaining_days = (
        _allocate_balanced_targets_first_round(
            weekday_available_amounts, daily_target, target_total_amount
        )
    )

    return _allocate_remaining_targets(
        daily_targets, weekday_available_amounts, remaining_target, remaining_days
    )
