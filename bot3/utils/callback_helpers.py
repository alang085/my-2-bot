"""回调处理辅助函数"""

import logging
from typing import Optional

from telegram import CallbackQuery, InlineKeyboardMarkup, Update
from telegram.error import BadRequest

logger = logging.getLogger(__name__)


async def safe_reply_text(update: Update, text: str, **kwargs):
    """
    安全地回复消息，自动处理 callback_query 和 message 的情况

    Args:
        update: Telegram Update 对象
        text: 要发送的文本
        **kwargs: 传递给 reply_text 的其他参数

    Returns:
        Message 对象或 None
    """
    try:
        if update.callback_query:
            query = update.callback_query
            if query.message:
                return await query.message.reply_text(text, **kwargs)
            else:
                # 如果 message 不存在，使用 answer
                answer_text = text[:200] if len(text) > 200 else text
                await query.answer(answer_text, show_alert=True)
                return None
        elif update.message:
            return await update.message.reply_text(text, **kwargs)
        else:
            logger.warning("无法发送消息：update 中没有 callback_query 或 message")
            return None
    except Exception as e:
        logger.error(f"发送消息失败: {e}", exc_info=True)
        # 尝试使用 answer 作为后备
        try:
            if update.callback_query:
                await update.callback_query.answer("⚠️ 操作失败", show_alert=True)
        except Exception:
            pass
        return None


async def safe_query_reply_text(query, text: str, reply_markup=None, **kwargs):
    """
    安全地通过 callback_query 回复消息

    Args:
        query: CallbackQuery 对象
        text: 要发送的文本
        reply_markup: 可选的键盘标记
        **kwargs: 传递给 reply_text 的其他参数

    Returns:
        Message 对象或 None
    """
    try:
        if query.message:
            return await query.message.reply_text(
                text, reply_markup=reply_markup, **kwargs
            )
        else:
            # 如果 message 不存在，使用 answer
            answer_text = text[:200] if len(text) > 200 else text
            await query.answer(answer_text, show_alert=True)
            return None
    except Exception as e:
        logger.error(f"通过 query 发送消息失败: {e}", exc_info=True)
        try:
            await query.answer("⚠️ 操作失败", show_alert=True)
        except Exception as e:
            logger.debug(f"发送错误消息失败（可忽略）: {e}")
        return None


async def _handle_no_message_case(query: CallbackQuery, text: str) -> bool:
    """处理没有消息的情况"""
    try:
        answer_text = text[:200] if len(text) > 200 else text
        await query.answer(answer_text, show_alert=True)
    except Exception:
        pass
    return False


async def _handle_message_not_modified(query: CallbackQuery) -> bool:
    """处理消息内容未改变的情况"""
    logger.debug("消息内容未改变，跳过编辑")
    try:
        await query.answer()
    except Exception:
        pass
    return True


async def _handle_message_not_found(
    query: CallbackQuery,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup],
    **kwargs,
) -> bool:
    """处理消息不存在或已被删除的情况"""
    logger.warning("消息无法编辑（可能已删除）")
    try:
        await safe_query_reply_text(query, text, reply_markup=reply_markup, **kwargs)
        return True
    except Exception as send_error:
        logger.error(f"发送新消息也失败: {send_error}")
        return False


async def _handle_message_too_long(
    query: CallbackQuery,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup],
    **kwargs,
) -> bool:
    """处理消息过长的情况"""
    logger.warning("消息过长，尝试截断")
    from constants import TELEGRAM_MESSAGE_MAX_LENGTH

    truncated_text = (
        text[: TELEGRAM_MESSAGE_MAX_LENGTH - 100] + "\n\n... (消息过长，已截断)"
    )
    try:
        await query.edit_message_text(
            truncated_text, reply_markup=reply_markup, **kwargs
        )
        return True
    except Exception:
        await safe_query_reply_text(
            query, truncated_text, reply_markup=reply_markup, **kwargs
        )
        return True


async def _handle_bad_request_error(
    query: CallbackQuery,
    e: BadRequest,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup],
    **kwargs,
) -> bool:
    """处理 BadRequest 错误"""
    error_msg = str(e).lower()

    if "message is not modified" in error_msg:
        return await _handle_message_not_modified(query)

    if (
        "message to edit not found" in error_msg
        or "message can't be edited" in error_msg
    ):
        return await _handle_message_not_found(query, text, reply_markup, **kwargs)

    if "message is too long" in error_msg:
        return await _handle_message_too_long(query, text, reply_markup, **kwargs)

    logger.warning(f"编辑消息失败 (BadRequest): {e}")
    try:
        await safe_query_reply_text(query, text, reply_markup=reply_markup, **kwargs)
        return True
    except Exception:
        return False


async def safe_edit_message_text(
    query: CallbackQuery,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    **kwargs,
) -> bool:
    """
    安全地编辑消息，自动处理各种错误情况

    Args:
        query: CallbackQuery 对象
        text: 新消息文本
        reply_markup: 可选的键盘标记
        **kwargs: 其他参数

    Returns:
        bool: 是否成功
    """
    if not query.message:
        return await _handle_no_message_case(query, text)

    try:
        await query.edit_message_text(text, reply_markup=reply_markup, **kwargs)
        return True
    except BadRequest as e:
        return await _handle_bad_request_error(query, e, text, reply_markup, **kwargs)
    except Exception as e:
        logger.error(f"编辑消息失败: {e}", exc_info=True)
        try:
            await safe_query_reply_text(
                query, text, reply_markup=reply_markup, **kwargs
            )
            return True
        except Exception:
            return False
