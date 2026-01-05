"""订单状态更新辅助函数 - 验证模块

包含订单状态更新的验证逻辑。
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def validate_order_for_state_update(
    order: Dict[str, Any],
) -> tuple[bool, Optional[str]]:
    """验证订单是否可以更新状态

    Args:
        order: 订单字典

    Returns:
        Tuple[bool, Optional[str]]: (是否有效, 订单ID)
    """
    current_state = order.get("state")
    if not current_state:
        order_id = order.get("order_id", "unknown")
        logger.warning(f"订单缺少状态信息: {order_id}")
        return False, None

    order_id = order.get("order_id", "unknown")
    chat_id = order.get("chat_id")

    if not chat_id:
        logger.error(f"订单缺少 chat_id: {order_id}")
        return False, None

    # 归档订单保护：end 和 breach_end 状态的订单归档，不可更改任何数据
    if current_state in ["end", "breach_end"]:
        logger.info(
            f"订单 {order_id} 状态为 {current_state}（归档状态），跳过所有更新，保持数据不变"
        )
        return False, None

    return True, order_id


def should_skip_state_update(current_state: str, target_state: str) -> bool:
    """判断是否应该跳过状态更新

    Args:
        current_state: 当前状态
        target_state: 目标状态

    Returns:
        bool: 是否应该跳过
    """
    return current_state == target_state
