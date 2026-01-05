"""订单验证辅助模块

包含订单验证和获取相关的辅助函数。
"""

# 标准库
import logging
from typing import Dict, Optional, Tuple

from telegram import Update

import db_operations
from utils.models import (OrderModel, OrderStateModel, validate_amount,
                          validate_order, validate_order_state)
from utils.update_info import get_chat_info, get_user_id

logger = logging.getLogger(__name__)


async def _fetch_and_validate_order_model(
    order_dict: Dict,
) -> Tuple[Optional[OrderModel], Optional[str]]:
    """验证订单模型

    Args:
        order_dict: 订单字典

    Returns:
        (订单模型, 错误消息)
    """
    try:
        order_model = validate_order(order_dict)
        return order_model, None
    except ValueError as e:
        logger.error(f"订单验证失败: {e}")
        return None, f"❌ Failed: Order validation error: {str(e)}"


def _validate_order_state_field(
    order_dict: Dict, allowed_states: Optional[Tuple[str, ...]]
) -> Tuple[Optional[OrderStateModel], Optional[str]]:
    """验证订单状态字段

    Args:
        order_dict: 订单字典
        allowed_states: 允许的状态列表

    Returns:
        (状态模型, 错误消息)
    """
    if not allowed_states:
        return None, None

    try:
        state_model = validate_order_state(order_dict, allowed_states)
        return state_model, None
    except ValueError as e:
        return None, f"❌ Failed: Order state validation error: {str(e)}"


def _validate_order_amount_field(
    order_dict: Dict, validate_amount_field: bool
) -> Tuple[Optional[float], Optional[str]]:
    """验证订单金额字段

    Args:
        order_dict: 订单字典
        validate_amount_field: 是否验证金额

    Returns:
        (验证后的金额, 错误消息)
    """
    if not validate_amount_field:
        return None, None

    try:
        amount_validated = validate_amount(order_dict.get("amount"))
        return amount_validated, None
    except ValueError as e:
        return None, f"❌ Failed: Amount validation error: {str(e)}"


async def _get_order_dict(chat_id: int) -> Tuple[Optional[Dict], Optional[str]]:
    """获取订单字典

    Args:
        chat_id: 聊天ID

    Returns:
        (订单字典, 错误消息)
    """
    order_dict = await db_operations.get_order_by_chat_id(chat_id)
    if not order_dict:
        return None, "❌ Failed: Order not found."
    return order_dict, None


async def _validate_all_order_fields(
    order_dict: Dict,
    allowed_states: Optional[Tuple[str, ...]],
    validate_amount_field: bool,
) -> Tuple[
    Optional[OrderModel], Optional[OrderStateModel], Optional[float], Optional[str]
]:
    """验证所有订单字段

    Args:
        order_dict: 订单字典
        allowed_states: 允许的状态列表
        validate_amount_field: 是否验证金额

    Returns:
        (order_model, state_model, amount_validated, error_msg)
    """
    order_model, error_msg = await _fetch_and_validate_order_model(order_dict)
    if order_model is None:
        return None, None, None, error_msg

    state_model, error_msg = _validate_order_state_field(order_dict, allowed_states)
    if state_model is None and error_msg:
        return None, None, None, error_msg

    amount_validated, error_msg = _validate_order_amount_field(
        order_dict, validate_amount_field
    )
    if amount_validated is None and error_msg:
        return None, None, None, error_msg

    return order_model, state_model, amount_validated, None


async def get_and_validate_order(
    chat_id: int,
    allowed_states: Optional[Tuple[str, ...]] = None,
    validate_amount_field: bool = False,
) -> Tuple[
    Optional[OrderModel], Optional[OrderStateModel], Optional[float], Optional[str]
]:
    """获取并验证订单（结合Pydantic验证）

    统一处理订单获取、存在性检查和Pydantic验证

    Args:
        chat_id: 聊天ID
        allowed_states: 允许的订单状态列表，如果提供则验证状态
        validate_amount_field: 是否验证金额字段

    Returns:
        Tuple[order_model, state_model, amount_validated, error_message]:
            - order_model: 验证后的订单模型，如果订单不存在或验证失败则为None
            - state_model: 验证后的状态模型，如果验证失败则为None
            - amount_validated: 验证后的金额，如果验证失败则为None
            - error_message: 错误消息，如果没有错误则为None
    """
    try:
        order_dict, error_msg = await _get_order_dict(chat_id)
        if order_dict is None:
            return None, None, None, error_msg

        return await _validate_all_order_fields(
            order_dict, allowed_states, validate_amount_field
        )

    except ValueError as e:
        return None, None, None, f"❌ Failed: {str(e)}"
    except Exception as e:
        logger.error(f"订单验证失败: {e}", exc_info=True)
        return None, None, None, "❌ Failed: Order validation error."


async def validate_and_get_order(
    update: Update,
    chat_id: Optional[int] = None,
    allowed_states: Optional[Tuple[str, ...]] = None,
    validate_amount_field: bool = False,
) -> Tuple[
    Optional[OrderModel], Optional[OrderStateModel], Optional[float], Optional[str]
]:
    """统一验证并获取订单（带错误消息发送）

    这是 get_and_validate_order 的包装函数，自动发送错误消息

    Args:
        update: Telegram Update 对象
        chat_id: 聊天ID，如果为None则从update中获取
        allowed_states: 允许的订单状态列表
        validate_amount_field: 是否验证金额字段

    Returns:
        Tuple[order_model, state_model, amount_validated, error_message]:
            如果出错，error_message不为None，且已发送给用户
    """
    from utils.message_helpers import send_error_message

    if chat_id is None:
        chat_id, _ = get_chat_info(update)
        if not chat_id:
            error_msg = "❌ Failed: Cannot get chat ID"
            await send_error_message(update, error_msg)
            return None, None, None, error_msg

    order_model, state_model, amount, error_msg = await get_and_validate_order(
        chat_id, allowed_states, validate_amount_field
    )

    if error_msg:
        await send_error_message(update, error_msg)

    return order_model, state_model, amount, error_msg
