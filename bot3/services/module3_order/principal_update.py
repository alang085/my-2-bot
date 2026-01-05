"""本金减少处理 - 更新模块

包含更新订单金额和统计数据的逻辑。
"""

import logging
from typing import Any, Dict, Optional, Tuple

import db_operations
from utils.date_helpers import get_daily_period_date
from utils.stats_helpers import update_all_stats, update_liquid_capital

logger = logging.getLogger(__name__)


async def update_order_and_statistics(
    order_model: Any,
    old_amount: float,
    new_amount: float,
    amount_validated: float,
    group_id: str,
) -> Tuple[bool, Optional[str]]:
    """更新订单金额和统计数据

    Args:
        order_model: 订单模型
        old_amount: 旧金额
        new_amount: 新金额
        amount_validated: 验证后的金额
        group_id: 归属ID

    Returns:
        Tuple: (是否成功, 错误消息)
    """
    # 步骤1: 更新订单金额
    try:
        if not await db_operations.update_order_amount(order_model.chat_id, new_amount):
            return False, "❌ Failed: DB Error (update order amount)", None
    except Exception as e:
        logger.error(f"更新订单金额失败: {e}", exc_info=True)
        return False, f"❌ Failed to update order amount. Error: {str(e)}", None

    # 步骤2: 更新统计数据
    try:
        # 2.1 有效金额减少
        await update_all_stats("valid", -amount_validated, 0, group_id)
        # 2.2 完成金额增加
        await update_all_stats("completed", amount_validated, 0, group_id)
        # 2.3 流动资金增加
        await update_liquid_capital(amount_validated)
        return True, None
    except Exception as e:
        logger.error(f"更新本金减少统计数据失败: {e}", exc_info=True)
        # 统计数据更新失败，回滚订单金额
        try:
            await db_operations.update_order_amount(order_model.chat_id, old_amount)
            logger.info(f"已回滚订单金额: {order_model.chat_id} -> {old_amount}")
        except Exception as rollback_error:
            logger.error(f"回滚订单金额失败: {rollback_error}", exc_info=True)

        return (
            False,
            f"❌ Statistics update failed. Order amount rolled back. Error: {str(e)}",
        )
