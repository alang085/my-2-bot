"""支付余额历史处理 - 消息发送模块

包含发送消息的辅助函数。
"""

from telegram import Update


async def send_message(update: Update, msg: str) -> None:
    """发送消息（支持message和callback_query）

    Args:
        update: Telegram 更新对象
        msg: 消息内容
    """
    if update.message:
        await update.message.reply_text(msg)
    elif update.callback_query:
        await update.callback_query.edit_message_text(msg)


async def send_error_message(update: Update, error_msg: str) -> None:
    """发送错误消息

    Args:
        update: Telegram 更新对象
        error_msg: 错误消息
    """
    await send_message(update, error_msg)
