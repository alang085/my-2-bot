"""订单完成 - 验证模块

包含验证订单的逻辑。
"""

import logging
from typing import Dict, Optional, Tuple

import db_operations
from utils.date_helpers import get_daily_period_date
from utils.handler_helpers import (validate_amount, validate_order,
                                   validate_order_state)

logger = logging.getLogger(__name__)


async def validate_order_for_completion(
    chat_id: int,
) -> Tuple[
    bool, Optional[str], Optional[Dict], Optional[str], Optional[str], Optional[float]
]:
    """验证订单是否可以完成

    Args:
        chat_id: 聊天ID

    Returns:
        Tuple: (是否成功, 错误消息, 订单模型, 旧状态, 归属ID, 金额)
    """
    # 获取并验证订单
    order = await db_operations.get_order_by_chat_id(chat_id)
    if not order:
        return False, "❌ Order not found.", None, None, None, None

    try:
        order_model = validate_order(order)
        validate_order_state(order, allowed_states=("normal", "overdue"))
        amount_validated = validate_amount(order["amount"])
    except ValueError as e:
        return False, f"❌ Failed: {str(e)}", None, None, None, None
    except Exception as e:
        logger.error(f"订单验证失败: {e}", exc_info=True)
        return False, "❌ Failed: Order validation error.", None, None, None, None

    old_state = order_model.state
    group_id = order_model.group_id
    amount = amount_validated

    return True, None, order_model, old_state, group_id, amount
