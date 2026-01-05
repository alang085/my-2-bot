"""利息处理 - 信用系统模块

包含集成信用系统的逻辑。
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


async def update_credit_system(
    order_state: str,
    customer_id: Optional[int],
    order_model: Any,
    amount_validated: float,
) -> None:
    """更新信用系统（如果订单状态为normal且有关联客户）

    Args:
        order_state: 订单状态
        customer_id: 客户ID
        order_model: 订单模型
        amount_validated: 验证后的金额
    """
    # 步骤3: 集成信用系统 - 如果订单状态为normal且有关联客户，更新信用
    if order_state in ("normal", "overdue") and customer_id:
        try:
            from services.module6_credit import (update_credit_on_payment,
                                                 update_value_on_payment)

            await update_credit_on_payment(customer_id, order_model.order_id)
            await update_value_on_payment(customer_id, amount_validated)
        except Exception as e:
            logger.warning(f"信用系统更新失败（不影响付息流程）: {e}", exc_info=True)
