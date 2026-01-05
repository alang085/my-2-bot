"""订单创建相关工具函数

包含从群名创建订单的功能。
"""

# 标准库
import logging
import re
from datetime import date
from typing import Any, Dict, Optional, Tuple

# 第三方库
from telegram import Update
from telegram.ext import ContextTypes

# 本地模块
import db_operations
from constants import HISTORICAL_THRESHOLD_DATE, ORDER_CREATE_CUTOFF_DATE
from utils.chat_helpers import get_weekday_group_from_date, is_group_chat
from utils.message_builders import build_order_creation_message
from utils.models import OrderCreateModel, validate_amount
from utils.order_broadcast import send_auto_broadcast
from utils.order_parsing import get_state_from_title, parse_order_from_title
from utils.order_state import (_handle_state_transition_stats,
                               _record_state_change_operation,
                               _validate_state_transition,
                               update_order_state_from_title)
from utils.stats_helpers import update_all_stats, update_liquid_capital

logger = logging.getLogger(__name__)


async def _send_digits_too_few_error(
    update: Update, title: str, digits: str, digits_count: int
) -> None:
    """发送数字位数不足的错误消息"""
    from utils.message_helpers import send_bilingual_message

    english_message = (
        f"❌ Invalid Group Title Format.\n\n"
        f"Detected {digits_count} digits, but system requires 10 or 11 digits.\n\n"
        f"Current title: {title}\n"
        f"Digits part: {digits}\n\n"
        f"Correct format:\n"
        f"1. 10 digits: YYMMDDNNKK\n"
        f"   - YYMMDD = Date (6 digits)\n"
        f"   - NN = Sequence (2 digits)\n"
        f"   - KK = Amount thousands (2 digits)\n"
        f"2. 11 digits: YYMMDDNNKKH\n"
        f"   - YYMMDD = Date (6 digits)\n"
        f"   - NN = Sequence (2 digits)\n"
        f"   - KK = Amount thousands (2 digits)\n"
        f"   - H = Amount hundreds (1 digit)\n\n"
        f"Example: 2310220105 or A2310220105"
    )

    chinese_message = (
        f"❌ 群名格式错误\n\n"
        f"检测到 {digits_count} 位数字，但系统要求 10 或 11 位数字。\n\n"
        f"当前群名: {title}\n"
        f"数字部分: {digits}\n\n"
        f"正确格式:\n"
        f"1. 10位数字: YYMMDDNNKK\n"
        f"   - YYMMDD = 日期（6位）\n"
        f"   - NN = 序号（2位）\n"
        f"   - KK = 金额千位（2位）\n"
        f"2. 11位数字: YYMMDDNNKKH\n"
        f"   - YYMMDD = 日期（6位）\n"
        f"   - NN = 序号（2位）\n"
        f"   - KK = 金额千位（2位）\n"
        f"   - H = 金额百位（1位）\n\n"
        f"示例: 2310220105 或 A2310220105"
    )

    await send_bilingual_message(update, english_message, chinese_message)


async def _send_digits_too_many_error(
    update: Update, title: str, digits: str, digits_count: int
) -> None:
    """发送数字位数过多的错误消息"""
    from utils.message_helpers import send_bilingual_message

    english_message = (
        f"❌ Invalid Group Title Format.\n\n"
        f"Detected {digits_count} digits, but system requires 10 or 11 digits.\n\n"
        f"Current title: {title}\n"
        f"Digits part: {digits}\n\n"
        f"Please check the format."
    )

    chinese_message = (
        f"❌ 群名格式错误\n\n"
        f"检测到 {digits_count} 位数字，但系统要求 10 或 11 位数字。\n\n"
        f"当前群名: {title}\n"
        f"数字部分: {digits}\n\n"
        f"请检查格式。"
    )

    await send_bilingual_message(update, english_message, chinese_message)


async def _send_general_format_error(update: Update, title: str) -> None:
    """发送一般格式错误消息"""
    from utils.message_helpers import send_bilingual_message

    english_message = (
        f"❌ Invalid Group Title Format.\n\n"
        f"Title must start with 10 or 11 consecutive digits, or A prefix.\n\n"
        f"Format:\n"
        f"- 10 digits: YYMMDDNNKK (Date+Seq+Amount thousands)\n"
        f"- 11 digits: YYMMDDNNKKH (Date+Seq+Amount thousands+hundreds)\n"
        f"- Title must start with 10 or 11 consecutive digits, or A\n\n"
        f"Current title: {title}"
    )

    chinese_message = (
        f"❌ 群名格式错误\n\n"
        f"群名必须以 10 或 11 位连续数字开头，或以 A 开头。\n\n"
        f"格式:\n"
        f"- 10位数字: YYMMDDNNKK (日期+序号+金额千位)\n"
        f"- 11位数字: YYMMDDNNKKH (日期+序号+金额千位+百位)\n\n"
        f"当前群名: {title}"
    )

    await send_bilingual_message(update, english_message, chinese_message)


async def _handle_parse_error(update: Update, title: str, manual_trigger: bool) -> None:
    """处理群名解析错误，发送错误消息

    Args:
        update: Telegram 更新对象
        title: 群名
        manual_trigger: 是否手动触发
    """
    if not manual_trigger:
        logger.info(
            f"Group title '{title}' does not match order pattern "
            f"(must start with 10 or 11 digits)."
        )
        return

    digits_match = re.search(r"A?(\d+)", title)
    if digits_match:
        digits = digits_match.group(1)
        digits_count = len(digits)
        if digits_count < 10:
            await _send_digits_too_few_error(update, title, digits, digits_count)
            return
        elif digits_count > 11:
            await _send_digits_too_many_error(update, title, digits, digits_count)
            return

    await _send_general_format_error(update, title)


async def _get_existing_chat_title(chat_id: int) -> Optional[str]:
    """获取现有群组的标题

    Args:
        chat_id: 群组ID

    Returns:
        群组标题，如果获取失败返回 None
    """
    try:
        from telegram import Bot

        from config import BOT_TOKEN

        bot = Bot(token=BOT_TOKEN)
        existing_chat = await bot.get_chat(chat_id)
        existing_title = existing_chat.title
        await bot.close()
        return existing_title
    except Exception as e:
        logger.warning(f"无法获取现有订单的群组标题 (chat_id: {chat_id}): {e}")
        return None


async def _associate_order_to_group(
    update: Update,
    order_id: str,
    existing_chat_id: int,
    new_chat_id: int,
    existing_state: str,
    manual_trigger: bool,
) -> Tuple[bool, Optional[Dict]]:
    """关联订单到新群组

    Args:
        update: Telegram 更新对象
        order_id: 订单ID
        existing_chat_id: 现有群组ID
        new_chat_id: 新群组ID
        existing_state: 现有订单状态
        manual_trigger: 是否手动触发

    Returns:
        Tuple[是否成功, 更新后的订单字典]
    """
    from utils.order_association_helpers import (
        _execute_order_association, _send_association_failure_message,
        _send_association_success_message)

    success, updated_order = await _execute_order_association(
        order_id, new_chat_id, existing_chat_id, existing_state
    )

    if success:
        await _send_association_success_message(update, order_id, manual_trigger)
        return True, updated_order
    else:
        await _send_association_failure_message(update, manual_trigger)
        return False, None


def _prepare_order_update_data(
    parsed_info: Dict[str, Any], title: str
) -> Dict[str, Any]:
    """准备订单更新数据

    Args:
        parsed_info: 解析后的订单信息
        title: 群名

    Returns:
        更新数据字典
    """
    initial_state = get_state_from_title(title)
    return {
        "order_id": parsed_info["order_id"],
        "date": parsed_info["date"],
        "customer": parsed_info["customer"],
        "amount": parsed_info["amount"],
        "state": initial_state,
    }


async def _handle_order_state_transition(
    update: Update,
    chat_id: int,
    existing_order: Dict[str, Any],
    old_state: str,
    new_state: str,
    amount: float,
) -> None:
    """处理订单状态转换

    Args:
        update: Telegram 更新对象
        chat_id: 群组ID
        existing_order: 现有订单字典
        old_state: 旧状态
        new_state: 新状态
        amount: 订单金额
    """
    order_id = existing_order.get("order_id")
    if not _validate_state_transition(old_state, new_state, order_id):
        return

    group_id = existing_order.get("group_id", "S01")
    await _handle_state_transition_stats(
        update, old_state, new_state, existing_order, group_id, amount
    )
    await _record_state_change_operation(
        update, chat_id, order_id, old_state, new_state, group_id, amount
    )


async def _send_order_update_response(update: Update, success: bool) -> None:
    """发送订单更新响应消息

    Args:
        update: Telegram 更新对象
        success: 是否成功
    """
    if success:
        message = "✅ Order updated" if is_group_chat(update) else "✅ 订单已更新"
    else:
        message = (
            "❌ Failed to update order" if is_group_chat(update) else "❌ 订单更新失败"
        )
    await update.message.reply_text(message)


async def _update_existing_order_from_parsed_info(
    update: Update,
    chat_id: int,
    existing_order: Dict[str, Any],
    parsed_info: Dict[str, Any],
    title: str,
) -> bool:
    """更新现有订单的信息

    Args:
        update: Telegram 更新对象
        chat_id: 群组ID
        existing_order: 现有订单字典
        parsed_info: 解析后的订单信息
        title: 群名

    Returns:
        是否成功更新
    """
    existing_state = existing_order.get("state")
    order_id = existing_order.get("order_id", "N/A")

    # 规则：完成或违约完成状态的订单不可更改数据
    if existing_state in ["end", "breach_end"]:
        logger.info(
            f"订单 {order_id} 已完成（状态: {existing_state}），"
            f"不可更改订单数据（chat_id: {chat_id}）"
        )
        from utils.message_helpers import send_error_message

        await send_error_message(
            update,
            f"❌ Cannot update order {order_id}: order is completed (state: {existing_state})",
            f"❌ 无法更新订单 {order_id}：订单已完成（状态: {existing_state}）",
        )
        return False

    update_data = _prepare_order_update_data(parsed_info, title)
    success = await db_operations.update_order_from_parsed_info(chat_id, update_data)

    if success:
        old_state = existing_order.get("state")
        new_state = update_data["state"]
        if old_state != new_state:
            await _handle_order_state_transition(
                update,
                chat_id,
                existing_order,
                old_state,
                new_state,
                parsed_info["amount"],
            )

    await _send_order_update_response(update, success)
    return success


def _prepare_order_creation_data(
    parsed_info: Dict[str, Any], title: str, order_date: Any
) -> Tuple[str, str, float, str, str, str, str]:
    """准备订单创建数据

    Args:
        parsed_info: 解析后的订单信息
        title: 群名
        order_date: 订单日期

    Returns:
        (订单ID, 客户类型, 金额, 初始状态, 归属ID, 星期分组, 创建时间)
    """
    from utils.order_creation_prepare import prepare_order_data

    return prepare_order_data(parsed_info, title, order_date)


async def _validate_order_creation(
    update: Update, order_date: Any, amount: float
) -> Tuple[bool, bool]:
    """验证订单创建

    Args:
        update: Telegram 更新对象
        order_date: 订单日期
        amount: 订单金额

    Returns:
        (是否历史订单, 余额是否有效)
    """
    from utils.order_creation_validation import (check_historical_order,
                                                 validate_balance_for_order)

    is_historical = check_historical_order(order_date)
    balance_valid, _ = await validate_balance_for_order(update, amount, is_historical)
    return is_historical, balance_valid


async def _create_new_order_internal(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    parsed_info: Dict[str, Any],
    title: str,
) -> bool:
    """创建新订单的内部逻辑

    Args:
        update: Telegram 更新对象
        context: 上下文对象
        chat_id: 群组ID
        parsed_info: 解析后的订单信息
        title: 群名

    Returns:
        是否成功创建
    """
    from utils.order_creation_data import OrderCreationParams
    from utils.order_creation_execute import execute_order_creation_flow

    order_date = parsed_info["date"]
    order_id, customer, amount, initial_state, group_id, weekday_group, created_at = (
        _prepare_order_creation_data(parsed_info, title, order_date)
    )

    is_historical, balance_valid = await _validate_order_creation(
        update, order_date, amount
    )
    if not balance_valid:
        return False

    from utils.order_creation_data import OrderCreationParams

    params = OrderCreationParams(
        update=update,
        context=context,
        parsed_info=parsed_info,
        chat_id=chat_id,
        order_id=order_id,
        customer=customer,
        amount=amount,
        initial_state=initial_state,
        group_id=group_id,
        weekday_group=weekday_group,
        created_at=created_at,
        is_historical=is_historical,
        order_date=order_date,
    )
    return await execute_order_creation_flow(params)
