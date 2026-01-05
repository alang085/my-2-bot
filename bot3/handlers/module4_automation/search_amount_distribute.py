"""搜索金额输入 - 分配模块

包含分配订单的逻辑。
"""

import logging
from typing import Any, Dict, List

from telegram import Message, Update
from telegram.ext import ContextTypes

from utils.amount_helpers import distribute_orders_evenly_by_weekday

logger = logging.getLogger(__name__)


async def distribute_orders_safely(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    processing_msg: Message,
    all_valid_orders: List[Dict[str, Any]],
    target_amount: float,
) -> List[Dict[str, Any]] | None:
    """安全地分配订单

    Args:
        update: Telegram 更新对象
        context: 上下文对象
        processing_msg: 处理中消息
        all_valid_orders: 所有有效订单
        target_amount: 目标金额

    Returns:
        List: 选中的订单列表，如果失败则返回 None
    """
    # 均匀分配选择订单
    try:
        selected_orders = distribute_orders_evenly_by_weekday(
            all_valid_orders, target_amount
        )
    except Exception as e:
        logger.error(f"分配订单时出错: {e}", exc_info=True)
        await _delete_processing_msg(processing_msg)
        await update.message.reply_text(f"⚠️ 处理订单时出错: {e}")
        context.user_data["state"] = None
        return None

    if not selected_orders:
        await _delete_processing_msg(processing_msg)
        await update.message.reply_text("❌ 无法选择订单，请尝试调整目标金额")
        context.user_data["state"] = None
        return None

    return selected_orders


async def _delete_processing_msg(processing_msg: Message) -> None:
    """删除处理中消息（忽略错误）

    Args:
        processing_msg: 处理中消息
    """
    try:
        await processing_msg.delete()
    except Exception:
        # Telegram API调用失败（如消息已被删除），忽略即可
        pass
