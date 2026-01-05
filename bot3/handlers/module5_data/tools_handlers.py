"""工具函数命令处理器"""

import logging
from typing import Dict, List, Optional

from telegram import Update
from telegram.ext import ContextTypes

import db_operations
from decorators import admin_required, error_handler, private_chat_only

logger = logging.getLogger(__name__)


@error_handler
@admin_required
@private_chat_only
async def find_tail_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查找导致有效金额尾数的订单（管理员命令）"""
    from handlers.module5_data.tools_tail_analyze import analyze_order_tails
    from handlers.module5_data.tools_tail_fetch import fetch_orders_and_stats
    from handlers.module5_data.tools_tail_group import analyze_by_group_id
    from handlers.module5_data.tools_tail_message import build_result_message
    from handlers.module5_data.tools_tail_send import send_result_message

    msg = await update.message.reply_text("🔍 正在分析有效金额尾数...")

    # 获取订单和统计数据
    all_valid_orders, actual_valid_amount, stats_valid_amount = (
        await fetch_orders_and_stats()
    )

    # 分析订单尾数
    _, tail_6_orders, tail_distribution = analyze_order_tails(all_valid_orders)

    # 按归属ID分组分析
    group_analysis = await analyze_by_group_id(all_valid_orders)

    # 构建结果消息
    result_msg = build_result_message(
        all_valid_orders,
        actual_valid_amount,
        stats_valid_amount,
        tail_6_orders,
        group_analysis,
        tail_distribution,
    )

    # 发送结果消息
    await send_result_message(update, msg, result_msg)


def _validate_customer_args(
    context: ContextTypes.DEFAULT_TYPE,
) -> tuple[bool, Optional[str], Optional[str], Optional[str]]:
    """验证客户查询参数

    Returns:
        (is_valid, error_msg, customer, start_date, end_date)
    """
    if not context.args or len(context.args) == 0:
        return (
            False,
            (
                "❌ 请指定客户类型\n\n"
                "用法: /customer <客户类型> [起始日期] [结束日期]\n\n"
                "客户类型: A (新客户) 或 B (老客户)\n"
                "日期格式: YYYY-MM-DD (可选，默认查询全部)\n\n"
                "示例:\n"
                "/customer A\n"
                "/customer B 2025-01-01 2025-12-31"
            ),
            None,
            None,
            None,
        )

    customer = context.args[0].upper()
    if customer not in ["A", "B"]:
        return False, "❌ 客户类型必须是 A (新客户) 或 B (老客户)", None, None, None

    start_date = context.args[1] if len(context.args) > 1 else None
    end_date = context.args[2] if len(context.args) > 2 else None
    return True, None, customer, start_date, end_date


async def _query_customer_data(
    customer: str, start_date: Optional[str], end_date: Optional[str]
) -> tuple[Dict, List]:
    """查询客户数据

    Returns:
        (total_contribution, orders_summary)
    """
    total_contribution = await db_operations.get_customer_total_contribution(
        customer, start_date, end_date
    )
    orders_summary = await db_operations.get_customer_orders_summary(
        customer, start_date, end_date
    )
    return total_contribution, orders_summary


def _build_customer_report_header(
    customer: str, start_date: Optional[str], end_date: Optional[str]
) -> str:
    """构建报告头部

    Args:
        customer: 客户类型
        start_date: 起始日期
        end_date: 结束日期

    Returns:
        报告头部文本
    """
    customer_name = "新客户" if customer == "A" else "老客户"
    date_range = ""
    if start_date or end_date:
        date_range = (
            f"\n📅 查询日期范围: {start_date or '最早'} 至 {end_date or '最新'}"
        )

    return (
        f"📊 {customer_name} (客户类型: {customer}) 总贡献报告{date_range}\n"
        f"{'=' * 60}\n\n"
    )


def _build_contribution_summary(total_contribution: Dict) -> str:
    """构建贡献汇总部分

    Args:
        total_contribution: 总贡献数据

    Returns:
        贡献汇总文本
    """
    return (
        f"💰 总贡献汇总:\n"
        f"  总贡献金额: {total_contribution['total_amount']:,.2f}\n"
        f"  其中:\n"
        f"    - 利息收入: {total_contribution['total_interest']:,.2f} "
        f"({total_contribution['interest_count']} 次)\n"
        f"    - 完成订单: {total_contribution['total_completed']:,.2f}\n"
        f"    - 违约完成: {total_contribution['total_breach_end']:,.2f}\n"
        f"    - 本金减少: {total_contribution['total_principal_reduction']:,.2f}\n\n"
    )


def _build_orders_statistics(total_contribution: Dict) -> str:
    """构建订单统计部分

    Args:
        total_contribution: 总贡献数据

    Returns:
        订单统计文本
    """
    stats = f"📋 订单统计:\n" f"  订单数量: {total_contribution['order_count']} 个\n"

    if total_contribution.get("first_order_date"):
        stats += (
            f"  首次订单: {total_contribution['first_order_date']}\n"
            f"  最后订单: {total_contribution['last_order_date']}\n"
        )

    return stats


def _build_orders_detail(orders_summary: List) -> str:
    """构建订单明细部分

    Args:
        orders_summary: 订单汇总列表

    Returns:
        订单明细文本
    """
    if not orders_summary:
        return ""

    from constants import MAX_DISPLAY_ITEMS

    detail = f"\n📝 订单明细 (显示前 {min(10, len(orders_summary))} 个):\n"
    detail += f"{'-' * 60}\n"

    for i, order_info in enumerate(orders_summary[:MAX_DISPLAY_ITEMS], 1):
        order = order_info["order"]
        detail += (
            f"\n{i}. 订单: {order['order_id']}\n"
            f"   日期: {order['date']}\n"
            f"   状态: {order['state']}\n"
            f"   金额: {order['amount']:,.2f}\n"
            f"   贡献: {order_info['total_contribution']:,.2f}\n"
            f"      - 利息: {order_info['interest']:,.2f}\n"
            f"      - 完成: {order_info['completed']:,.2f}\n"
            f"      - 违约完成: {order_info['breach_end']:,.2f}\n"
        )

    if len(orders_summary) > MAX_DISPLAY_ITEMS:
        detail += f"\n... 还有 {len(orders_summary) - MAX_DISPLAY_ITEMS} 个订单\n"

    return detail


def _build_customer_report(
    customer: str,
    start_date: Optional[str],
    end_date: Optional[str],
    total_contribution: Dict,
    orders_summary: List,
) -> str:
    """构建客户贡献报告

    Returns:
        报告文本
    """
    report = _build_customer_report_header(customer, start_date, end_date)
    report += _build_contribution_summary(total_contribution)
    report += _build_orders_statistics(total_contribution)
    report += _build_orders_detail(orders_summary)

    return report


@error_handler
@admin_required
@private_chat_only
async def customer_contribution(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查询客户总贡献（跨所有订单周期）（管理员命令）"""
    is_valid, error_msg, customer, start_date, end_date = _validate_customer_args(
        context
    )
    if not is_valid:
        await update.message.reply_text(error_msg)
        return

    msg = await update.message.reply_text("🔍 正在查询客户总贡献，请稍候...")
    total_contribution, orders_summary = await _query_customer_data(
        customer, start_date, end_date
    )
    report = _build_customer_report(
        customer, start_date, end_date, total_contribution, orders_summary
    )
    await msg.edit_text(report)
