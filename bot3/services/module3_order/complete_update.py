"""订单完成 - 更新模块

包含更新订单状态和统计数据的逻辑。
"""

import logging
from typing import Dict, Optional, Tuple

import db_operations
from utils.date_helpers import get_daily_period_date
from utils.stats_helpers import update_all_stats, update_liquid_capital

logger = logging.getLogger(__name__)


async def update_order_state_for_completion(chat_id: int) -> Tuple[bool, Optional[str]]:
    """更新订单状态为完成

    Args:
        chat_id: 聊天ID

    Returns:
        Tuple: (是否成功, 错误消息)
    """
    try:
        if not await db_operations.update_order_state(chat_id, "end"):
            return False, "❌ Failed: DB Error (update order state)", None
        return True, None
    except Exception as e:
        logger.error(f"更新订单状态失败: {e}", exc_info=True)
        return False, f"❌ Failed to update order state. Error: {str(e)}", None


async def update_statistics_for_completion(
    amount: float, group_id: str
) -> Tuple[bool, Optional[str]]:
    """更新统计数据

    Args:
        amount: 订单金额
        group_id: 归属ID

    Returns:
        Tuple: (是否成功, 错误消息)
    """
    try:
        await update_all_stats("valid", -amount, -1, group_id)
        await update_all_stats("completed", amount, 1, group_id)
        await update_liquid_capital(amount)
        return True, None
    except Exception as e:
        logger.error(f"更新订单完成统计数据失败: {e}", exc_info=True)
        error_info = {
            "operation": "order_completed",
            "amount": amount,
            "error": str(e),
        }
        logger.error(f"数据不一致风险: {error_info}")
        return (
            False,
            (
                f"❌ Statistics update failed, but order state and income record saved. "
                f"Use /fix_statistics to repair. Error: {str(e)}"
            ),
        )
