"""群名变更处理 - 验证模块

包含验证群名变更请求的逻辑。
"""

import logging
from typing import Optional

from telegram import Chat, Update

logger = logging.getLogger(__name__)


def validate_chat_title_change(
    update: Update,
) -> tuple[bool, Optional[Chat], Optional[str]]:
    """验证群名变更请求

    Args:
        update: Telegram更新对象

    Returns:
        Tuple: (是否有效, 聊天对象, 新群名)
    """
    if not update.message:
        return False, None, None

    chat = update.effective_chat
    new_title = update.message.new_chat_title

    if not new_title:
        logger.warning(
            f"Group title changed but new_title is None "
            f"(chat_id: {chat.id if chat else 'unknown'})"
        )
        return False, None, None

    if not chat:
        logger.warning("Group title changed but chat is None")
        return False, None, None

    logger.info(f"Group title changed to: '{new_title}' (chat_id: {chat.id})")
    return True, chat, new_title


def should_skip_title_change(context, chat_id: int) -> bool:
    """检查是否应该跳过群名变更处理

    Args:
        context: 上下文对象
        chat_id: 聊天ID

    Returns:
        bool: 是否应该跳过
    """
    # 检查是否正在等待违约完成金额输入
    if context.user_data.get("state") == "WAITING_BREACH_END_AMOUNT":
        breach_end_chat_id = context.user_data.get("breach_end_chat_id")
        if breach_end_chat_id and chat_id == breach_end_chat_id:
            logger.info(
                f"Waiting for breach end amount input, skipping title change handling "
                f"(chat_id: {chat_id})"
            )
            return True
    return False
