"""回调处理辅助函数"""

import logging

from telegram import Update

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
            return await query.message.reply_text(text, reply_markup=reply_markup, **kwargs)
        else:
            # 如果 message 不存在，使用 answer
            answer_text = text[:200] if len(text) > 200 else text
            await query.answer(answer_text, show_alert=True)
            return None
    except Exception as e:
        logger.error(f"通过 query 发送消息失败: {e}", exc_info=True)
        try:
            await query.answer("⚠️ 操作失败", show_alert=True)
        except Exception:
            pass
        return None
