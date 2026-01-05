"""本金减少处理 - 验证模块

包含验证订单和金额的逻辑。
"""

import logging
from typing import Any, Dict, Optional, Tuple

from utils.handler_helpers import get_and_validate_order
from utils.models import validate_amount

logger = logging.getLogger(__name__)


async def validate_order_and_amount_for_reduction(
    order: Dict[str, Any], amount: float
) -> Tuple[bool, Optional[str], Optional[Any], Optional[float]]:
    """验证订单和金额（用于本金减少）

    Args:
        order: 订单字典
        amount: 减少的金额

    Returns:
        Tuple: (是否成功, 错误消息, 订单模型, 验证后的金额)
    """
    chat_id = order.get("chat_id")
    if not chat_id:
        return False, "❌ Failed: Order missing chat_id", None, None

    # 验证订单
    order_model, _, _, error_msg = await get_and_validate_order(
        chat_id, allowed_states=("normal", "overdue")
    )
    if error_msg:
        return False, error_msg, None, None

    # 验证金额
    try:
        amount_validated = validate_amount(amount)
    except ValueError as e:
        return False, f"❌ Failed: {str(e)}", None, None

    # 验证金额不超过订单金额
    if amount_validated > order_model.amount:
        return (
            False,
            f"❌ Failed: Exceeds order amount ({order_model.amount:.2f})",
            None,
            None,
        )

    return True, None, order_model, amount_validated
