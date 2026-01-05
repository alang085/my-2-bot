"""订单操作回调处理器 - 主路由"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from callbacks.order_callbacks_attribution import (
    handle_order_change_attribution, handle_order_change_to)
from callbacks.order_callbacks_navigation import handle_order_action_back
from callbacks.order_callbacks_state import handle_order_state_action

logger = logging.getLogger(__name__)


async def handle_order_action_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """处理订单操作的回调"""
    query = update.callback_query
    if not query:
        return

    # 获取原始数据
    data = query.data
    if not data:
        return

    # 处理更改归属的回调
    if data == "order_action_change_attribution":
        await handle_order_change_attribution(update, context, query)
        return

    # 处理选择归属ID的回调
    if data.startswith("order_change_to_"):
        await handle_order_change_to(update, context, query, data)
        return

    # 处理返回按钮
    if data == "order_action_back":
        await handle_order_action_back(update, context, query)
        return

    # 处理其他操作（状态设置等）
    action = data.replace("order_action_", "")
    await handle_order_state_action(update, context, query, action)

    # 尝试 answer callback，消除加载状态
    try:
        await query.answer()
    except Exception:
        pass
