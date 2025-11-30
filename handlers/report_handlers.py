"""报表相关处理器"""
import logging
from datetime import datetime
from typing import Optional
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import db_operations
from utils.date_helpers import get_daily_period_date
from decorators import error_handler, authorized_required, private_chat_only

logger = logging.getLogger(__name__)


async def generate_report_text(period_type: str, start_date: str, end_date: str, group_id: Optional[str] = None) -> str:
    """生成报表文本"""
    # 获取当前状态数据（资金和有效订单）
    if group_id:
        current_data = await db_operations.get_grouped_data(group_id)
        report_title = f"📊 归属ID {group_id} 报表"
    else:
        current_data = await db_operations.get_financial_data()
        report_title = "📊 全局报表"

    # 获取周期统计数据
    stats = await db_operations.get_stats_by_date_range(
        start_date, end_date, group_id)

    # 格式化时间
    tz = pytz.timezone('Asia/Shanghai')
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M")

    # 确定周期显示
    if period_type == "today":
        period_display = f"📅 今日 ({start_date})"
    elif period_type == "month":
        period_display = f"📅 本月 ({start_date[:-3]})"
    else:
        period_display = f"📅 区间 ({start_date} 至 {end_date})"

    # 计算总收入
    total_income = (
        stats['new_clients_amount'] +
        stats['old_clients_amount'] +
        stats['interest'] +
        stats['completed_amount'] +
        stats['breach_end_amount']
    )
    
    # 计算总支出
    total_expenses = (
        stats['breach_amount'] +
        stats['company_expenses'] +
        stats['other_expenses']
    )
    
    # 计算净流量（流动资金）
    net_flow = total_income - total_expenses

    # 构建报表（更清晰的格式）
    report_lines = [
        f"{report_title}",
        f"{period_display}",
        f"生成时间: {now}",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
        "📋 【当前状态】",
        f"  有效订单: {current_data['valid_orders']} 笔",
        f"  有效金额: {current_data['valid_amount']:,.2f}",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
        "📈 【收入明细】",
    ]
    
    # 收入项
    if stats['new_clients'] > 0 or stats['new_clients_amount'] > 0:
        report_lines.append(f"  新客户: {stats['new_clients']} 笔 | {stats['new_clients_amount']:,.2f}")
    if stats['old_clients'] > 0 or stats['old_clients_amount'] > 0:
        report_lines.append(f"  老客户: {stats['old_clients']} 笔 | {stats['old_clients_amount']:,.2f}")
    if stats['interest'] > 0:
        report_lines.append(f"  利息收入: {stats['interest']:,.2f}")
    if stats['completed_orders'] > 0 or stats['completed_amount'] > 0:
        report_lines.append(f"  完成订单: {stats['completed_orders']} 笔 | {stats['completed_amount']:,.2f}")
    if stats['breach_end_orders'] > 0 or stats['breach_end_amount'] > 0:
        report_lines.append(f"  违约完成: {stats['breach_end_orders']} 笔 | {stats['breach_end_amount']:,.2f}")
    
    if total_income > 0:
        report_lines.append(f"  ────────────────────────")
        report_lines.append(f"  收入合计: {total_income:,.2f}")
    
    report_lines.extend([
        "",
        "📉 【支出明细】",
    ])
    
    # 支出项
    if stats['breach_orders'] > 0 or stats['breach_amount'] > 0:
        report_lines.append(f"  违约订单: {stats['breach_orders']} 笔 | {stats['breach_amount']:,.2f}")
    if stats['company_expenses'] > 0:
        report_lines.append(f"  公司开销: {stats['company_expenses']:,.2f}")
    if stats['other_expenses'] > 0:
        report_lines.append(f"  其他开销: {stats['other_expenses']:,.2f}")
    
    if total_expenses > 0:
        report_lines.append(f"  ────────────────────────")
        report_lines.append(f"  支出合计: {total_expenses:,.2f}")
    
    report_lines.extend([
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
        "💰 【资金总结】",
        f"  流动资金: {stats['liquid_flow']:,.2f}",
        f"  （收入 {total_income:,.2f} - 支出 {total_expenses:,.2f} = {net_flow:,.2f}）",
        "",
        "💵 【账户余额】",
        f"  现金余额: {current_data['liquid_funds']:,.2f}",
    ])
    
    return "\n".join(report_lines)


@error_handler
@private_chat_only
@authorized_required
async def show_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """显示报表"""
    # 默认为今日报表
    period_type = "today"
    group_id = None

    # 处理参数
    if context.args:
        group_id = context.args[0]

    # 获取今日日期
    daily_date = get_daily_period_date()

    # 生成报表
    report_text = await generate_report_text(period_type, daily_date, daily_date, group_id)

    # 构建按钮（中文）
    keyboard = [
        [
            InlineKeyboardButton(
                "📅 月报", callback_data=f"report_view_month_{group_id if group_id else 'ALL'}"),
            InlineKeyboardButton(
                "📆 日期查询", callback_data=f"report_view_query_{group_id if group_id else 'ALL'}")
        ],
        [
            InlineKeyboardButton(
                "🏢 公司开销", callback_data="report_record_company"),
            InlineKeyboardButton(
                "📝 其他开销", callback_data="report_record_other")
        ]
    ]

    # 如果是全局报表，显示归属查询和查找功能按钮
    if not group_id:
        keyboard.append([
            InlineKeyboardButton(
                "🔍 按归属查询", callback_data="report_menu_attribution"),
            InlineKeyboardButton(
                "🔎 查找订单", callback_data="report_search_orders")
        ])
    else:
        keyboard.append([InlineKeyboardButton(
            "🔙 返回", callback_data="report_view_today_ALL")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(report_text, reply_markup=reply_markup)

