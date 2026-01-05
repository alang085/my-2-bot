"""搜索金额输入 - 获取模块

包含获取订单和验证总金额的逻辑。
"""

import logging
from typing import Any, Dict, List

from telegram import Message, Update
from telegram.ext import ContextTypes

import db_operations

logger = logging.getLogger(__name__)


async def fetch_and_validate_orders(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    processing_msg: Message,
    target_amount: float,
) -> tuple[List[Dict[str, Any]], float] | None:
    """获取订单并验证总金额

    Args:
        update: Telegram 更新对象
        context: 上下文对象
        processing_msg: 处理中消息
        target_amount: 目标金额

    Returns:
        tuple: (订单列表, 总有效金额) 或 None（如果验证失败）
    """
    # 获取所有有效订单（normal和overdue状态）
    criteria = {}
    all_valid_orders = await db_operations.search_orders_advanced(criteria)

    if not all_valid_orders:
        await _delete_processing_msg(processing_msg)
        await update.message.reply_text("❌ 没有找到有效订单")
        context.user_data["state"] = None
        return None

    # 计算总有效金额
    total_valid_amount = sum(order.get("amount", 0) for order in all_valid_orders)

    if total_valid_amount < target_amount:
        await _delete_processing_msg(processing_msg)
        await update.message.reply_text(
            f"❌ 总有效金额不足\n\n"
            f"目标金额: {target_amount:,.2f}\n"
            f"当前总有效金额: {total_valid_amount:,.2f}\n"
            f"差额: {target_amount - total_valid_amount:,.2f}"
        )
        context.user_data["state"] = None
        return None

    return all_valid_orders, total_valid_amount


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
