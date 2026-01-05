"""利息处理 - 记录模块

包含记录收入明细的逻辑。
"""

import logging
from typing import Any, Dict, Optional, Tuple

import db_operations

logger = logging.getLogger(__name__)


async def record_income_detail(
    order_model: Any,
    amount_validated: float,
    date: str,
    group_id: str,
    note: str,
    user_id: Optional[int] = None,
) -> Tuple[bool, Optional[str], Optional[int]]:
    """记录收入明细

    Args:
        order_model: 订单模型
        amount_validated: 验证后的金额
        date: 日期
        group_id: 归属ID
        note: 备注
        user_id: 用户ID

    Returns:
        Tuple: (是否成功, 错误消息, 收入记录ID)
    """
    try:
        income_record_id = await db_operations.record_income(
            date=date,
            type="interest",
            amount=amount_validated,
            group_id=group_id,
            order_id=order_model.order_id,
            order_date=order_model.date,
            customer=order_model.customer,
            weekday_group=order_model.weekday_group,
            note=note,
            created_by=user_id,
        )
        return True, None, income_record_id
    except Exception as e:
        logger.error(f"记录利息收入明细失败: {e}", exc_info=True)
        return (
            False,
            (
                f"❌ Failed to record income details. "
                f"Please retry or contact admin. Error: {str(e)}"
            ),
            None,
        )
