"""群组事件处理器（新成员入群、群名变更）"""

# 标准库
import logging

# 第三方库
from telegram import Update
from telegram.ext import ContextTypes

# 本地模块
import db_operations
from decorators import error_handler
from utils.order_helpers import (try_create_order_from_title,
                                 update_order_state_from_title)
from utils.schedule_executor import (_combine_fixed_message_with_anti_fraud,
                                     _send_group_message,
                                     get_current_weekday_index,
                                     get_weekday_message)

logger = logging.getLogger(__name__)


async def _handle_bot_added_to_group(
    update: Update, context: ContextTypes.DEFAULT_TYPE, chat, title: str
) -> None:
    """处理机器人被添加到群组的情况

    Args:
        update: Telegram更新对象
        context: 上下文对象
        chat: 聊天对象
        title: 群组标题
    """
    if not title:
        logger.warning(f"Bot added to group but no title found (chat_id: {chat.id})")
        return

    logger.info(f"Bot added to group: '{title}' (chat_id: {chat.id})")

    if "⭕️" in title or "❌⭕️" in title:
        logger.info(
            f"Group title contains completion markers, skipping order creation "
            f"(chat_id: {chat.id})"
        )
        return

    await try_create_order_from_title(
        update, context, chat, title, manual_trigger=False
    )


async def _send_welcome_messages_to_new_members(
    context: ContextTypes.DEFAULT_TYPE, chat, new_members: list, config: dict
) -> None:
    """向新成员发送欢迎信息

    Args:
        context: 上下文对象
        chat: 聊天对象
        new_members: 新成员列表
        config: 群组配置
    """
    chat_title = chat.title or "群组"
    weekday_index = get_current_weekday_index()
    welcome_message = get_weekday_message(config, "welcome_message", weekday_index)

    if not welcome_message:
        return

    bot_links = config.get("bot_links") or None
    worker_links = config.get("worker_links") or None
    anti_fraud = get_weekday_message(config, "anti_fraud_message", weekday_index)

    for member in new_members:
        try:
            username = member.username or member.first_name or "新成员"
            combined_message = _combine_fixed_message_with_anti_fraud(
                welcome_message, anti_fraud, bot_links, worker_links
            )

            await _send_group_message(
                context.bot, chat.id, combined_message, parse_mode="HTML"
            )
            logger.info(f"Sent welcome message to {username} in {chat_title}")
        except Exception as e:
            logger.error(f"Failed to send welcome message: {e}", exc_info=True)


async def _handle_new_members_joined(
    context: ContextTypes.DEFAULT_TYPE, chat, new_members: list
) -> None:
    """处理新成员加入的情况

    Args:
        context: 上下文对象
        chat: 聊天对象
        new_members: 新成员列表
    """
    if not new_members:
        return

    config = await db_operations.get_group_message_config_by_chat_id(chat.id)
    if config and config.get("is_active"):
        await _send_welcome_messages_to_new_members(context, chat, new_members, config)


@error_handler
async def handle_new_chat_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理新成员入群（机器人入群或新成员加入）"""
    if not update.message or not update.message.new_chat_members:
        return

    chat = update.effective_chat
    if not chat:
        return

    bot_id = context.bot.id
    new_members = []
    is_bot_added = False

    for member in update.message.new_chat_members:
        if member.id == bot_id:
            is_bot_added = True
        else:
            new_members.append(member)

    if is_bot_added:
        await _handle_bot_added_to_group(update, context, chat, chat.title)

    await _handle_new_members_joined(context, chat, new_members)


@error_handler
async def handle_new_chat_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理群名变更"""
    from handlers.module4_automation.chat_title_existing import \
        handle_existing_order
    from handlers.module4_automation.chat_title_new import \
        handle_new_order_creation
    from handlers.module4_automation.chat_title_validate import (
        should_skip_title_change, validate_chat_title_change)

    # 验证群名变更请求
    is_valid, chat, new_title = validate_chat_title_change(update)
    if not is_valid:
        return

    # 检查是否应该跳过处理
    if should_skip_title_change(context, chat.id):
        return

    # 检查是否存在订单
    existing_order = await db_operations.get_order_by_chat_id(chat.id)
    if existing_order:
        # 处理现有订单
        handled = await handle_existing_order(
            update, context, existing_order, new_title, chat
        )
        if handled:
            return
    else:
        # 处理新订单创建
        await handle_new_order_creation(update, context, chat, new_title)
