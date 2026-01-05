"""订单创建辅助函数 - 通知模块

包含订单创建后的通知和记录逻辑。
"""

import logging
from typing import Any, Dict

from telegram import Update
from telegram.ext import ContextTypes

import db_operations
from handlers.module5_data.undo_handlers import reset_undo_count
from utils.message_builders import build_order_creation_message
from utils.order_broadcast import send_auto_broadcast
from utils.order_notification_data import (OrderNotificationParams,
                                           OrderRecordParams)

logger = logging.getLogger(__name__)


def _build_order_creation_message_data(
    order_id: str,
    group_id: str,
    created_at: str,
    weekday_group: str,
    customer: str,
    amount: float,
    initial_state: str,
    is_historical: bool,
) -> str:
    """构建订单创建消息

    Args:
        order_id: 订单ID
        group_id: 归属ID
        created_at: 创建时间
        weekday_group: 星期分组
        customer: 客户类型
        amount: 订单金额
        initial_state: 初始状态
        is_historical: 是否为历史订单

    Returns:
        消息文本
    """
    from utils.order_message_data import OrderCreationMessageParams

    message_params = OrderCreationMessageParams(
        order_id=order_id,
        group_id=group_id,
        created_at=created_at,
        weekday_group=weekday_group,
        customer=customer,
        amount=amount,
        initial_state=initial_state,
        is_historical=is_historical,
    )
    return build_order_creation_message(message_params)


async def _record_order_creation_operation(params: OrderRecordParams) -> None:
    """记录订单创建操作历史

    Args:
        params: 订单记录参数
    """
    await db_operations.record_operation(
        user_id=params.user_id,
        operation_type="order_created",
        operation_data={
            "order_id": params.order_id,
            "chat_id": params.chat_id,
            "group_id": params.group_id,
            "amount": params.amount,
            "customer": params.customer,
            "initial_state": params.initial_state,
            "is_historical": params.is_historical,
            "date": params.created_at,
        },
        chat_id=params.chat_id,
    )
    if params.context:
        reset_undo_count(params.context, params.user_id)


async def send_order_creation_notification(
    params: OrderNotificationParams,
) -> None:
    """发送订单创建通知和记录操作历史

    Args:
        params: 订单通知参数
    """
    await _send_order_creation_message(params)
    user_id = params.update.effective_user.id if params.update.effective_user else None
    if user_id:
        record_params = OrderRecordParams(
            update=params.update,
            context=params.context,
            user_id=user_id,
            order_id=params.order_id,
            chat_id=params.chat_id,
            group_id=params.group_id,
            amount=params.amount,
            customer=params.customer,
            initial_state=params.initial_state,
            is_historical=params.is_historical,
            created_at=params.created_at,
        )
        await _record_order_creation_if_needed(record_params)


async def _send_order_creation_message(params: OrderNotificationParams) -> None:
    """发送订单创建消息

    Args:
        params: 订单通知参数
    """
    msg = _build_order_creation_message_data(
        params.order_id,
        params.group_id,
        params.created_at,
        params.weekday_group,
        params.customer,
        params.amount,
        params.initial_state,
        params.is_historical,
    )
    await params.update.message.reply_text(msg)


async def _record_order_creation_if_needed(params: OrderRecordParams) -> None:
    """记录订单创建操作（如果需要）

    Args:
        params: 订单记录参数
    """
    if params.user_id:
        await _record_order_creation_operation(params)


async def send_auto_broadcast_if_needed(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    amount: float,
    created_at: str,
    order_id: str,
    is_historical: bool,
) -> None:
    """发送自动播报（如果需要）

    Args:
        update: Telegram 更新对象
        context: 上下文对象
        chat_id: 聊天ID
        amount: 订单金额
        created_at: 创建时间
        order_id: 订单ID
        is_historical: 是否为历史订单
    """
    if not is_historical:
        # 自动播报下一期还款（基于订单日期计算下个周期）
        await send_auto_broadcast(update, context, chat_id, amount, created_at)
    else:
        # 历史订单不播报
        logger.info(f"Historical order {order_id} created, skipping broadcast")
