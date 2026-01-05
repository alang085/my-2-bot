"""查找尾数订单 - 消息发送模块

包含发送结果消息的逻辑。
"""

from telegram import Message, Update

from constants import TELEGRAM_MESSAGE_SAFE_LENGTH


async def send_result_message(update: Update, msg: Message, result_msg: str) -> None:
    """发送结果消息（如果太长则分段发送）

    Args:
        update: Telegram 更新对象
        msg: 初始消息对象
        result_msg: 结果消息内容
    """
    if len(result_msg) > TELEGRAM_MESSAGE_SAFE_LENGTH:
        # 发送第一部分
        await msg.edit_text(result_msg[:TELEGRAM_MESSAGE_SAFE_LENGTH])
        # 发送剩余部分
        remaining = result_msg[TELEGRAM_MESSAGE_SAFE_LENGTH:]
        while len(remaining) > TELEGRAM_MESSAGE_SAFE_LENGTH:
            await update.message.reply_text(remaining[:TELEGRAM_MESSAGE_SAFE_LENGTH])
            remaining = remaining[TELEGRAM_MESSAGE_SAFE_LENGTH:]
        if remaining:
            await update.message.reply_text(remaining)
    else:
        await msg.edit_text(result_msg)
