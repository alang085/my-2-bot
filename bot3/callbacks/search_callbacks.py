"""搜索相关回调处理器"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from callbacks.search_callbacks_attribution import (
    handle_search_change_attribution, handle_search_change_to)
from callbacks.search_callbacks_execute import handle_search_do
from callbacks.search_callbacks_menu import (handle_search_lock_start,
                                             handle_search_menu_amount,
                                             handle_search_menu_attribution,
                                             handle_search_menu_group,
                                             handle_search_menu_state,
                                             handle_search_start)

logger = logging.getLogger(__name__)


async def handle_search_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理搜索相关的回调"""
    query = update.callback_query
    if not query:
        return

    data = query.data
    if not data:
        return

    # 菜单相关
    if data == "search_start":
        await handle_search_start(update, context, query)
        return
    elif data == "search_menu_state":
        await handle_search_menu_state(update, context, query)
        return
    elif data == "search_menu_attribution":
        await handle_search_menu_attribution(update, context, query)
        return
    elif data == "search_menu_group":
        await handle_search_menu_group(update, context, query)
        return
    elif data == "search_menu_amount":
        await handle_search_menu_amount(update, context, query)
        return
    elif data == "search_lock_start":
        await handle_search_lock_start(update, context, query)
        return

    # 归属变更相关
    if data == "search_change_attribution":
        await handle_search_change_attribution(update, context, query)
        return
    elif data.startswith("search_change_to_"):
        await handle_search_change_to(update, context, query, data)
        return

    # 执行搜索
    if data.startswith("search_do_"):
        await handle_search_do(update, context, query, data)
        return
