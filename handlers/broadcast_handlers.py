"""播报功能处理器"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

import db_operations
from decorators import authorized_required, group_chat_only
from utils.broadcast_helpers import calculate_next_payment_date, format_broadcast_message
from utils.chat_helpers import is_group_chat

logger = logging.getLogger(__name__)


@authorized_required
@group_chat_only
async def broadcast_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """播报付款提醒命令（群聊）- 直接发送模板消息"""
    # 检查是否有订单
    chat_id = update.message.chat_id
    order = await db_operations.get_order_by_chat_id(chat_id)

    if not order:
        await update.message.reply_text("❌ No active order in this group")
        return

    # 从订单获取本金
    principal = order.get("amount", 0)
    principal_12 = principal * 0.12

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


async def handle_broadcast_payment_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str
):
    """处理播报输入"""
    # 检查取消
    if text.lower() == "cancel":
        context.user_data["state"] = None
        context.user_data["broadcast_step"] = None
        context.user_data["broadcast_data"] = {}
        await update.message.reply_text("✅ Operation cancelled")
        return

    step = context.user_data.get("broadcast_step", 1)
    data = context.user_data.get("broadcast_data", {})

    if step == 1:
        # 输入本金
        try:
            principal = float(text)
            if principal <= 0:
                await update.message.reply_text("❌ Principal must be greater than 0")
                return
            data["principal"] = principal
            context.user_data["broadcast_data"] = data
            context.user_data["broadcast_step"] = 2
            await update.message.reply_text(
                f"✅ Principal set: {principal:.2f}\n\n"
                "Enter 12% of principal (or 'auto' for auto calculation):"
            )
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid number")

    elif step == 2:
        # 输入本金12%
        try:
            if text.lower() == "auto":
                principal = data.get("principal", 0)
                principal_12 = principal * 0.12
            else:
                principal_12 = float(text)
                if principal_12 <= 0:
                    await update.message.reply_text("❌ Amount must be greater than 0")
                    return
            data["principal_12"] = principal_12
            context.user_data["broadcast_data"] = data
            context.user_data["broadcast_step"] = 3
            await update.message.reply_text(
                f"✅ 12% of principal set: {principal_12:.2f}\n\n"
                "Enter outstanding interest (employee input):"
            )
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid number or 'auto'")

    elif step == 3:
        # 输入未付利息
        try:
            outstanding_interest = float(text)
            if outstanding_interest < 0:
                await update.message.reply_text("❌ Interest cannot be negative")
                return
            data["outstanding_interest"] = outstanding_interest

            # 生成并发送播报消息
            await send_broadcast_message(update, context, data)

            # 清除状态
            context.user_data["state"] = None
            context.user_data["broadcast_step"] = None
            context.user_data["broadcast_data"] = {}
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid number")


async def send_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE, data: dict):
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
                    f"Send 12% version ({principal_12:.2f})", callback_data="broadcast_send_12"
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
