"""搜索相关处理器"""

import logging
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from decorators import error_handler
from services.module4_automation.search_service import SearchService
from utils.message_helpers import display_search_results_helper

logger = logging.getLogger(__name__)


@error_handler
def _build_search_menu_keyboard() -> InlineKeyboardMarkup:
    """构建搜索菜单键盘

    Returns:
        内联键盘
    """
    keyboard = [
        [
            InlineKeyboardButton("按状态", callback_data="search_menu_state"),
            InlineKeyboardButton("按归属ID", callback_data="search_menu_attribution"),
            InlineKeyboardButton("按星期分组", callback_data="search_menu_group"),
        ],
        [InlineKeyboardButton("按总有效金额", callback_data="search_menu_amount")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def _show_search_menu(update: Update) -> None:
    """显示搜索菜单"""
    reply_markup = _build_search_menu_keyboard()
    await update.message.reply_text("🔍 查找方式:", reply_markup=reply_markup)


def _parse_search_criteria_from_args(
    context: ContextTypes.DEFAULT_TYPE,
) -> Optional[dict]:
    """从命令行参数解析搜索条件

    Args:
        context: 上下文对象

    Returns:
        搜索条件字典，如果解析失败则返回None
    """
    from handlers.module4_automation.search_criteria_parser import \
        parse_search_criteria

    return parse_search_criteria(context)


async def _handle_search_with_criteria(
    update: Update, context: ContextTypes.DEFAULT_TYPE, criteria: dict
) -> None:
    """使用搜索条件执行搜索"""
    orders = await SearchService.search_orders(criteria)
    await display_search_results_helper(update, context, orders)


async def search_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """查找订单（支持交互式菜单和旧命令方式）"""
    if not context.args or len(context.args) < 2:
        await _show_search_menu(update)
        return

    criteria = _parse_search_criteria_from_args(context)
    if not criteria:
        search_type = context.args[0].lower() if context.args else "unknown"
        if search_type == "date":
            await update.message.reply_text(
                "Please provide Start Date and End Date (Format: YYYY-MM-DD)"
            )
        elif search_type == "group":
            await update.message.reply_text("Please provide Group (e.g., Mon, Tue)")
        elif search_type == "order_id":
            await update.message.reply_text("Please provide Order ID")
        elif search_type == "group_id":
            await update.message.reply_text("Please provide Group ID")
        elif search_type == "customer":
            await update.message.reply_text("Please provide Customer Type (A or B)")
        elif search_type == "state":
            await update.message.reply_text("Please provide State")
        else:
            await update.message.reply_text(f"Unknown search type: {search_type}")
        return

    await _handle_search_with_criteria(update, context, criteria)
