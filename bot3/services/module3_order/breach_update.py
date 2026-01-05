"""违约订单完成 - 更新模块

包含更新订单状态和记录收入的逻辑。
"""

import logging
from typing import Dict, Optional, Tuple

import db_operations
from services.module3_order.order_models import OrderModel
from utils.date_helpers import get_daily_period_date

logger = logging.getLogger(__name__)


async def update_order_state_to_breach_end(chat_id: int) -> Tuple[bool, Optional[str]]:
    """更新订单状态为breach_end

    Args:
        chat_id: 聊天ID

    Returns:
        Tuple: (是否成功, 错误消息)
    """
    try:
        if not await db_operations.update_order_state(chat_id, "breach_end"):
            return False, "❌ Failed: DB Error (update order state)"
    except Exception as e:
        logger.error(f"更新订单状态失败: {e}", exc_info=True)
        return False, f"❌ Failed to update order state. Error: {str(e)}"

    return True, None


async def record_breach_end_income(
    order_model: OrderModel, amount: float, user_id: Optional[int]
) -> Tuple[Optional[int], Optional[str]]:
    """记录违约完成收入明细

    Args:
        order_model: 订单模型
        amount: 金额
        user_id: 用户ID

    Returns:
        Tuple: (收入记录ID, 错误消息)
    """
    group_id = order_model.group_id
    date_str = get_daily_period_date()

    try:
        income_record_id = await db_operations.record_income(
            date=date_str,
            type="breach_end",
            amount=amount,
            group_id=group_id,
            order_id=order_model.order_id,
            order_date=order_model.date,
            customer=order_model.customer,
            weekday_group=order_model.weekday_group,
            note="违约完成",
            created_by=user_id,
        )
        return income_record_id, None
    except Exception as e:
        logger.error(f"记录违约完成收入明细失败: {e}", exc_info=True)
        return None, str(e)


async def rollback_order_state(chat_id: int, target_state: str = "breach") -> None:
    """回滚订单状态

    Args:
        chat_id: 聊天ID
        target_state: 目标状态
    """
    try:
        await db_operations.update_order_state(chat_id, target_state)
        logger.info(f"已回滚订单状态: {chat_id} -> {target_state}")
    except Exception as rollback_error:
        logger.error(f"回滚订单状态失败: {rollback_error}", exc_info=True)
