"""订单相关文本输入辅助函数"""

# 标准库
import logging
from typing import Optional

# 第三方库
from telegram import Update
from telegram.ext import ContextTypes

# 本地模块
import db_operations
from utils.error_messages import ErrorMessages

logger = logging.getLogger(__name__)


async def _validate_breach_end_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str
) -> tuple[bool, Optional[float], Optional[int], Optional[int]]:
    """验证违约完成输入

    Returns:
        (is_valid, amount_validated, chat_id, user_id)
    """
    try:
        amount = float(text)
        if amount <= 0:
            await update.message.reply_text("❌ Amount must be positive")
            return False, None, None, None

        chat_id = context.user_data.get("breach_end_chat_id")
        if not chat_id:
            await update.message.reply_text("❌ State Error. Please retry.")
            context.user_data["state"] = None
            return False, None, None, None

        order = await db_operations.get_order_by_chat_id(chat_id)
        if not order or order["state"] != "breach":
            await update.message.reply_text("❌ Order state changed or not found")
            context.user_data["state"] = None
            return False, None, None, None

        from utils.models import validate_amount

        user_id = update.effective_user.id if update.effective_user else None
        try:
            amount_validated = validate_amount(amount)
        except ValueError as e:
            await update.message.reply_text(f"❌ {str(e)}")
            context.user_data["state"] = None
            return False, None, None, None

        return True, amount_validated, chat_id, user_id
    except ValueError:
        await update.message.reply_text(ErrorMessages.invalid_amount_format())
        return False, None, None, None


async def _execute_breach_end_completion(
    chat_id: int, amount_validated: float, user_id: Optional[int]
) -> tuple[bool, Optional[str], Optional[dict]]:
    """执行违约完成操作

    Returns:
        (success, error_msg, operation_data)
    """
    from services.module3_order.order_service import OrderService

    return await OrderService.complete_breach_order(chat_id, amount_validated, user_id)


async def _send_breach_end_success_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    operation_data: dict,
    amount_validated: float,
) -> None:
    """发送违约完成成功消息"""
    order = await db_operations.get_order_by_chat_id(chat_id)
    if not order:
        await update.message.reply_text("❌ Order not found after completion.")
        return

    order_id = operation_data.get("order_id", order.get("order_id", ""))
    amount_display = operation_data.get("amount", amount_validated)
    msg_en = (
        f"✅ Breach Order Ended\nAmount: {amount_display:.2f}\n" f"Order ID: {order_id}"
    )

    prompt_msg_id = context.user_data.get("breach_end_prompt_msg_id")
    if prompt_msg_id:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=prompt_msg_id)
        except Exception as e:
            logger.debug(f"删除提示消息失败（可能已被删除）: {e}")
        context.user_data.pop("breach_end_prompt_msg_id", None)

    if update.effective_chat.id != chat_id:
        await context.bot.send_message(chat_id=chat_id, text=msg_en)
        await update.message.reply_text(msg_en)
    else:
        await update.message.reply_text(msg_en)


async def _handle_breach_end_amount(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str
):
    """处理违约完成金额输入"""
    is_valid, amount_validated, chat_id, user_id = await _validate_breach_end_input(
        update, context, text
    )
    if not is_valid:
        return

    success, error_msg, operation_data = await _execute_breach_end_completion(
        chat_id, amount_validated, user_id
    )
    if not success:
        await update.message.reply_text(f"❌ {error_msg}")
        context.user_data["state"] = None
        return

    if user_id:
        from handlers.module5_data.undo_handlers import reset_undo_count

        reset_undo_count(context, user_id)

    await _send_breach_end_success_message(
        update, context, chat_id, operation_data, amount_validated
    )
    context.user_data["state"] = None
