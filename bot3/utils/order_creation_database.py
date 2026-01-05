"""订单创建辅助函数 - 数据库操作模块

包含订单数据库创建的逻辑。
"""

import logging
from typing import Any, Dict

from telegram import Update

import db_operations
from utils.chat_helpers import is_group_chat

logger = logging.getLogger(__name__)


async def create_order_in_database(update: Update, new_order: Dict[str, Any]) -> bool:
    """创建订单到数据库

    Args:
        update: Telegram 更新对象
        new_order: 订单字典

    Returns:
        bool: 是否成功创建
    """
    success = await db_operations.create_order_in_classified_tables(new_order)

    if not success:
        if is_group_chat(update):
            await update.message.reply_text(
                "❌ Failed to create order. Order ID might duplicate."
            )
        return False

    return True
