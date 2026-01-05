"""订单状态更新辅助函数 - 状态转换模块

包含订单状态转换的逻辑。
"""

import logging
from typing import Any, Dict, Optional, Tuple

from telegram import Update
from telegram.ext import ContextTypes

from services.order_service import OrderService
from utils.chat_helpers import reply_in_group
from utils.order_state import _validate_state_transition, get_state_from_title

logger = logging.getLogger(__name__)


async def handle_state_transition(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    order: Dict[str, Any],
    current_state: str,
    title: str,
    order_id: str,
) -> None:
    """处理订单状态转换

    Args:
        update: Telegram 更新对象
        context: 上下文对象
        order: 订单字典
        current_state: 当前状态
        title: 群名
        order_id: 订单ID
    """
    target_state = get_state_from_title(title)

    # 验证状态转换是否合法
    if not _validate_state_transition(current_state, target_state, order_id):
        return

    try:
        # 确定允许的旧状态和转换类型
        allowed_old_states, transition_type = _get_state_transition_info(target_state)

        if transition_type == "complete":
            await _handle_complete_transition(update, order, order_id, target_state)
        elif allowed_old_states:
            await _handle_normal_transition(
                update, order, current_state, target_state, allowed_old_states
            )

    except Exception as e:
        logger.error(f"Auto update state failed: {e}", exc_info=True)


def _get_state_transition_info(
    target_state: str,
) -> Tuple[Tuple[str, ...], str]:
    """获取状态转换信息

    Args:
        target_state: 目标状态

    Returns:
        Tuple[Tuple[str, ...], str]: (允许的旧状态, 转换类型)
    """
    if target_state == "normal":
        return (("overdue",), "normal")
    elif target_state == "overdue":
        return (("normal",), "normal")
    elif target_state == "breach":
        return (("normal", "overdue"), "normal")
    elif target_state == "end":
        return (("normal", "overdue"), "complete")
    else:
        return ((), "normal")


async def _handle_complete_transition(
    update: Update, order: Dict[str, Any], order_id: str, target_state: str
) -> None:
    """处理完成订单的状态转换

    Args:
        update: Telegram 更新对象
        order: 订单字典
        order_id: 订单ID
        target_state: 目标状态
    """
    chat_id = order.get("chat_id")
    user_id = update.effective_user.id if update.effective_user else None

    success, error_msg, operation_data = await OrderService.complete_order(
        chat_id, user_id
    )

    if success:
        await reply_in_group(
            update,
            f"✅ Order Completed: {target_state} (Auto)\nStats moved to Completed.",
        )
    else:
        logger.error(f"Auto complete order failed: {error_msg}")
        await reply_in_group(
            update,
            f"❌ Auto complete order failed: {error_msg}",
        )


async def _handle_normal_transition(
    update: Update,
    order: Dict[str, Any],
    current_state: str,
    target_state: str,
    allowed_old_states: Tuple[str, ...],
) -> None:
    """处理普通状态转换

    Args:
        update: Telegram 更新对象
        order: 订单字典
        current_state: 当前状态
        target_state: 目标状态
        allowed_old_states: 允许的旧状态
    """
    chat_id = order.get("chat_id")
    user_id = update.effective_user.id if update.effective_user else None

    success, error_msg, operation_data = await OrderService.change_order_state(
        chat_id=chat_id,
        new_state=target_state,
        allowed_old_states=allowed_old_states,
        user_id=user_id,
    )

    if success:
        # 发送成功消息
        if target_state == "breach":
            await reply_in_group(
                update,
                f"🔄 State Changed: {target_state} (Auto)\nStats moved to Breach.",
            )
        else:
            await reply_in_group(update, f"🔄 State Changed: {target_state} (Auto)")
    else:
        logger.error(f"Auto update state failed: {error_msg}")
        await reply_in_group(
            update,
            f"❌ Auto state update failed: {error_msg}",
        )
