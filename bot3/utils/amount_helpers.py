"""金额处理相关工具函数"""

import re
from typing import Any, Dict, List, Optional


def parse_amount(text: str) -> Optional[float]:
    """
    解析金额文本，支持多种格式
    例如: "20万" -> 200000, "20.5万" -> 205000, "200000" -> 200000
    """
    text = text.strip().replace(",", "")

    # 匹配"万"单位
    match = re.match(r"^(\d+(?:\.\d+)?)\s*万$", text)
    if match:
        return float(match.group(1)) * 10000

    # 匹配纯数字
    match = re.match(r"^(\d+(?:\.\d+)?)$", text)
    if match:
        return float(match.group(1))

    return None


def select_orders_by_amount(orders: List[Dict], target_amount: float) -> List[Dict]:
    """
    使用均衡算法从订单列表中选择订单，使得总金额尽可能接近目标金额
    并且订单金额分布均衡（避免全部选择大额或小额订单）
    返回选中的订单列表
    """
    from utils.amount_select_choose import select_orders_from_ranges
    from utils.amount_select_group import group_orders_by_amount_range
    from utils.amount_select_validate import validate_orders_and_amount

    # 验证订单和金额
    is_valid, valid_orders = validate_orders_and_amount(orders, target_amount)
    if not is_valid:
        return []

    # 计算订单金额范围
    amounts = [o.get("amount", 0) for o in valid_orders]
    min_amount = min(amounts)
    max_amount = max(amounts)

    # 如果金额范围很小，使用简单贪心算法
    if max_amount - min_amount < 1000:
        return _greedy_select(valid_orders, target_amount)

    # 按金额分组订单
    range_orders, _ = group_orders_by_amount_range(valid_orders)

    # 按金额排序每个区间的订单
    sorted_range_orders = []
    for range_order_list in range_orders:
        sorted_range_orders.append(
            sorted(range_order_list, key=lambda x: x.get("amount", 0), reverse=True)
        )

    # 从分组中选择订单
    selected, _ = select_orders_from_ranges(sorted_range_orders, target_amount)

    return selected


def _greedy_select(orders: List[Dict], target_amount: float) -> List[Dict]:
    """
    简单的贪心算法选择订单（用于补充或简单情况）
    """
    if not orders or target_amount <= 0:
        return []

    # 按金额降序排序
    sorted_orders = sorted(orders, key=lambda x: x.get("amount", 0), reverse=True)

    selected = []
    current_total = 0.0

    for order in sorted_orders:
        order_amount = order.get("amount", 0)
        if order_amount <= 0:
            continue

        if current_total + order_amount <= target_amount:
            selected.append(order)
            current_total += order_amount
        elif (
            current_total < target_amount
            and current_total + order_amount - target_amount < target_amount * 0.1
        ):
            # 如果超过目标金额但差额小于10%，仍然选择
            selected.append(order)
            current_total += order_amount
            break

    return selected


def distribute_orders_evenly_by_weekday(
    orders: List[Dict], target_total_amount: float
) -> List[Dict]:
    """
    从周一到周日的有效订单中，均匀地选择订单，使得总金额接近目标金额
    并且每天的订单金额尽可能均衡
    返回选中的订单列表
    """
    from utils.amount_helpers_weekday_group import group_orders_by_weekday
    from utils.amount_helpers_weekday_target import calculate_weekday_targets

    if not orders or target_total_amount <= 0:
        return []

    # 按星期分组
    weekday_orders = group_orders_by_weekday(orders)

    # 计算每天的目标金额
    daily_target = target_total_amount / 7

    # 计算每天可用的订单总金额
    weekday_available_amounts = {}
    for weekday_name in ["一", "二", "三", "四", "五", "六", "日"]:
        day_orders = weekday_orders.get(weekday_name, [])
        total_amount = sum(order.get("amount", 0) for order in day_orders)
        weekday_available_amounts[weekday_name] = total_amount

    # 计算每天的目标金额
    daily_targets = calculate_weekday_targets(
        weekday_available_amounts, target_total_amount, daily_target
    )

    # 对每天使用贪心算法选择订单
    selected_orders = []
    weekday_selected_amounts = {}

    for weekday_name in ["一", "二", "三", "四", "五", "六", "日"]:
        day_orders = weekday_orders.get(weekday_name, [])
        if day_orders and weekday_name in daily_targets:
            day_target = daily_targets[weekday_name]
            day_selected = select_orders_by_amount(day_orders, day_target)
            selected_orders.extend(day_selected)
            weekday_selected_amounts[weekday_name] = sum(
                order.get("amount", 0) for order in day_selected
            )
        else:
            weekday_selected_amounts[weekday_name] = 0.0

    return selected_orders
