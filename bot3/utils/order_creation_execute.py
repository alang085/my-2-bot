"""订单创建辅助函数 - 执行模块

包含订单创建的执行流程逻辑。
"""

from typing import Any, Dict, Optional, Tuple

from telegram import Update
from telegram.ext import ContextTypes

from utils.order_creation_data import (OrderCreationParams,
                                       OrderPostCreationParams)
from utils.order_creation_database import create_order_in_database
from utils.order_creation_model import create_and_validate_order_model
from utils.order_creation_notification import (
    send_auto_broadcast_if_needed, send_order_creation_notification)
from utils.order_creation_statistics import update_statistics_for_new_order


async def _create_and_validate_order_model_step(
    update: Update,
    parsed_info: Dict[str, Any],
    chat_id: int,
    group_id: str,
    weekday_group: str,
    initial_state: str,
    order_date: Any,
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """创建并验证订单模型步骤

    Args:
        update: Telegram 更新对象
        parsed_info: 解析后的订单信息
        chat_id: 群组ID
        group_id: 归属ID
        weekday_group: 星期分组
        initial_state: 初始状态
        order_date: 订单日期

    Returns:
        (是否成功, 订单字典)
    """
    model_success, new_order, _ = await create_and_validate_order_model(
        update, parsed_info, chat_id, group_id, weekday_group, initial_state, order_date
    )
    return model_success, new_order


async def _post_creation_steps(params: OrderPostCreationParams) -> None:
    """订单创建后的后续步骤

    Args:
        params: 订单创建后处理参数
    """
    await update_statistics_for_new_order(
        params.initial_state,
        params.amount,
        params.group_id,
        params.customer,
        params.is_historical,
    )
    await send_auto_broadcast_if_needed(
        params.update,
        params.context,
        params.chat_id,
        params.amount,
        params.created_at,
        params.order_id,
        params.is_historical,
    )
    from utils.order_notification_data import OrderNotificationParams

    notification_params = OrderNotificationParams(
        update=params.update,
        context=params.context,
        order_id=params.order_id,
        group_id=params.group_id,
        created_at=params.created_at,
        weekday_group=params.weekday_group,
        customer=params.customer,
        amount=params.amount,
        initial_state=params.initial_state,
        is_historical=params.is_historical,
        chat_id=params.chat_id,
    )
    await send_order_creation_notification(notification_params)


async def _validate_and_create_order_model(
    update: Update,
    parsed_info: Dict[str, Any],
    chat_id: int,
    group_id: str,
    weekday_group: str,
    initial_state: str,
    order_date: Any,
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """验证并创建订单模型

    Args:
        update: Telegram 更新对象
        parsed_info: 解析后的订单信息
        chat_id: 群组ID
        group_id: 归属ID
        weekday_group: 星期分组
        initial_state: 初始状态
        order_date: 订单日期

    Returns:
        (是否成功, 订单字典)
    """
    return await _create_and_validate_order_model_step(
        update, parsed_info, chat_id, group_id, weekday_group, initial_state, order_date
    )


async def _save_order_to_database(update: Update, new_order: Dict[str, Any]) -> bool:
    """保存订单到数据库

    Args:
        update: Telegram 更新对象
        new_order: 订单字典

    Returns:
        是否成功
    """
    return await create_order_in_database(update, new_order)


async def execute_order_creation_flow(params: OrderCreationParams) -> bool:
    """执行订单创建流程

    Args:
        params: 订单创建参数

    Returns:
        bool: 是否成功创建
    """
    model_success, new_order = await _validate_and_create_order_model(
        params.update,
        params.parsed_info,
        params.chat_id,
        params.group_id,
        params.weekday_group,
        params.initial_state,
        params.order_date,
    )
    if not model_success or new_order is None:
        return False

    if not await _save_order_to_database(params.update, new_order):
        return False

    post_params = OrderPostCreationParams(
        update=params.update,
        context=params.context,
        order_id=params.order_id,
        customer=params.customer,
        amount=params.amount,
        initial_state=params.initial_state,
        group_id=params.group_id,
        weekday_group=params.weekday_group,
        created_at=params.created_at,
        is_historical=params.is_historical,
        chat_id=params.chat_id,
    )
    await _post_creation_steps(post_params)

    return True
