"""报表生成 - 报表构建模块

包含构建报表文本的逻辑。
"""

from typing import Dict, Optional


def _build_report_title(group_id: Optional[str]) -> str:
    """构建报表标题"""
    if group_id:
        return f"归属ID {group_id} 的报表"
    return "全局报表"


def _build_period_display(period_type: str, start_date: str, end_date: str) -> str:
    """构建周期显示文本"""
    if period_type == "today":
        return f"今日数据 ({start_date})"
    elif period_type == "month":
        try:
            return (
                f"本月数据 ({start_date[:7] if len(start_date) >= 7 else start_date})"
            )
        except Exception:
            return f"本月数据 ({start_date})"
    else:
        return f"区间数据 ({start_date} 至 {end_date})"


def _build_report_base_section(
    report_title: str, now: str, period_display: str, current_data: Dict, stats: Dict
) -> str:
    """构建报表基础部分"""
    return (
        f"=== {report_title} ===\n"
        f"📅 {now}\n"
        f"{'─' * 25}\n"
        f"💰 【当前状态】\n"
        f"有效订单数: {current_data.get('valid_orders', 0)}\n"
        f"有效订单金额: {current_data.get('valid_amount', 0.0):,.2f}\n"
        f"{'─' * 25}\n"
        f"📈 【{period_display}】\n"
        f"流动资金: {stats.get('liquid_flow', 0.0):,.2f}\n"
        f"新客户数: {stats.get('new_clients', 0)}\n"
        f"新客户金额: {stats.get('new_clients_amount', 0.0):,.2f}\n"
        f"老客户数: {stats.get('old_clients', 0)}\n"
        f"老客户金额: {stats.get('old_clients_amount', 0.0):,.2f}\n"
        f"利息收入: {stats.get('interest', 0.0):,.2f}\n"
        f"完成订单数: {stats.get('completed_orders', 0)}\n"
        f"完成订单金额: {stats.get('completed_amount', 0.0):,.2f}\n"
        f"违约订单数: {stats.get('breach_orders', 0)}\n"
        f"违约订单金额: {stats.get('breach_amount', 0.0):,.2f}\n"
        f"违约完成订单数: {stats.get('breach_end_orders', 0)}\n"
        f"违约完成金额: {stats.get('breach_end_amount', 0.0):,.2f}\n"
    )


def _build_surplus_section(stats: Dict) -> str:
    """构建盈余部分"""
    surplus = (
        stats.get("interest", 0.0)
        + stats.get("breach_end_amount", 0.0)
        - stats.get("breach_amount", 0.0)
    )
    surplus_str = f"{surplus:,.2f}"
    if surplus > 0:
        return f"盈余: +{surplus_str}\n"
    elif surplus < 0:
        return f"盈余: {surplus_str}\n"
    else:
        return f"盈余: {surplus_str}\n"


def _build_expenses_section(current_data: Dict, stats: Dict) -> str:
    """构建开销与余额部分"""
    return (
        f"{'─' * 25}\n"
        f"💸 【开销与余额】\n"
        f"公司开销: {stats.get('company_expenses', 0.0):,.2f}\n"
        f"其他开销: {stats.get('other_expenses', 0.0):,.2f}\n"
        f"现金余额: {current_data.get('liquid_funds', 0.0):,.2f}\n"
    )


def build_report_text(
    period_type: str,
    start_date: str,
    end_date: str,
    group_id: Optional[str],
    current_data: Dict,
    stats: Dict,
    show_expenses: bool = True,
) -> str:
    """构建报表文本

    Args:
        period_type: 周期类型
        start_date: 开始日期
        end_date: 结束日期
        group_id: 归属ID
        current_data: 当前状态数据
        stats: 统计数据
        show_expenses: 是否显示开销

    Returns:
        str: 报表文本
    """
    from datetime import datetime

    import pytz

    report_title = _build_report_title(group_id)
    tz = pytz.timezone("Asia/Shanghai")
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M")
    period_display = _build_period_display(period_type, start_date, end_date)

    report = _build_report_base_section(
        report_title, now, period_display, current_data, stats
    )

    if group_id:
        report += _build_surplus_section(stats)

    if show_expenses:
        report += _build_expenses_section(current_data, stats)

    return report
