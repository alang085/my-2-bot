"""利息处理 - 验证模块

包含验证订单和金额的逻辑。
"""

import logging
from typing import Any, Dict, Optional, Tuple

from utils.handler_helpers import get_and_validate_order

logger = logging.getLogger(__name__)


async def validate_order_and_amount(
    order: Dict[str, Any], amount: float
) -> Tuple[bool, Optional[str], Optional[Any], Optional[float]]:
    """验证订单和金额

    Args:
        order: 订单字典
        amount: 利息金额

    Returns:
        Tuple: (是否成功, 错误消息, 订单模型, 验证后的金额)
    """
    chat_id = order.get("chat_id")
    if not chat_id:
        return False, "❌ Failed: Order missing chat_id", None, None

    # 验证订单（允许所有状态，包括已完成状态）
    order_model, _, _, error_msg = await get_and_validate_order(chat_id)
    if error_msg:
        return False, error_msg, None, None

    # 验证金额
    try:
        from utils.models import validate_amount

        amount_validated = validate_amount(amount)
    except ValueError as e:
        return False, f"❌ Failed: {str(e)}", None, None

    return True, None, order_model, amount_validated
