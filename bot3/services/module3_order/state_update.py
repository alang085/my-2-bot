"""订单状态变更 - 更新模块

包含更新订单状态的逻辑。
"""

import logging
from typing import Optional, Tuple

import db_operations

logger = logging.getLogger(__name__)


async def update_order_state_safe(
    chat_id: int, new_state: str
) -> Tuple[bool, Optional[str]]:
    """安全更新订单状态

    Args:
        chat_id: 聊天ID
        new_state: 新状态

    Returns:
        Tuple: (是否成功, 错误消息)
    """
    try:
        if not await db_operations.update_order_state(chat_id, new_state):
            return False, "❌ Failed: DB Error (update order state)"
    except Exception as e:
        logger.error(f"更新订单状态失败: {e}", exc_info=True)
        return False, f"❌ Failed to update order state. Error: {str(e)}"

    return True, None


async def rollback_order_state_safe(chat_id: int, old_state: str) -> None:
    """安全回滚订单状态

    Args:
        chat_id: 聊天ID
        old_state: 旧状态
    """
    try:
        await db_operations.update_order_state(chat_id, old_state)
        logger.info(f"已回滚订单状态: {chat_id} -> {old_state}")
    except Exception as rollback_error:
        logger.error(f"回滚订单状态失败: {rollback_error}", exc_info=True)
