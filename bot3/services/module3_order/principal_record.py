"""本金减少处理 - 记录模块

包含记录收入明细的逻辑。
"""

import logging
from typing import Any, Dict, Optional

import db_operations
from utils.date_helpers import get_daily_period_date

logger = logging.getLogger(__name__)


async def record_principal_reduction_income(
    order_model: Any,
    amount_validated: float,
    new_amount: float,
    date: str,
    group_id: str,
    user_id: Optional[int] = None,
) -> Optional[int]:
    """记录本金减少收入明细

    Args:
        order_model: 订单模型
        amount_validated: 验证后的金额
        new_amount: 新金额
        date: 日期
        group_id: 归属ID
        user_id: 用户ID

    Returns:
        Optional[int]: 收入记录ID，如果失败则返回 None
    """
    income_record_id = None
    try:
        income_record_id = await db_operations.record_income(
            date=date,
            type="principal_reduction",
            amount=amount_validated,
            group_id=group_id,
            order_id=order_model.order_id,
            order_date=order_model.date,
            customer=order_model.customer,
            weekday_group=order_model.weekday_group,
            note=f"本金减少 {amount_validated:.2f}，剩余 {new_amount:.2f}",
            created_by=user_id,
        )
    except Exception as e:
        logger.error(f"记录本金减少收入明细失败: {e}", exc_info=True)
        # 收入明细记录失败，但订单金额和统计数据已更新
        # 记录错误信息，提示用户使用修复命令
        error_info = {
            "operation": "principal_reduction",
            "chat_id": order_model.chat_id,
            "order_id": order_model.order_id,
            "amount": amount_validated,
            "error": str(e),
        }
        logger.error(f"数据不一致风险: {error_info}")

    return income_record_id
