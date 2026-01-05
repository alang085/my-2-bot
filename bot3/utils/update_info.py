"""Update信息提取模块

包含从Telegram Update对象中提取信息的辅助函数。
"""

# 标准库
from typing import Callable, Optional, Tuple

from telegram import Update

logger = __import__("logging").getLogger(__name__)


def get_chat_info(update: Update) -> Tuple[Optional[int], Optional[Callable]]:
    """从update中提取chat_id和reply_func

    统一处理 message 和 callback_query 两种情况

    Args:
        update: Telegram Update 对象

    Returns:
        Tuple[chat_id, reply_func]:
            - chat_id: 聊天ID，如果无法获取则返回None
            - reply_func: 回复函数，如果无法获取则返回None
    """
    if update.message:
        return update.message.chat_id, update.message.reply_text
    elif update.callback_query and update.callback_query.message:
        return (
            update.callback_query.message.chat_id,
            update.callback_query.message.reply_text,
        )
    return None, None


def get_user_id(update: Update) -> Optional[int]:
    """从update中提取user_id

    Args:
        update: Telegram Update 对象

    Returns:
        user_id: 用户ID，如果无法获取则返回None
    """
    # 防御性检查
    if not update or not update.effective_user:
        return None

    user_id = getattr(update.effective_user, "id", None)
    if isinstance(user_id, int):
        return user_id
    return None


def require_chat_info(update: Update) -> Tuple[int, Callable]:
    """要求必须获取到chat_id和reply_func，否则抛出异常

    用于必须要有chat_id和reply_func的场景

    Args:
        update: Telegram Update 对象

    Returns:
        Tuple[chat_id, reply_func]: 保证不为None

    Raises:
        ValueError: 如果无法获取chat_id或reply_func
    """
    chat_id, reply_func = get_chat_info(update)
    if not chat_id or not reply_func:
        raise ValueError("无法从update中获取chat_id或reply_func")
    return chat_id, reply_func


def get_user_info(update: Update) -> Tuple[Optional[int], Optional[str], Optional[str]]:
    """从update中提取用户信息

    Args:
        update: Telegram Update 对象

    Returns:
        Tuple[user_id, username, first_name]:
            - user_id: 用户ID
            - username: 用户名（可能为None）
            - first_name: 名字（可能为None）
    """
    if not update.effective_user:
        return None, None, None

    user = update.effective_user
    return (
        user.id,
        user.username,
        user.first_name,
    )
