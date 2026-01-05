"""报表回调视图处理模块

包含报表视图相关的回调处理逻辑。
"""

import logging
from datetime import datetime

import pytz
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from callbacks.report_callbacks_base import check_expense_permission
from config import ADMIN_IDS
from handlers.data_access import get_user_group_id
from services.module5_data.report_service import ReportService
from utils.callback_helpers import safe_edit_message_text
from utils.date_helpers import get_daily_period_date

logger = logging.getLogger(__name__)


async def handle_report_view_today(
    query,
    context: ContextTypes.DEFAULT_TYPE,
    group_id: str,
    user_id: int,
    user_group_id: str,
) -> None:
    """处理今日报表视图"""
    # 必须先 answer，防止客户端转圈
    try:
        await query.answer()
    except Exception:
        pass  # 忽略 answer 错误（例如 query 已过期）
    
    date = get_daily_period_date()
    # 如果用户有权限限制，不显示开销与余额
    show_expenses = not user_group_id
    report_text = await ReportService.generate_report_text(
        "today", date, date, group_id, show_expenses=show_expenses
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "📅 月报",
                callback_data=f"report_view_month_{group_id if group_id else 'ALL'}",
            ),
            InlineKeyboardButton(
                "📆 日期查询",
                callback_data=f"report_view_query_{group_id if group_id else 'ALL'}",
            ),
        ]
    ]

    # 只有有权限的用户才显示开销按钮
    if await check_expense_permission(user_id):
        keyboard.append(
            [
                InlineKeyboardButton(
                    "🏢 公司开销", callback_data="report_record_company"
                ),
                InlineKeyboardButton(
                    "📝 其他开销", callback_data="report_record_other"
                ),
            ]
        )

    # 全局视图添加通用按钮（但用户有权限限制时不显示）
    if not group_id and not user_group_id:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "🔍 按归属查询", callback_data="report_menu_attribution"
                ),
                InlineKeyboardButton(
                    "🔎 查找订单", callback_data="report_search_orders"
                ),
            ]
        )
        # 仅管理员显示收入明细和订单总表按钮
        if user_id and user_id in ADMIN_IDS:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "💰 收入明细", callback_data="income_view_today"
                    ),
                    InlineKeyboardButton(
                        "📊 订单总表", callback_data="order_table_view"
                    ),
                ]
            )
    elif group_id:
        # 如果用户有权限限制，不显示返回按钮（因为不能返回全局视图）
        if not user_group_id:
            keyboard.append(
                [InlineKeyboardButton("🔙 返回", callback_data="report_view_today_ALL")]
            )

    await safe_edit_message_text(
        query, report_text, reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_report_view_month(
    query,
    context: ContextTypes.DEFAULT_TYPE,
    group_id: str,
    user_id: int,
    user_group_id: str,
) -> None:
    """处理月报视图"""
    # 必须先 answer，防止客户端转圈
    try:
        await query.answer()
    except Exception:
        pass  # 忽略 answer 错误（例如 query 已过期）
    
    # 如果用户有权限限制，确保使用用户的归属ID
    if user_group_id:
        group_id = user_group_id

    tz = pytz.timezone("Asia/Shanghai")
    now = datetime.now(tz)
    start_date = now.replace(day=1).strftime("%Y-%m-%d")
    end_date = get_daily_period_date()

    # 如果用户有权限限制，不显示开销与余额
    show_expenses = not user_group_id
    report_text = await ReportService.generate_report_text(
        "month", start_date, end_date, group_id, show_expenses=show_expenses
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "📄 今日报表",
                callback_data=f"report_view_today_{group_id if group_id else 'ALL'}",
            ),
            InlineKeyboardButton(
                "📆 日期查询",
                callback_data=f"report_view_query_{group_id if group_id else 'ALL'}",
            ),
        ]
    ]

    # 只有有权限的用户才显示开销按钮
    if await check_expense_permission(user_id):
        keyboard.append(
            [
                InlineKeyboardButton(
                    "🏢 公司开销", callback_data="report_record_company"
                ),
                InlineKeyboardButton(
                    "📝 其他开销", callback_data="report_record_other"
                ),
            ]
        )
    await safe_edit_message_text(
        query, report_text, reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_report_view_query(
    query, context: ContextTypes.DEFAULT_TYPE, group_id: str, user_group_id: str
) -> None:
    """处理日期查询视图"""
    # 必须先 answer，防止客户端转圈
    try:
        await query.answer()
    except Exception:
        pass  # 忽略 answer 错误（例如 query 已过期）
    
    # 如果用户有权限限制，确保使用用户的归属ID
    if user_group_id:
        group_id = user_group_id

    try:
        if query.message:
            await query.message.reply_text(
                "📆 请输入查询日期范围：\n"
                "格式1 (单日): 2024-01-01\n"
                "格式2 (范围): 2024-01-01 2024-01-31\n"
                "输入 'cancel' 取消"
            )
        else:
            await query.answer("请输入查询日期范围", show_alert=True)
    except Exception as e:
        logger.error(f"发送查询日期范围提示失败: {e}", exc_info=True)
        await query.answer("请输入查询日期范围", show_alert=True)
    context.user_data["state"] = "REPORT_QUERY"
    context.user_data["report_group_id"] = group_id
