"""Telegram操作辅助函数（带重试机制）

使用Tenacity提供自动重试功能，简化错误处理
"""

import logging
from typing import Optional

from telegram import Bot
from telegram.error import NetworkError, RetryAfter, TimedOut
from tenacity import (retry, retry_if_exception_type, stop_after_attempt,
                      wait_exponential)

logger = logging.getLogger(__name__)


# 重试配置：网络错误自动重试
RETRY_CONFIG = {
    "stop": stop_after_attempt(3),
    "wait": wait_exponential(multiplier=1, min=2, max=10),
    "retry": retry_if_exception_type((NetworkError, TimedOut, RetryAfter)),
    "reraise": True,
}


@retry(**RETRY_CONFIG)
async def send_message_safe(
    bot: Bot,
    chat_id: int,
    text: str,
    parse_mode: Optional[str] = None,
    reply_markup=None,
    **kwargs,
):
    """安全发送消息（带自动重试）

    Args:
        bot: Telegram Bot实例
        chat_id: 聊天ID
        text: 消息文本
        parse_mode: 解析模式（HTML/Markdown）
        reply_markup: 内联键盘
        **kwargs: 其他参数

    Returns:
        Message对象

    Raises:
        如果重试3次后仍然失败，抛出异常
    """
    try:
        return await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
            **kwargs,
        )
    except (NetworkError, TimedOut, RetryAfter) as e:
        logger.warning(f"发送消息失败（将重试）: {e}")
        raise
    except Exception as e:
        logger.error(f"发送消息失败（不重试）: {e}", exc_info=True)
        raise


@retry(**RETRY_CONFIG)
async def edit_message_text_safe(
    bot: Bot,
    chat_id: int,
    message_id: int,
    text: str,
    parse_mode: Optional[str] = None,
    reply_markup=None,
    **kwargs,
):
    """安全编辑消息（带自动重试）

    Args:
        bot: Telegram Bot实例
        chat_id: 聊天ID
        message_id: 消息ID
        text: 新消息文本
        parse_mode: 解析模式
        reply_markup: 内联键盘
        **kwargs: 其他参数

    Returns:
        Message对象或True

    Raises:
        如果重试3次后仍然失败，抛出异常
    """
    try:
        return await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
            **kwargs,
        )
    except (NetworkError, TimedOut, RetryAfter) as e:
        logger.warning(f"编辑消息失败（将重试）: {e}")
        raise
    except Exception as e:
        logger.error(f"编辑消息失败（不重试）: {e}", exc_info=True)
        raise


@retry(**RETRY_CONFIG)
async def answer_callback_query_safe(
    bot: Bot,
    callback_query_id: str,
    text: Optional[str] = None,
    show_alert: bool = False,
    **kwargs,
):
    """安全回答回调查询（带自动重试）

    Args:
        bot: Telegram Bot实例
        callback_query_id: 回调查询ID
        text: 提示文本
        show_alert: 是否显示警告
        **kwargs: 其他参数

    Returns:
        True

    Raises:
        如果重试3次后仍然失败，抛出异常
    """
    try:
        return await bot.answer_callback_query(
            callback_query_id=callback_query_id,
            text=text,
            show_alert=show_alert,
            **kwargs,
        )
    except (NetworkError, TimedOut, RetryAfter) as e:
        logger.warning(f"回答回调查询失败（将重试）: {e}")
        raise
    except Exception as e:
        logger.error(f"回答回调查询失败（不重试）: {e}", exc_info=True)
        raise


# ========== 使用说明 ==========
#
# 这些函数可以逐步替换现有的Telegram API调用
# 使用方式：
#   - 新代码：使用 send_message_safe 等函数
#   - 现有代码：继续使用原有方式（向后兼容）
#   - 迁移：逐步将关键操作迁移到带重试的版本
#
# 优势：
#   - 自动重试网络错误
#   - 减少重复的错误处理代码
#   - 提高可靠性
#
