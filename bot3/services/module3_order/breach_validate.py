"""违约订单完成 - 验证模块

包含验证违约订单完成请求的逻辑。
"""

import logging
from typing import Dict, Optional, Tuple

import db_operations

logger = logging.getLogger(__name__)


async def validate_breach_order_completion(
    chat_id: int, amount: float
) -> Tuple[bool, Optional[str], Optional[Dict], Optional[float]]:
    """验证违约订单完成请求

    Args:
        chat_id: 聊天ID
        amount: 金额

    Returns:
        Tuple: (是否有效, 错误消息, 订单模型, 验证后的金额)
    """
    from services.module3_order.order_models import validate_order
    from services.module3_order.order_validation import (validate_amount,
                                                         validate_order_state)

    # 获取并验证订单
    order = await db_operations.get_order_by_chat_id(chat_id)
    if not order:
        return False, "❌ Order not found.", None

    try:
        order_model = validate_order(order)
        validate_order_state(order, allowed_states=("breach",))
        amount_validated = validate_amount(amount)
    except ValueError as e:
        return False, f"❌ Failed: {str(e)}", None
    except Exception as e:
        logger.error(f"订单验证失败: {e}", exc_info=True)
        return False, "❌ Failed: Order validation error.", None

    return True, None, order_model, amount_validated
