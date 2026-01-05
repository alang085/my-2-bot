"""播报功能处理器"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

import db_operations
from decorators import authorized_required, error_handler, group_chat_only
from utils.broadcast_helpers import (calculate_next_payment_date,
                                     format_broadcast_message)
from utils.handler_helpers import get_and_validate_order, get_chat_info

logger = logging.getLogger(__name__)


@error_handler
@authorized_required
@group_chat_only
async def broadcast_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """播报付款提醒命令（群聊）- 直接发送模板消息"""
    # 检查是否有订单
    chat_id, _ = get_chat_info(update)
    if not chat_id:
        return

    # 获取订单（不需要验证状态）
    order_model, _, _, error_msg = await get_and_validate_order(chat_id)
    if error_msg:
        await update.message.reply_text("❌ No active order in this group")
        return

    order = await db_operations.get_order_by_chat_id(
        chat_id
    )  # 保留原始字典用于后续使用

    # 从订单获取本金
    principal = order.get("amount", 0)
    from constants import PRINCIPAL_PERCENTAGE

    principal_12 = principal * PRINCIPAL_PERCENTAGE

    # 获取未付利息（默认为0）
    outstanding_interest = 0

    # 从订单获取日期，计算下个周期（周四）
    order_date_str = order.get("date", "")
    # 使用统一的播报模板函数，基于订单日期计算下个周期
    _, date_str, weekday_str = calculate_next_payment_date(order_date_str)
    message = format_broadcast_message(
        principal=principal,
        principal_12=principal_12,
        outstanding_interest=outstanding_interest,
        date_str=date_str,
        weekday_str=weekday_str,
    )

    try:
        await context.bot.send_message(chat_id=chat_id, text=message)
        # 不发送任何回复，静默完成
    except Exception as e:
        logger.error(f"发送播报消息失败: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Send failed: {e}")


async def _handle_cancel_broadcast(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> bool:
    """处理取消播报

    Returns:
        是否已取消
    """
    context.user_data["state"] = None
    context.user_data["broadcast_step"] = None
    context.user_data["broadcast_data"] = {}
    await update.message.reply_text("✅ Operation cancelled")
    return True


async def _handle_principal_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, data: dict
) -> bool:
    """处理本金输入

    Returns:
        是否成功
    """
    try:
        principal = float(text)
        if principal <= 0:
            await update.message.reply_text("❌ Principal must be greater than 0")
            return False

        data["principal"] = principal
        context.user_data["broadcast_data"] = data
        context.user_data["broadcast_step"] = 2
        await update.message.reply_text(
            f"✅ Principal set: {principal:.2f}\n\n"
            "Enter 12% of principal (or 'auto' for auto calculation):"
        )
        return True
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number")
        return False


async def _handle_principal_12_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, data: dict
) -> bool:
    """处理本金12%输入

    Returns:
        是否成功
    """
    try:
        if text.lower() == "auto":
            principal = data.get("principal", 0)
            from constants import PRINCIPAL_PERCENTAGE

            principal_12 = principal * PRINCIPAL_PERCENTAGE
        else:
            principal_12 = float(text)
            if principal_12 <= 0:
                await update.message.reply_text("❌ Amount must be greater than 0")
                return False

        data["principal_12"] = principal_12
        context.user_data["broadcast_data"] = data
        context.user_data["broadcast_step"] = 3
        await update.message.reply_text(
            f"✅ 12% of principal set: {principal_12:.2f}\n\n"
            "Enter outstanding interest (employee input):"
        )
        return True
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number or 'auto'")
        return False


async def _handle_interest_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, data: dict
) -> bool:
    """处理未付利息输入

    Returns:
        是否成功
    """
    try:
        outstanding_interest = float(text)
        if outstanding_interest < 0:
            await update.message.reply_text("❌ Interest cannot be negative")
            return False

        data["outstanding_interest"] = outstanding_interest
        await send_broadcast_message(update, context, data)

        context.user_data["state"] = None
        context.user_data["broadcast_step"] = None
        context.user_data["broadcast_data"] = {}
        return True
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number")
        return False


async def handle_broadcast_payment_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str
):
    """处理播报输入"""
    if text.lower() == "cancel":
        await _handle_cancel_broadcast(update, context)
        return

    step = context.user_data.get("broadcast_step", 1)
    data = context.user_data.get("broadcast_data", {})

    if step == 1:
        await _handle_principal_input(update, context, text, data)
    elif step == 2:
        await _handle_principal_12_input(update, context, text, data)
    elif step == 3:
        await _handle_interest_input(update, context, text, data)


async def send_broadcast_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE, data: dict
):
    """发送播报消息"""
    principal = data.get("principal", 0)
    principal_12 = data.get("principal_12", 0)
    outstanding_interest = data.get("outstanding_interest", 0)

    # 使用统一的播报模板函数
    _, date_str, weekday_str = calculate_next_payment_date()
    message = format_broadcast_message(
        principal=principal,
        principal_12=principal_12,
        outstanding_interest=outstanding_interest,
        date_str=date_str,
        weekday_str=weekday_str,
    )

    # 发送消息到当前群组
    try:
        await context.bot.send_message(chat_id=update.message.chat_id, text=message)

        # 保存数据到context，用于后续发送
        context.user_data["broadcast_principal_12"] = principal_12
        context.user_data["broadcast_outstanding_interest"] = outstanding_interest
        context.user_data["broadcast_date_str"] = date_str
        context.user_data["broadcast_weekday_str"] = weekday_str

        # 询问是否发送本金12%版本
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        keyboard = [
            [
                InlineKeyboardButton(
                    f"Send 12% version ({principal_12:.2f})",
                    callback_data="broadcast_send_12",
                )
            ],
            [InlineKeyboardButton("Done", callback_data="broadcast_done")],
        ]
        await update.message.reply_text(
            f"✅ Principal version sent\n\n" f"Send 12% version ({principal_12:.2f})?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    except Exception as e:
        logger.error(f"发送播报消息失败: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Send failed: {e}")
