"""订单导入 - 下载模块

包含下载Excel文件的逻辑。
"""

import logging
import os
from pathlib import Path

from telegram import Message
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def download_excel_file(
    document, file_name: str, context: ContextTypes.DEFAULT_TYPE
) -> tuple[Path, int]:
    """下载Excel文件

    Args:
        document: Telegram文档对象
        file_name: 文件名
        context: 上下文对象

    Returns:
        Tuple: (文件路径, 文件大小)
    """
    # 创建临时目录
    temp_dir = Path("/app/data/temp")
    temp_dir.mkdir(parents=True, exist_ok=True)

    # 下载文件
    file_path = temp_dir / file_name
    logger.info(f"下载Excel文件到: {file_path}")

    file = await context.bot.get_file(document.file_id)
    await file.download_to_drive(file_path)

    file_size = os.path.getsize(file_path)
    logger.info(f"文件下载完成: {file_path} (大小: {file_size} 字节)")

    return file_path, file_size


async def update_download_message(
    processing_msg: Message, file_name: str, file_size: int
) -> None:
    """更新下载完成消息

    Args:
        processing_msg: 处理中消息对象
        file_name: 文件名
        file_size: 文件大小
    """
    await processing_msg.edit_text(
        f"✅ 文件下载完成\n"
        f"📄 文件名: {file_name}\n"
        f"📊 大小: {file_size} 字节\n\n"
        f"🔄 开始反推订单..."
    )
