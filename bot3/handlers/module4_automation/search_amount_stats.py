"""搜索金额输入 - 统计模块

包含统计订单分组的逻辑。
"""

from typing import Any, Dict, List


def calculate_weekday_stats(
    selected_orders: List[Dict[str, Any]],
) -> Dict[str, Dict[str, float]]:
    """计算按星期分组的统计

    Args:
        selected_orders: 选中的订单列表

    Returns:
        Dict: 星期分组统计字典
    """
    weekday_stats = {}
    for order in selected_orders:
        weekday = order.get("weekday_group", "未知")
        if weekday not in weekday_stats:
            weekday_stats[weekday] = {"count": 0, "amount": 0.0}
        weekday_stats[weekday]["count"] += 1
        weekday_stats[weekday]["amount"] += order.get("amount", 0)

    return weekday_stats


def build_result_message(
    target_amount: float,
    selected_amount: float,
    selected_count: int,
    weekday_stats: Dict[str, Dict[str, float]],
    daily_target: float,
) -> str:
    """构建结果消息

    Args:
        target_amount: 目标金额
        selected_amount: 选中金额
        selected_count: 选中订单数
        weekday_stats: 星期分组统计
        daily_target: 每天目标金额

    Returns:
        str: 结果消息
    """
    weekday_names = ["一", "二", "三", "四", "五", "六", "日"]

    result_msg = (
        f"💰 按总有效金额查找结果\n\n"
        f"目标金额: {target_amount:,.2f}\n"
        f"选中金额: {selected_amount:,.2f}\n"
        f"差额: {target_amount - selected_amount:,.2f}\n"
        f"选中订单数: {selected_count}\n\n"
        f"按星期分组统计（目标: {daily_target:,.2f}/天）:\n"
    )

    for weekday in weekday_names:
        if weekday in weekday_stats:
            stats = weekday_stats[weekday]
            actual_amount = stats["amount"]
            diff = actual_amount - daily_target
            diff_pct = (diff / daily_target * 100) if daily_target > 0 else 0
            diff_sign = "+" if diff >= 0 else ""
            result_msg += (
                f"周{weekday}: {stats['count']}个订单, "
                f"{actual_amount:,.2f} "
                f"({diff_sign}{diff:,.2f}, {diff_sign}{diff_pct:.1f}%)\n"
            )
        else:
            result_msg += f"周{weekday}: 0个订单, 0.00 (未选择)\n"

    return result_msg
