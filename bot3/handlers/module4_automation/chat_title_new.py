"""群名变更处理 - 新订单模块

包含处理新订单创建的逻辑。
"""

import logging
from typing import Dict, Optional

from telegram import Chat, Update
from telegram.ext import ContextTypes

import db_operations
from utils.order_helpers import parse_order_from_title

logger = logging.getLogger(__name__)


async def _handle_completed_order_in_different_group(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    chat: Chat,
    new_title: str,
    new_order_id: str,
    existing_chat_id: int,
) -> None:
    """处理已完成订单在不同群组的情况

    Args:
        update: Telegram更新对象
        context: 上下文对象
        chat: 聊天对象
        new_title: 新群名
        new_order_id: 新订单ID
        existing_chat_id: 现有订单的群组ID
    """
    logger.info(
        f"订单 {new_order_id} 已在其他群组完成（chat_id: {existing_chat_id}），"
        f"当前群组可以创建新订单 (chat_id: {chat.id})"
    )
    from handlers.module4_automation.chat_event_handlers import \
        try_create_order_from_title

    await try_create_order_from_title(
        update, context, chat, new_title, manual_trigger=False
    )


async def _handle_existing_order_by_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    chat: Chat,
    new_title: str,
    new_order_id: str,
    existing_order_by_id: Dict,
) -> None:
    """处理已存在订单ID的情况

    Args:
        update: Telegram更新对象
        context: 上下文对象
        chat: 聊天对象
        new_title: 新群名
        new_order_id: 新订单ID
        existing_order_by_id: 已存在的订单
    """
    existing_state = existing_order_by_id.get("state")
    existing_chat_id = existing_order_by_id.get("chat_id")

    if existing_state in ["end", "breach_end"]:
        if existing_chat_id != chat.id:
            await _handle_completed_order_in_different_group(
                update, context, chat, new_title, new_order_id, existing_chat_id
            )
        else:
            logger.info(
                f"订单 {new_order_id} 已在当前群组完成，不创建新订单 (chat_id: {chat.id})"
            )
    else:
        logger.warning(
            f"订单 {new_order_id} 存在但状态为 {existing_state}，"
            f"但get_order_by_chat_id未找到，可能存在数据不一致 (chat_id: {chat.id})"
        )


async def handle_new_order_creation(
    update: Update, context: ContextTypes.DEFAULT_TYPE, chat: Chat, new_title: str
) -> None:
    """处理新订单创建

    Args:
        update: Telegram更新对象
        context: 上下文对象
        chat: 聊天对象
        new_title: 新群名
    """
    parsed_info = parse_order_from_title(new_title)

    if not parsed_info:
        logger.info(
            f"Group title '{new_title}' does not match order pattern, "
            f"skipping order creation (chat_id: {chat.id})"
        )
        return

    new_order_id = parsed_info.get("order_id")
    existing_order_by_id = await db_operations.get_order_by_order_id(new_order_id)

    if existing_order_by_id:
        await _handle_existing_order_by_id(
            update, context, chat, new_title, new_order_id, existing_order_by_id
        )
    else:
        logger.info(
            f"No existing order, attempting to create from title: '{new_title}'"
        )
        from handlers.module4_automation.chat_event_handlers import \
            try_create_order_from_title

        await try_create_order_from_title(
            update, context, chat, new_title, manual_trigger=False
        )
