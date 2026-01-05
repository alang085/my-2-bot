"""报表处理 - 消息发送模块

包含发送报表消息的逻辑。
"""

from telegram import Update
from telegram.ext import ContextTypes

from constants import TELEGRAM_MESSAGE_MAX_LENGTH


async def send_report_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE, report_text: str, reply_markup
) -> None:
    """发送报表消息（如果太长则分段发送）

    Args:
        update: Telegram更新对象
        context: 上下文对象
        report_text: 报表文本
        reply_markup: 按钮键盘
    """
    if len(report_text) > TELEGRAM_MESSAGE_MAX_LENGTH:
        # 分段发送
        chunks = []
        current_chunk = ""
        for line in report_text.split("\n"):
            if (
                len(current_chunk) + len(line) + 1 > TELEGRAM_MESSAGE_MAX_LENGTH - 200
            ):  # 留200字符余量
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = line + "\n"
            else:
                current_chunk += line + "\n"
        if current_chunk:
            chunks.append(current_chunk)

        # 发送第一段（带按钮）
        if chunks:
            first_chunk = chunks[0]
            if len(chunks) > 1:
                first_chunk += f"\n\n⚠️ 报表内容较长，已分段显示 ({len(chunks)}段)"
            await update.message.reply_text(first_chunk, reply_markup=reply_markup)

            # 发送剩余段
            for i, chunk in enumerate(chunks[1:], 2):
                await update.message.reply_text(f"[第 {i}/{len(chunks)} 段]\n\n{chunk}")
    else:
        await update.message.reply_text(report_text, reply_markup=reply_markup)
