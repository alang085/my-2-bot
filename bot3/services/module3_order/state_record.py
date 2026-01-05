"""订单状态变更 - 操作记录模块

包含记录操作历史的逻辑。
"""

import logging
from typing import Dict, Optional

import db_operations

logger = logging.getLogger(__name__)


async def record_order_state_change_operation(
    user_id: Optional[int], operation_data: Dict, chat_id: int
) -> None:
    """记录订单状态变更操作历史

    Args:
        user_id: 用户ID
        operation_data: 操作数据
        chat_id: 聊天ID
    """
    if user_id:
        try:
            await db_operations.record_operation(
                user_id=user_id,
                operation_type="order_state_change",
                operation_data=operation_data,
                chat_id=chat_id,
            )
        except Exception as e:
            logger.warning(f"记录操作历史失败（不影响主流程）: {e}", exc_info=True)
