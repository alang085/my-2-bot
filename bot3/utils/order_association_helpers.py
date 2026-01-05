"""订单关联辅助函数

包含订单关联的辅助函数，提取复杂逻辑。
"""

import logging
from typing import Dict, Optional, Tuple

from telegram import Update

import db_operations

logger = logging.getLogger(__name__)


async def _send_association_success_message(
    update: Update, order_id: str, manual_trigger: bool
) -> None:
    """发送关联成功消息

    Args:
        update: Telegram 更新对象
        order_id: 订单ID
        manual_trigger: 是否手动触发
    """
    if not manual_trigger:
        return

    from utils.message_helpers import send_success_message

    await send_success_message(
        update,
        f"✅ Order {order_id} has been associated to current group",
        f"✅ 订单 {order_id} 已关联到当前群组",
    )


async def _send_association_failure_message(
    update: Update, manual_trigger: bool
) -> None:
    """发送关联失败消息

    Args:
        update: Telegram 更新对象
        manual_trigger: 是否手动触发
    """
    if not manual_trigger:
        return

    from utils.message_helpers import send_error_message

    await send_error_message(update, "❌ Failed to associate order", "❌ 订单关联失败")


async def _execute_order_association(
    order_id: str, new_chat_id: int, existing_chat_id: int, existing_state: str
) -> Tuple[bool, Optional[Dict]]:
    """执行订单关联操作

    Args:
        order_id: 订单ID
        new_chat_id: 新群组ID
        existing_chat_id: 现有群组ID
        existing_state: 现有订单状态

    Returns:
        Tuple[是否成功, 更新后的订单字典]
    """
    # 完成和违约完成的订单允许关联或创建新订单
    if existing_state in ["end", "breach_end"]:
        logger.info(
            f"订单 {order_id} 已完成（状态: {existing_state}），"
            f"允许关联到当前群组或创建新订单（chat_id: {existing_chat_id} -> {new_chat_id}）"
        )
        # 继续执行关联逻辑，不阻止

    # 更新订单的 chat_id 为当前群组（关联操作）
    logger.info(
        f"关联订单 {order_id} 到群组: (chat_id {existing_chat_id} -> {new_chat_id})"
    )

    success = await db_operations.update_order_chat_id(order_id, new_chat_id)
    if success:
        updated_order = await db_operations.get_order_by_order_id(order_id)
        return True, updated_order
    return False, None
