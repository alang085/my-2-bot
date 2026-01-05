"""搜索回调执行模块

包含搜索执行相关的回调处理逻辑。
"""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from services.module4_automation.search_service import SearchService
from utils.message_helpers import display_search_results_helper

logger = logging.getLogger(__name__)


async def handle_search_do(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query, data: str
) -> None:
    """执行搜索操作"""
    criteria = {}
    if data.startswith("search_do_state_"):
        criteria["state"] = data[16:]
    elif data.startswith("search_do_attribution_"):
        criteria["group_id"] = data[22:]
    elif data.startswith("search_do_group_"):
        criteria["weekday_group"] = data[16:]

    orders = await SearchService.search_orders(criteria)
    await display_search_results_helper(update, context, orders)
