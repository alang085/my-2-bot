"""订单操作回调处理器 - 状态设置模块

包含订单状态设置相关的回调处理逻辑。
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from handlers.module3_order.state_handlers import (set_breach, set_breach_end,
                                                   set_end, set_normal,
                                                   set_overdue)
from utils.chat_helpers import is_group_chat

logger = logging.getLogger(__name__)


async def handle_order_state_action(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query, action: str
) -> None:
    """处理订单状态设置操作"""
    is_group = is_group_chat(update)

    # 在群聊中，删除订单状态消息，只保留执行结果
    if is_group and action in ["normal", "overdue", "end", "breach", "breach_end"]:
        try:
            await query.delete_message()
        except Exception:
            pass

    # 根据操作类型调用相应的处理函数
    if action == "normal":
        await set_normal(update, context)
    elif action == "overdue":
        await set_overdue(update, context)
    elif action == "end":
        await set_end(update, context)
    elif action == "breach":
        await set_breach(update, context)
    elif action == "breach_end":
        await set_breach_end(update, context)
    elif action == "create":
        await _handle_create_action(query, is_group)


async def _handle_create_action(query, is_group: bool) -> None:
    """处理创建订单操作（仅提示用法）"""
    try:
        if query.message:
            await query.message.reply_text(
                "To create an order, please use command: "
                "/create <Group ID> <Customer A/B> <Amount>"
            )
        else:
            await query.answer(
                "Use command: /create <Group ID> <Customer A/B> <Amount>",
                show_alert=True,
            )
    except Exception as e:
        logger.error(f"发送创建订单提示失败: {e}", exc_info=True)
        await query.answer("Use /create command", show_alert=True)
