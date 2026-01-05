"""诊断辅助函数 - 消息发送

包含消息发送和分段的逻辑。
"""

import logging
from typing import List

from telegram import Message, Update

logger = logging.getLogger(__name__)


async def send_long_message(
    update: Update,
    msg: Message,
    output: str,
    max_length: int = 4096,
    chunk_size: int = 4000,
) -> None:
    """发送长消息（自动分段）

    Args:
        update: Telegram更新对象
        msg: 初始消息对象
        output: 要发送的文本
        max_length: Telegram消息最大长度
        chunk_size: 每个分段的建议大小
    """
    if len(output) > max_length:
        # 分段发送
        chunks = []
        current_chunk = ""
        for line in output.split("\n"):
            if len(current_chunk) + len(line) + 1 > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = line + "\n"
            else:
                current_chunk += line + "\n"
        if current_chunk:
            chunks.append(current_chunk)

        # 发送第一段
        if chunks:
            await msg.edit_text(f"```\n{chunks[0]}\n```", parse_mode="Markdown")

            # 发送剩余段
            for i, chunk in enumerate(chunks[1:], 1):
                await update.message.reply_text(
                    f"```\n[第 {i+1} 段]\n{chunk}\n```", parse_mode="Markdown"
                )
    else:
        # 输出不太长，直接发送
        if output:
            await msg.edit_text(f"```\n{output}\n```", parse_mode="Markdown")
        else:
            await msg.edit_text("❌ 检查完成，但没有数据")
