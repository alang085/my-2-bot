"""每日操作记录处理器"""

import logging
from datetime import datetime
from typing import Dict, Optional, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

import db_operations
from decorators import admin_required, error_handler, private_chat_only
from utils.date_helpers import get_daily_period_date
from utils.handler_helpers import is_admin_user

logger = logging.getLogger(__name__)

# 操作类型的中文名称映射
OPERATION_TYPE_NAMES = {
    "order_created": "订单创建",
    "order_state_change": "订单状态变更",
    "order_completed": "订单完成",
    "order_breach_end": "违约完成",
    "interest": "利息收入",
    "principal_reduction": "本金减少",
    "expense": "开销记录",
    "funds_adjustment": "资金调整",
    "operation_undo": "撤销操作",
    "attribution_created": "创建归属ID",
    "employee_added": "添加员工",
    "employee_removed": "移除员工",
    "user_permission_set": "设置用户权限",
    "user_permission_removed": "移除用户权限",
    "weekday_groups_updated": "更新星期分组",
    "statistics_fixed": "修复统计数据",
    "operation_deleted": "删除操作记录",
    "daily_data_restored": "还原当天数据",
    "payment_account_balance_updated": "更新支付账号余额",
    "payment_account_updated": "更新支付账号信息",
    "operation_modified": "修改操作记录",
    "group_message_setup": "设置群组自动消息",
    "group_message_test": "测试群组消息",
    "group_message_config_updated": "更新群组消息配置",
    "other": "其他操作",
}


def format_operation_type(op_type: str) -> str:
    """格式化操作类型名称"""
    return OPERATION_TYPE_NAMES.get(op_type, op_type)


def format_operation_detail(operation: dict) -> str:
    """格式化单个操作的详细信息"""
    from handlers.module5_data.operation_format_finance import \
        format_finance_operations
    from handlers.module5_data.operation_format_order import \
        format_order_operations
    from handlers.module5_data.operation_format_payment import \
        format_payment_operations
    from handlers.module5_data.operation_format_system import \
        format_system_operations
    from handlers.module5_data.operation_format_time import format_time_string
    from handlers.module5_data.operation_format_user import \
        format_user_operations

    op_type = operation.get("operation_type", "unknown")
    op_data = operation.get("operation_data", {})
    created_at = operation.get("created_at", "")

    # 格式化时间字符串
    time_str = format_time_string(created_at)

    detail = f"⏰ {time_str} | {format_operation_type(op_type)}"

    # 根据操作类型添加详细信息
    detail = format_order_operations(op_type, op_data, detail)
    detail = format_finance_operations(op_type, op_data, detail)
    detail = format_user_operations(op_type, op_data, detail)
    detail = format_system_operations(op_type, op_data, detail)
    detail = format_payment_operations(op_type, op_data, detail)

    # 检查是否已撤销
    if operation.get("is_undone", 0) == 1:
        detail += " [已撤销]"

    return detail


@error_handler
@admin_required
@private_chat_only
async def show_daily_operations(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """查看指定日期的操作历史（仅管理员）"""
    from handlers.module5_data.daily_ops_message import (
        build_full_operations_message, build_summary_operations_message)
    from handlers.module5_data.daily_ops_parse import parse_date_args
    from handlers.module5_data.daily_ops_send import (send_full_operations,
                                                      send_summary_operations)

    try:
        # 解析日期参数
        args = context.args if context.args else []
        date, show_all = parse_date_args(args)

        if date is None:
            await update.message.reply_text(
                "❌ 日期格式错误\n"
                "正确格式: /daily_operations 2025-01-15 [all]\n"
                "或: /daily_operations [all] (使用今天)"
            )
            return

        # 获取操作历史
        operations = await db_operations.get_operations_by_date(date)

        if not operations:
            await update.message.reply_text(f"📋 操作记录 ({date})\n\n" "暂无操作记录")
            return

        # 如果请求显示全部，或者操作数少于50条，显示完整列表
        if show_all or len(operations) <= 50:
            message_parts = build_full_operations_message(operations, date)
            await send_full_operations(update, message_parts, date)
        else:
            message = build_summary_operations_message(operations, date)
            await send_summary_operations(update, message, date)

    except Exception as e:
        logger.error(f"查看操作记录失败: {e}", exc_info=True)
        await update.message.reply_text(f"❌ 查看操作记录失败: {str(e)}")


@error_handler
@admin_required
@private_chat_only
def _parse_date_from_args(
    context: ContextTypes.DEFAULT_TYPE,
) -> Tuple[Optional[str], Optional[str]]:
    """从参数解析日期

    Args:
        context: 上下文对象

    Returns:
        (日期字符串, 错误消息)
    """
    args = context.args if context.args else []
    if not args:
        return get_daily_period_date(), None

    date_str = args[0]
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str, None
    except ValueError:
        error_msg = (
            "❌ 日期格式错误\n"
            "正确格式: /daily_operations_summary 2025-01-15\n"
            "或: /daily_operations_summary (使用今天)"
        )
        return None, error_msg


def _build_summary_message(date: str, summary: Dict) -> str:
    """构建汇总消息

    Args:
        date: 日期字符串
        summary: 汇总数据

    Returns:
        消息文本
    """
    message = f"📊 操作汇总 ({date})\n"
    message += "═══════════════════════════════════════\n"
    message += f"总操作数: {summary['total_count']}\n"
    message += f"有效操作: {summary['valid_count']}\n"
    message += f"已撤销: {summary['undone_count']}\n\n"

    if summary.get("by_type"):
        message += "📋 按操作类型:\n"
        for op_type, count in sorted(
            summary["by_type"].items(), key=lambda x: x[1], reverse=True
        ):
            message += f"  {format_operation_type(op_type)}: {count} 次\n"
        message += "\n"

    if summary.get("by_user"):
        message += "👥 按用户:\n"
        from constants import MAX_DISPLAY_ITEMS

        user_stats = sorted(
            summary["by_user"].items(), key=lambda x: x[1], reverse=True
        )[:MAX_DISPLAY_ITEMS]
        for user_id, count in user_stats:
            message += f"  用户 {user_id}: {count} 次\n"
        if len(summary["by_user"]) > MAX_DISPLAY_ITEMS:
            message += (
                f"  ... 还有 {len(summary['by_user']) - MAX_DISPLAY_ITEMS} 个用户\n"
            )

    return message


async def show_daily_operations_summary(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """查看指定日期的操作汇总（仅管理员）"""
    try:
        date, error_msg = _parse_date_from_args(context)
        if date is None:
            await update.message.reply_text(error_msg)
            return

        summary = await db_operations.get_daily_operations_summary(date)

        if not summary or summary.get("total_count", 0) == 0:
            await update.message.reply_text(f"📊 操作汇总 ({date})\n\n" "暂无操作记录")
            return

        message = _build_summary_message(date, summary)
        await update.message.reply_text(message)

    except Exception as e:
        logger.error(f"查看操作汇总失败: {e}", exc_info=True)
        await update.message.reply_text(f"❌ 查看操作汇总失败: {str(e)}")


@error_handler
@private_chat_only
async def show_daily_summary(
    update: Update, context: ContextTypes.DEFAULT_TYPE, date: str = None
):
    """显示日切数据表（仅管理员）"""
    user_id = update.effective_user.id if update.effective_user else None

    if not is_admin_user(user_id):
        await update.message.reply_text("❌ 此功能仅限管理员使用")
        return

    try:
        # 如果没有指定日期，使用当前日切日期
        if not date:
            date = get_daily_period_date()

        # 获取日切数据
        summary = await db_operations.get_daily_summary(date)

        if not summary:
            await update.message.reply_text(f"📊 日切数据 ({date})\n\n暂无数据")
            return

        # 生成报表文本
        report = f"📊 日切数据 ({date})\n"
        report += "═══════════════════════════════════════\n"
        report += f"新客户订单: {summary.get('new_clients_count', 0)} 个\n"
        report += f"新客户订单金额: {summary.get('new_clients_amount', 0.0):,.2f}\n"
        report += f"老客户订单: {summary.get('old_clients_count', 0)} 个\n"
        report += f"老客户订单金额: {summary.get('old_clients_amount', 0.0):,.2f}\n"
        report += f"完成订单: {summary.get('completed_orders_count', 0)} 个\n"
        report += f"完成订单金额: {summary.get('completed_amount', 0.0):,.2f}\n"
        report += f"违约订单: {summary.get('breach_orders_count', 0)} 个\n"
        report += f"违约订单金额: {summary.get('breach_amount', 0.0):,.2f}\n"
        report += f"违约完成: {summary.get('breach_end_orders_count', 0)} 个\n"
        report += f"违约完成金额: {summary.get('breach_end_amount', 0.0):,.2f}\n"
        report += f"当日利息: {summary.get('daily_interest', 0.0):,.2f}\n"
        report += f"公司开销: {summary.get('company_expenses', 0.0):,.2f}\n"
        report += f"其他开销: {summary.get('other_expenses', 0.0):,.2f}\n"
        total_expenses = summary.get("company_expenses", 0.0) + summary.get(
            "other_expenses", 0.0
        )
        report += f"总开销: {total_expenses:,.2f}\n"
        report += "═══════════════════════════════════════\n"

        keyboard = [
            [InlineKeyboardButton("🔙 返回报表", callback_data="report_view_today_ALL")]
        ]

        await update.message.reply_text(
            report, reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"显示日切数据失败: {e}", exc_info=True)
        await update.message.reply_text(f"❌ 显示日切数据失败: {e}")
