"""报表处理 - 键盘构建模块

包含构建报表按钮键盘的逻辑。
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import db_operations
from constants import ADMIN_IDS
from utils.handler_helpers import check_user_permissions


def _build_base_report_keyboard(
    group_id: str | None,
) -> List[List[InlineKeyboardButton]]:
    """构建基础报表键盘

    Args:
        group_id: 归属ID

    Returns:
        键盘按钮列表
    """
    group_key = group_id if group_id else "ALL"
    return [
        [
            InlineKeyboardButton(
                "📅 月报", callback_data=f"report_view_month_{group_key}"
            ),
            InlineKeyboardButton(
                "📆 日期查询", callback_data=f"report_view_query_{group_key}"
            ),
        ]
    ]


async def _add_expense_buttons_if_authorized(
    keyboard: List[List[InlineKeyboardButton]], user_id: int | None
) -> None:
    """如果用户有权限，添加开销按钮

    Args:
        keyboard: 键盘按钮列表
        user_id: 用户ID
    """
    if user_id:
        is_admin, is_authorized, _ = await check_user_permissions(user_id)
        if is_admin or is_authorized:
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


def _add_global_report_buttons(
    keyboard: List[List[InlineKeyboardButton]], user_id: int | None
) -> None:
    """添加全局报表按钮

    Args:
        keyboard: 键盘按钮列表
        user_id: 用户ID
    """
    keyboard.append(
        [
            InlineKeyboardButton(
                "🔍 按归属查询", callback_data="report_menu_attribution"
            ),
            InlineKeyboardButton("🔎 查找订单", callback_data="report_search_orders"),
        ]
    )
    if user_id and user_id in ADMIN_IDS:
        keyboard.append(
            [InlineKeyboardButton("💰 收入明细", callback_data="income_view_today")]
        )


async def build_report_keyboard(
    update, context: ContextTypes.DEFAULT_TYPE, group_id: str | None
) -> InlineKeyboardMarkup:
    """构建报表按钮键盘

    Args:
        update: Telegram更新对象
        context: 上下文对象
        group_id: 归属ID

    Returns:
        InlineKeyboardMarkup: 按钮键盘
    """
    keyboard = _build_base_report_keyboard(group_id)

    user_id = update.effective_user.id if update.effective_user else None
    await _add_expense_buttons_if_authorized(keyboard, user_id)

    if not group_id:
        _add_global_report_buttons(keyboard, user_id)
    else:
        keyboard.append(
            [InlineKeyboardButton("🔙 返回", callback_data="report_view_today_ALL")]
        )

    return InlineKeyboardMarkup(keyboard)
