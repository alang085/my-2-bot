"""订单创建主函数

包含从群名创建订单的主函数 try_create_order_from_title。
由于函数较长，拆分为多个辅助函数以提高可读性。
"""

# 标准库
import logging
import re
from datetime import date
from typing import Any, Dict, Optional, Tuple

# 第三方库
from telegram import Bot, Update
from telegram.ext import ContextTypes

# 本地模块
import db_operations
from config import BOT_TOKEN
from constants import HISTORICAL_THRESHOLD_DATE, ORDER_CREATE_CUTOFF_DATE
from utils.chat_helpers import get_weekday_group_from_date, is_group_chat
from utils.message_builders import build_order_creation_message
from utils.models import OrderCreateModel, validate_amount
from utils.order_broadcast import send_auto_broadcast
from utils.order_creation import (_create_new_order_internal,
                                  _handle_parse_error,
                                  _update_existing_order_from_parsed_info)
from utils.order_parsing import get_state_from_title, parse_order_from_title
from utils.order_state import (_handle_state_transition_stats,
                               _record_state_change_operation,
                               _validate_state_transition,
                               update_order_state_from_title)
from utils.stats_helpers import update_all_stats, update_liquid_capital

logger = logging.getLogger(__name__)


async def _get_existing_order_title(existing_chat_id: int) -> Optional[str]:
    """获取现有订单的群组标题

    Args:
        existing_chat_id: 现有订单的群组ID

    Returns:
        群组标题，如果获取失败则返回None
    """
    try:
        bot = Bot(token=BOT_TOKEN)
        existing_chat = await bot.get_chat(existing_chat_id)
        existing_title = existing_chat.title
        await bot.close()
        return existing_title
    except Exception as e:
        logger.warning(f"无法获取现有订单的群组标题 (chat_id: {existing_chat_id}): {e}")
        return None


async def _handle_title_match(
    update: Update,
    order_id: str,
    existing_order_by_id: Dict[str, Any],
    existing_chat_id: int,
    chat_id: int,
    title: str,
    manual_trigger: bool,
) -> Optional[Dict[str, Any]]:
    """处理群组标题匹配的情况

    Returns:
        如果应该继续处理，返回订单字典；如果应该返回，返回None
    """
    existing_state = existing_order_by_id.get("state")

    # 规则：完成或违约完成状态的订单不可更改数据，但可以创建新订单
    if existing_state in ["end", "breach_end"]:
        logger.info(
            f"订单 {order_id} 已完成（状态: {existing_state}），"
            f"不可更改订单数据，允许创建新订单（chat_id: {chat_id}）"
        )
        return None  # 返回None以允许创建新订单

    logger.info(
        f"订单 {order_id} 群组标题匹配: '{title}', 更新 chat_id: {existing_chat_id} -> {chat_id}"
    )
    if existing_chat_id != chat_id:
        success = await db_operations.update_order_chat_id(order_id, chat_id)
        if success:
            existing_order_by_id["chat_id"] = chat_id
        else:
            if manual_trigger:
                from utils.message_helpers import send_error_message

                await send_error_message(
                    update,
                    "❌ Failed to update order chat_id",
                    "❌ 订单 chat_id 更新失败",
                )
            return None
    return existing_order_by_id


async def _handle_order_association(
    params: "OrderAssociationParams",
) -> Optional[Dict[str, Any]]:
    """处理订单关联到当前群组

    Args:
        params: 订单关联参数

    Returns:
        如果关联成功返回None，否则返回None
    """
    from utils.order_association_data import OrderAssociationParams

    update = params.update
    order_id = params.order_id
    existing_chat_id = params.existing_chat_id
    chat_id = params.chat_id
    existing_title = params.existing_title
    title = params.title
    existing_state = params.existing_state
    manual_trigger = params.manual_trigger
    if existing_state in ["end", "breach_end"]:
        logger.info(
            f"订单 {order_id} 已完成（状态: {existing_state}），"
            f"允许关联到当前群组或创建新订单（chat_id: {existing_chat_id} -> {chat_id}）"
        )

    logger.info(
        f"关联订单 {order_id} 到群组: 原群组标题='{existing_title}', 新群组标题='{title}' "
        f"(chat_id {existing_chat_id} -> {chat_id})"
    )
    success = await db_operations.update_order_chat_id(order_id, chat_id)
    if success:
        if manual_trigger:
            if is_group_chat(update):
                await update.message.reply_text(
                    f"✅ Order {order_id} has been associated to current group"
                )
            else:
                await update.message.reply_text(f"✅ 订单 {order_id} 已关联到当前群组")
        return None
    else:
        if manual_trigger:
            if is_group_chat(update):
                await update.message.reply_text("❌ Failed to associate order")
            else:
                await update.message.reply_text("❌ 订单关联失败")
        return None


async def _handle_existing_order_by_id(
    update: Update,
    order_id: str,
    existing_order_by_id: Dict[str, Any],
    chat_id: int,
    title: str,
    manual_trigger: bool,
) -> Optional[Dict[str, Any]]:
    """处理通过订单ID找到的现有订单

    Returns:
        如果应该继续处理，返回订单字典；如果应该返回，返回None
    """
    existing_chat_id = existing_order_by_id.get("chat_id")
    existing_state = existing_order_by_id.get("state")

    existing_title = await _get_existing_order_title(existing_chat_id)

    if existing_title and existing_title == title:
        return await _handle_title_match(
            update,
            order_id,
            existing_order_by_id,
            existing_chat_id,
            chat_id,
            title,
            manual_trigger,
        )
    if existing_chat_id != chat_id:
        from utils.order_association_data import OrderAssociationParams

        association_params = OrderAssociationParams(
            update=update,
            order_id=order_id,
            existing_chat_id=existing_chat_id,
            chat_id=chat_id,
            existing_title=existing_title,
            title=title,
            existing_state=existing_state,
            manual_trigger=manual_trigger,
        )
        return await _handle_order_association(association_params)
    return existing_order_by_id


def _should_create_new_order(order_date: date) -> bool:
    """判断是否应该创建新订单而不是更新

    Args:
        order_date: 订单日期

    Returns:
        是否应该创建新订单
    """
    cutoff_date = date(*ORDER_CREATE_CUTOFF_DATE)
    return order_date >= cutoff_date


async def _update_order_data(
    chat_id: int, parsed_info: Dict[str, Any], title: str, order_date: date
) -> bool:
    """更新订单数据

    Returns:
        是否成功
    """
    initial_state = get_state_from_title(title)
    update_data = {
        "order_id": parsed_info["order_id"],
        "date": order_date,
        "customer": parsed_info["customer"],
        "amount": parsed_info["amount"],
        "state": initial_state,
    }
    return await db_operations.update_order_from_parsed_info(chat_id, update_data)


async def _handle_state_transition_for_update(
    update: Update,
    existing_order: Dict[str, Any],
    initial_state: str,
    order_id: str,
    amount: float,
) -> None:
    """处理订单更新时的状态转换

    Args:
        update: Telegram更新对象
        existing_order: 现有订单
        initial_state: 初始状态
        order_id: 订单ID
        amount: 订单金额
    """
    old_state = existing_order.get("state")
    if old_state != initial_state and _validate_state_transition(
        old_state, initial_state, order_id
    ):
        group_id = existing_order.get("group_id", "S01")
        await _handle_state_transition_stats(
            update, old_state, initial_state, existing_order, group_id, amount
        )
        await _record_state_change_operation(
            update,
            existing_order.get("chat_id"),
            order_id,
            old_state,
            initial_state,
            group_id,
            amount,
        )


async def _send_update_result_message(update: Update, success: bool) -> None:
    """发送更新结果消息"""
    if is_group_chat(update):
        message = "✅ Order updated" if success else "❌ Failed to update order"
    else:
        message = "✅ 订单已更新" if success else "❌ 订单更新失败"
    await update.message.reply_text(message)


async def _handle_existing_order_update(
    update: Update,
    chat_id: int,
    existing_order: Dict[str, Any],
    parsed_info: Dict[str, Any],
    title: str,
    order_date: date,
) -> bool:
    """处理现有订单的更新逻辑

    Returns:
        如果已处理完成返回True，否则返回False
    """
    if _should_create_new_order(order_date):
        logger.info(
            f"订单日期 {order_date} >= {date(*ORDER_CREATE_CUTOFF_DATE)}，"
            f"创建新订单而不是更新（chat_id: {chat_id}）"
        )
        return False

    logger.info(
        f"订单日期 {order_date} < {date(*ORDER_CREATE_CUTOFF_DATE)}，"
        f"更新现有订单（chat_id: {chat_id}）"
    )

    success = await _update_order_data(chat_id, parsed_info, title, order_date)
    if success:
        initial_state = get_state_from_title(title)
        await _handle_state_transition_for_update(
            update,
            existing_order,
            initial_state,
            parsed_info["order_id"],
            parsed_info["amount"],
        )

    await _send_update_result_message(update, success)
    return True


async def _parse_and_validate_title(
    update: Update, title: str, manual_trigger: bool
) -> Optional[Dict]:
    """解析并验证群名，返回解析结果或None"""
    parsed_info = parse_order_from_title(title)
    if not parsed_info:
        await _handle_parse_error(update, title, manual_trigger)
        return None

    logger.info(
        f"Parsed order info: order_id={parsed_info['order_id']}, "
        f"customer={parsed_info['customer']}, date={parsed_info['date']}, "
        f"amount={parsed_info['amount']}"
    )
    return parsed_info


async def _find_existing_order_by_id(
    update: Update, order_id: str, chat_id: int, title: str, manual_trigger: bool
) -> Tuple[Optional[Dict], bool]:
    """查找并处理通过订单ID找到的订单，返回(订单, 是否已处理完成)"""
    existing_order_by_id = await db_operations.get_order_by_order_id(order_id)
    if existing_order_by_id:
        result = await _handle_existing_order_by_id(
            update, order_id, existing_order_by_id, chat_id, title, manual_trigger
        )
        if result is None:
            return None, True
        return result, False
    return await db_operations.get_order_by_chat_id_including_archived(chat_id), False


async def _handle_existing_order_logic(
    params: "ExistingOrderLogicParams",
) -> bool:
    """处理已存在订单的逻辑，返回是否已处理完成

    Args:
        params: 已存在订单逻辑参数

    Returns:
        是否已处理完成
    """
    from utils.order_handling_data import ExistingOrderLogicParams

    current_state = params.existing_order.get("state")
    existing_order_id = params.existing_order.get("order_id")

    if current_state in ["end", "breach_end"]:
        logger.info(
            f"订单 {existing_order_id} 已完成（状态: {current_state}），"
            f"允许创建新订单 {params.order_id}（chat_id: {params.chat_id}）"
        )
        return False

    if params.manual_trigger:
        order_date = params.parsed_info["date"]
        handled = await _handle_existing_order_update(
            params.update,
            params.chat_id,
            params.existing_order,
            params.parsed_info,
            params.title,
            order_date,
        )
        return handled
    else:
        await update_order_state_from_title(
            params.update, params.context, params.existing_order, params.title
        )
        return True


async def _handle_existing_order_flow(params: "ExistingOrderFlowParams") -> bool:
    """处理已存在订单的流程

    Args:
        params: 已存在订单流程参数

    Returns:
        是否已处理
    """
    from utils.order_handling_data import (ExistingOrderFlowParams,
                                           ExistingOrderLogicParams)

    logic_params = ExistingOrderLogicParams(
        update=params.update,
        context=params.context,
        existing_order=params.existing_order,
        parsed_info=params.parsed_info,
        title=params.title,
        order_id=params.order_id,
        chat_id=params.chat_id,
        manual_trigger=params.manual_trigger,
    )
    handled = await _handle_existing_order_logic(logic_params)
    return handled


async def _handle_new_order_creation(params: "NewOrderCreationParams") -> None:
    """处理新订单创建

    Args:
        params: 新订单创建参数
    """
    from utils.order_handling_data import NewOrderCreationParams

    if not params.allow_create_new:
        if params.manual_trigger:
            await params.update.message.reply_text(
                f"❌ 订单 {params.order_id} 不存在，无法关联。\n"
                f"请使用 /create 命令创建新订单。"
            )
        return

    await _create_new_order_internal(
        params.update, params.context, params.chat_id, params.parsed_info, params.title
    )


async def try_create_order_from_title(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    chat,
    title: str,
    manual_trigger: bool = False,
    allow_create_new: bool = True,
):
    """尝试从群标题创建订单（通用逻辑）

    Args:
        update: Telegram 更新对象
        context: 上下文对象
        chat: 聊天对象
        title: 群名
        manual_trigger: 是否手动触发
        allow_create_new: 是否允许创建新订单（False 时只关联，不创建）
    """
    chat_id = chat.id

    logger.info(
        f"Attempting to create order from title: '{title}' "
        f"(chat_id: {chat_id}, manual_trigger: {manual_trigger})"
    )

    parsed_info = await _parse_and_validate_title(update, title, manual_trigger)
    if not parsed_info:
        return

    order_id = parsed_info["order_id"]
    existing_order, handled = await _find_existing_order_by_id(
        update, order_id, chat_id, title, manual_trigger
    )
    if handled:
        return

    if existing_order:
        from utils.order_handling_data import ExistingOrderFlowParams

        flow_params = ExistingOrderFlowParams(
            update=update,
            context=context,
            existing_order=existing_order,
            parsed_info=parsed_info,
            title=title,
            order_id=order_id,
            chat_id=chat_id,
            manual_trigger=manual_trigger,
        )
        handled = await _handle_existing_order_flow(flow_params)
        if handled:
            return

    from utils.order_handling_data import NewOrderCreationParams

    creation_params = NewOrderCreationParams(
        update=update,
        context=context,
        chat_id=chat_id,
        parsed_info=parsed_info,
        title=title,
        order_id=order_id,
        allow_create_new=allow_create_new,
        manual_trigger=manual_trigger,
    )
    await _handle_new_order_creation(creation_params)
