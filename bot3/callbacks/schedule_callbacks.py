"""定时播报回调处理器 - 主路由"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from callbacks.schedule_callbacks_actions import (handle_schedule_delete,
                                                  handle_schedule_toggle)
from callbacks.schedule_callbacks_input import (handle_schedule_chat,
                                                handle_schedule_message,
                                                handle_schedule_time)
from callbacks.schedule_callbacks_refresh import handle_schedule_refresh
from callbacks.schedule_callbacks_setup import handle_schedule_setup

logger = logging.getLogger(__name__)


async def handle_schedule_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """处理定时播报回调"""
    query = update.callback_query

    # 必须先 answer，防止客户端转圈
    try:
        await query.answer()
    except Exception:
        pass

    data = query.data

    # 刷新菜单
    if data == "schedule_refresh":
        await handle_schedule_refresh(query)
        return

    # 设置播报
    if data.startswith("schedule_setup_"):
        await handle_schedule_setup(query, data)
        return

    # 设置时间
    if data.startswith("schedule_time_"):
        await handle_schedule_time(query, data, context)
        return

    # 设置群组
    if data.startswith("schedule_chat_"):
        await handle_schedule_chat(query, data, context)
        return

    # 设置内容
    if data.startswith("schedule_message_"):
        await handle_schedule_message(query, data, context)
        return

    # 删除播报
    if data.startswith("schedule_delete_"):
        await handle_schedule_delete(query, data, context)
        return

    # 切换状态
    if data.startswith("schedule_toggle_"):
        await handle_schedule_toggle(update, context, query, data)
        return
