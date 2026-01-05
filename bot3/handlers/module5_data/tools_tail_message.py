"""查找尾数订单 - 消息构建模块

包含构建结果消息的逻辑。
"""

from typing import Any, Dict, List


def build_result_message(
    all_valid_orders: List[Dict[str, Any]],
    actual_valid_amount: float,
    stats_valid_amount: float,
    tail_6_orders: List[Dict[str, Any]],
    group_analysis: Dict[str, Dict[str, Any]],
    tail_distribution: Dict[int, List[Dict[str, Any]]],
) -> str:
    """构建结果消息

    Args:
        all_valid_orders: 所有有效订单列表
        actual_valid_amount: 实际有效金额
        stats_valid_amount: 统计有效金额
        tail_6_orders: 尾数为6的订单列表
        group_analysis: 分组分析结果
        tail_distribution: 尾数分布字典

    Returns:
        str: 结果消息
    """
    result_msg = "🔍 有效金额尾数分析报告\n\n"
    result_msg += _build_summary_section(
        all_valid_orders, actual_valid_amount, stats_valid_amount
    )
    result_msg += _build_tail_analysis_section(
        actual_valid_amount, stats_valid_amount, tail_6_orders
    )
    result_msg += _build_group_analysis_section(group_analysis)
    result_msg += _build_tail_distribution_section(tail_distribution)
    result_msg += _build_reason_analysis_section(
        actual_valid_amount, stats_valid_amount, tail_6_orders
    )

    return result_msg


def _build_summary_section(
    all_valid_orders: List[Dict[str, Any]],
    actual_valid_amount: float,
    stats_valid_amount: float,
) -> str:
    """构建总体统计部分

    Args:
        all_valid_orders: 所有有效订单列表
        actual_valid_amount: 实际有效金额
        stats_valid_amount: 统计有效金额

    Returns:
        str: 总体统计消息
    """
    msg = "📊 总体统计：\n"
    msg += f"有效订单数: {len(all_valid_orders)}\n"
    msg += f"实际有效金额: {actual_valid_amount:,.2f}\n"
    msg += f"统计有效金额: {stats_valid_amount:,.2f}\n"
    msg += f"差异: {stats_valid_amount - actual_valid_amount:,.2f}\n\n"
    return msg


def _build_tail_analysis_section(
    actual_valid_amount: float,
    stats_valid_amount: float,
    tail_6_orders: List[Dict[str, Any]],
) -> str:
    """构建尾数分析部分

    Args:
        actual_valid_amount: 实际有效金额
        stats_valid_amount: 统计有效金额
        tail_6_orders: 尾数为6的订单列表

    Returns:
        str: 尾数分析消息
    """
    msg = ""
    actual_tail = int(actual_valid_amount % 1000)
    stats_tail = int(stats_valid_amount % 1000)

    if actual_tail == 6:
        msg += "⚠️ 实际有效金额尾数是 6\n"
    elif stats_tail == 6:
        msg += f"⚠️ 统计有效金额尾数是 6（但实际尾数是 {actual_tail}）\n"
        msg += "   说明统计数据不一致，建议运行 /fix_statistics\n\n"
    else:
        msg += f"✅ 总金额尾数: 实际={actual_tail}, 统计={stats_tail}\n\n"

    # 显示尾数为6的订单
    if tail_6_orders:
        msg += f"⚠️ 发现 {len(tail_6_orders)} 个尾数为 6 的订单：\n\n"
        for order in tail_6_orders:
            msg += (
                f"订单ID: {order.get('order_id')}\n"
                f"金额: {order.get('amount'):,.2f}\n"
                f"状态: {order.get('state')}\n"
                f"归属: {order.get('group_id')}\n"
                f"日期: {order.get('date')}\n"
                f"客户: {order.get('customer', 'N/A')}\n\n"
            )
    else:
        msg += "✅ 没有找到尾数为 6 的订单\n\n"

    return msg


def _build_group_analysis_section(group_analysis: Dict[str, Dict[str, Any]]) -> str:
    """构建分组分析部分

    Args:
        group_analysis: 分组分析结果

    Returns:
        str: 分组分析消息
    """
    msg = "📋 按归属ID分组分析：\n\n"
    for group_id in sorted(group_analysis.keys()):
        analysis = group_analysis[group_id]
        msg += f"{group_id}:\n"
        msg += f"  实际金额: {analysis['actual_amount']:,.2f} (尾数: {analysis['actual_tail']})\n"
        msg += f"  统计金额: {analysis['stats_amount']:,.2f} (尾数: {analysis['stats_tail']})\n"

        if analysis["actual_tail"] == 6 or analysis["stats_tail"] == 6:
            msg += "  ⚠️ 该归属ID导致尾数6！\n"

        if analysis["non_thousand"]:
            msg += f"  非整千数订单: {len(analysis['non_thousand'])} 个\n"
            for order in analysis["non_thousand"][:3]:
                amount = order.get("amount", 0)
                tail = int(amount % 1000)
                msg += f"    - {order.get('order_id')}: {amount:,.2f} (尾数: {tail})\n"
            if len(analysis["non_thousand"]) > 3:
                msg += f"    ... 还有 {len(analysis['non_thousand']) - 3} 个\n"
        msg += "\n"

    return msg


def _build_tail_distribution_section(
    tail_distribution: Dict[int, List[Dict[str, Any]]],
) -> str:
    """构建尾数分布统计部分

    Args:
        tail_distribution: 尾数分布字典

    Returns:
        str: 尾数分布统计消息
    """
    msg = ""
    if tail_distribution:
        msg += f"📊 尾数分布统计：\n"
        for tail in sorted(tail_distribution.keys()):
            count = len(tail_distribution[tail])
            total = sum(o.get("amount", 0) for o in tail_distribution[tail])
            msg += f"  尾数 {tail}: {count} 个订单, 总金额: {total:,.2f}\n"
        msg += "\n"

    return msg


def _build_reason_analysis_section(
    actual_valid_amount: float,
    stats_valid_amount: float,
    tail_6_orders: List[Dict[str, Any]],
) -> str:
    """构建原因分析部分

    Args:
        actual_valid_amount: 实际有效金额
        stats_valid_amount: 统计有效金额
        tail_6_orders: 尾数为6的订单列表

    Returns:
        str: 原因分析消息
    """
    msg = ""
    actual_tail = int(actual_valid_amount % 1000)
    stats_tail = int(stats_valid_amount % 1000)

    if stats_tail == 6 and actual_tail != 6:
        msg += "💡 原因分析：\n"
        msg += "统计金额尾数为6，但实际订单金额尾数不是6\n"
        msg += "说明统计数据与实际订单数据不一致\n"
        msg += "建议：运行 /fix_statistics 修复统计数据\n"
    elif actual_tail == 6:
        msg += "💡 原因分析：\n"
        if tail_6_orders:
            msg += f"找到 {len(tail_6_orders)} 个订单金额尾数为6\n"
            msg += "可能原因：\n"
            msg += "1. 订单创建时输入了非整千数金额\n"
            msg += "2. 执行了本金减少操作（+<金额>b），减少的金额不是整千数\n"
            msg += "3. 例如：订单原金额10000，执行+9994b后，剩余金额为6\n"
        else:
            msg += "未找到尾数为6的订单，但总金额尾数是6\n"
            msg += "可能是多个订单的尾数累加导致的\n"

    return msg
