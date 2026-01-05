"""订单状态变更 - 验证模块

包含验证订单状态变更请求的逻辑。
"""

import logging
from typing import Dict, Optional, Tuple

import db_operations
from utils.models import validate_amount, validate_order, validate_order_state

logger = logging.getLogger(__name__)


async def validate_order_state_change(
    chat_id: int, allowed_old_states: Tuple[str, ...]
) -> Tuple[bool, Optional[str], Optional[Dict]]:
    """验证订单状态变更请求

    Args:
        chat_id: 聊天ID
        allowed_old_states: 允许的旧状态列表

    Returns:
        Tuple: (是否有效, 错误消息, 订单模型)
    """
    # 获取并验证订单
    order = await db_operations.get_order_by_chat_id(chat_id)
    if not order:
        return False, "❌ Order not found.", None

    try:
        order_model = validate_order(order)
        old_state = order_model.state

        # 检查订单是否已完成：已完成订单（end）和违约完成订单（breach_end）不允许修改状态
        if old_state in ("end", "breach_end"):
            return (
                False,
                f"❌ 订单已完成（状态：{old_state}），不允许修改状态。可以创建新订单。",
                None,
            )

        validate_order_state(order, allowed_states=allowed_old_states)
        amount_validated = validate_amount(order["amount"])
    except ValueError as e:
        return False, f"❌ Failed: {str(e)}", None
    except Exception as e:
        logger.error(f"订单验证失败: {e}", exc_info=True)
        return False, "❌ Failed: Order validation error.", None

    return True, None, order_model, old_state, amount_validated
