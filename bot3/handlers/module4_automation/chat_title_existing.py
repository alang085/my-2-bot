"""群名变更处理 - 现有订单模块

包含处理现有订单的逻辑。
"""

import logging
from typing import Dict, Optional

from telegram import Chat, Update
from telegram.ext import ContextTypes

import db_operations
from utils.order_state import update_order_state_from_title

logger = logging.getLogger(__name__)


async def _handle_archived_order(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    existing_order: Dict,
    new_title: str,
    chat: Chat,
) -> None:
    """处理归档订单（已完成订单）

    Args:
        update: Telegram更新对象
        context: 上下文对象
        existing_order: 现有订单
        new_title: 新群名
        chat: 聊天对象
    """
    logger.info(
        f"订单 {existing_order.get('order_id', 'unknown')} 状态为 {existing_order.get('state')}（归档状态），"
        f"不可更改任何数据，数据库留档"
    )

    from utils.order_helpers import parse_order_from_title

    parsed_info = parse_order_from_title(new_title)
    if not parsed_info:
        logger.info(f"归档订单存在，但新群名无法解析，不创建订单 (chat_id: {chat.id})")
        return

    new_order_id = parsed_info.get("order_id")
    old_order_id = existing_order.get("order_id")

    if new_order_id and new_order_id != old_order_id:
        logger.info(
            f"归档订单 {old_order_id} 存在，但新群名解析出不同的订单ID {new_order_id}，"
            f"允许创建新订单 (chat_id: {chat.id})"
        )
        from handlers.module4_automation.chat_event_handlers import \
            try_create_order_from_title

        await try_create_order_from_title(
            update, context, chat, new_title, manual_trigger=False
        )
    else:
        logger.info(
            f"归档订单 {old_order_id} 存在，新群名解析出相同的订单ID，"
            f"不创建新订单 (chat_id: {chat.id})"
        )


async def handle_existing_order(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    existing_order: Dict,
    new_title: str,
    chat: Chat,
) -> bool:
    """处理现有订单

    Args:
        update: Telegram更新对象
        context: 上下文对象
        existing_order: 现有订单
        new_title: 新群名
        chat: 聊天对象

    Returns:
        bool: 是否已处理（True表示已处理，不需要继续）
    """
    current_state = existing_order.get("state")
    if current_state in ["end", "breach_end"]:
        await _handle_archived_order(update, context, existing_order, new_title, chat)
        return True

    logger.info(f"Order exists, updating state from title: '{new_title}'")
    await update_order_state_from_title(update, context, existing_order, new_title)
    return True
