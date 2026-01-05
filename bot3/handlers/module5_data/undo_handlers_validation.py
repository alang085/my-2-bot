"""撤销操作处理器 - 验证模块

包含撤销操作的验证逻辑。
"""

import logging
from typing import Optional, Tuple

from telegram import Update
from telegram.ext import ContextTypes

from services.module5_data.undo_service import UndoService
from utils.chat_helpers import is_group_chat
from utils.date_helpers import get_daily_period_date
from utils.handler_helpers import get_user_id

logger = logging.getLogger(__name__)

# 最大连续撤销次数
MAX_UNDO_COUNT = 3


async def validate_user_and_context(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> Tuple[Optional[int], bool, Optional[int]]:
    """验证用户和上下文信息

    Args:
        update: Telegram更新对象
        context: 上下文对象

    Returns:
        Tuple[Optional[int], bool, Optional[int]]: (user_id, is_group, chat_id)
        如果验证失败，返回 (None, False, None)
    """
    user_id = get_user_id(update)
    is_group = is_group_chat(update)

    if not user_id:
        if is_group:
            await update.message.reply_text("❌ Unable to get user information")
        else:
            await update.message.reply_text("❌ 无法获取用户信息")
        return None, False, None

    # 获取当前聊天环境的 chat_id
    chat_id = update.effective_chat.id if update.effective_chat else None
    if not chat_id:
        if is_group:
            await update.message.reply_text(
                "❌ Unable to get chat environment information"
            )
        else:
            await update.message.reply_text("❌ 无法获取聊天环境信息")
        return None, False, None

    return user_id, is_group, chat_id


async def _send_undo_limit_message(update: Update, is_group: bool) -> None:
    """发送撤销次数限制消息

    Args:
        update: Telegram更新对象
        is_group: 是否为群聊
    """
    if is_group:
        await update.message.reply_text(
            f"❌ Maximum consecutive undo count reached ({MAX_UNDO_COUNT} times).\n"
            "Please enter correct data again before using undo."
        )
    else:
        await update.message.reply_text(
            f"❌ 已达到最大连续撤销次数（{MAX_UNDO_COUNT}次）。\n"
            "请重新输入正确数据后，再使用撤销功能。"
        )


async def check_undo_count_limit(
    update: Update, context: ContextTypes.DEFAULT_TYPE, is_group: bool
) -> Tuple[bool, int]:
    """检查连续撤销次数限制

    Args:
        update: Telegram更新对象
        context: 上下文对象
        is_group: 是否为群聊

    Returns:
        Tuple[bool, int]: (是否超过限制, 当前撤销次数)
    """
    undo_count = context.user_data.get("undo_count", 0)
    if undo_count >= MAX_UNDO_COUNT:
        await _send_undo_limit_message(update, is_group)
        return True, undo_count
    return False, undo_count


async def _handle_no_operation_found(
    update: Update, is_group: bool, today_date: str
) -> None:
    """处理未找到操作的情况

    Args:
        update: Telegram更新对象
        is_group: 是否为群聊
        today_date: 今天日期
    """
    if is_group:
        await update.message.reply_text(
            f"❌ No undoable operation in this group chat today ({today_date}).\n\n"
            "Note: /undo command can only undo today's operations "
            "executed in the current chat environment."
        )
    else:
        chat_type = "私聊"
        await update.message.reply_text(
            f"❌ 在当前{chat_type}环境中今天（{today_date}）没有可撤销的操作\n\n"
            "提示：/undo 命令只能撤销当天在当前聊天环境（私聊或群聊）中执行的上一个操作。"
        )


async def _handle_chat_id_mismatch(
    update: Update, is_group: bool, operation_chat_id: int, chat_id: int
) -> None:
    """处理聊天ID不匹配的情况

    Args:
        update: Telegram更新对象
        is_group: 是否为群聊
        operation_chat_id: 操作的聊天ID
        chat_id: 当前聊天ID
    """
    logger.warning(
        f"撤回操作安全验证失败：操作 chat_id ({operation_chat_id}) "
        f"与当前聊天环境 chat_id ({chat_id}) 不匹配"
    )
    if is_group:
        await update.message.reply_text(
            "❌ Security check failed: Operation does not belong to this group chat.\n\n"
            "Note: /undo command can only undo operations executed "
            "in the current chat environment."
        )
    else:
        from utils.error_messages import ErrorMessages

        await update.message.reply_text(
            f"{ErrorMessages.operation_failed('安全验证', '操作不属于当前聊天环境')}\n\n"
            "提示：/undo 命令只能撤销在当前聊天环境（私聊或群聊）中执行的操作。"
        )


async def get_and_validate_last_operation(
    update: Update, user_id: int, chat_id: int, is_group: bool
) -> Optional[dict]:
    """获取并验证最后一个操作

    Args:
        update: Telegram更新对象
        user_id: 用户ID
        chat_id: 聊天ID
        is_group: 是否为群聊

    Returns:
        Optional[dict]: 最后一个操作，如果不存在或验证失败则返回None
    """
    today_date = get_daily_period_date()
    last_operation = await UndoService.get_last_operation(user_id, chat_id, today_date)

    if not last_operation:
        await _handle_no_operation_found(update, is_group, today_date)
        return None

    operation_chat_id = last_operation.get("chat_id")
    if operation_chat_id != chat_id:
        await _handle_chat_id_mismatch(update, is_group, operation_chat_id, chat_id)
        return None

    return last_operation
