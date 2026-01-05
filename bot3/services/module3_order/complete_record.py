"""订单完成 - 记录模块

包含记录收入明细和操作历史的逻辑。
"""

import logging
from typing import Dict, Optional

import db_operations
from utils.date_helpers import get_daily_period_date

logger = logging.getLogger(__name__)


async def record_income_for_completion(
    order_model: Dict, amount: float, group_id: str, user_id: Optional[int] = None
) -> Tuple[bool, Optional[str], Optional[int], Optional[str]]:
    """记录订单完成收入明细

    Args:
        order_model: 订单模型
        amount: 订单金额
        group_id: 归属ID
        user_id: 用户ID

    Returns:
        Tuple: (是否成功, 错误消息, 收入记录ID, 旧状态)
    """
    date_str = get_daily_period_date()
    old_state = order_model.state

    try:
        income_record_id = await db_operations.record_income(
            date=date_str,
            type="completed",
            amount=amount,
            group_id=group_id,
            order_id=order_model.order_id,
            order_date=order_model.date,
            customer=order_model.customer,
            weekday_group=order_model.weekday_group,
            note="订单完成",
            created_by=user_id,
        )
        return True, None, income_record_id, old_state
    except Exception as e:
        logger.error(f"记录订单完成收入明细失败: {e}", exc_info=True)
        # 回滚订单状态
        try:
            await db_operations.update_order_state(order_model.chat_id, old_state)
            logger.info(f"已回滚订单状态: {order_model.chat_id} -> {old_state}")
        except Exception as rollback_error:
            logger.error(f"回滚订单状态失败: {rollback_error}", exc_info=True)
        return (
            False,
            f"❌ Failed to record income details. Order state rolled back. Error: {str(e)}",
            None,
            old_state,
        )


async def record_operation_history(params: "CompletionHistoryParams") -> None:
    """记录操作历史

    Args:
        params: 订单完成历史参数
    """
    from services.module3_order.order_completion_data import \
        CompletionHistoryParams

    user_id = params.user_id
    chat_id = params.chat_id
    order_id = params.order_model.order_id
    group_id = params.group_id
    amount = params.amount
    old_state = params.old_state
    date_str = params.date_str
    income_record_id = params.income_record_id
    if user_id:
        try:
            operation_data = {
                "chat_id": chat_id,
                "order_id": order_id,
                "group_id": group_id,
                "amount": amount,
                "old_state": old_state,
                "date": date_str,
                "income_record_id": income_record_id,
            }
            await db_operations.record_operation(
                user_id=user_id,
                operation_type="order_completed",
                operation_data=operation_data,
                chat_id=chat_id,
            )
        except Exception as e:
            logger.warning(f"记录操作历史失败（不影响主流程）: {e}", exc_info=True)
