"""金额操作处理器"""

import sys
from pathlib import Path

# 确保项目根目录在 Python 路径中
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import logging
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

import db_operations
from decorators import error_handler
from handlers.module5_data.undo_handlers import reset_undo_count
from services.module3_order.amount_service import AmountService
from utils.chat_helpers import is_group_chat
# get_daily_period_date 未使用，已移除
from utils.error_messages import ErrorMessages
from utils.handler_helpers import HandlerContext, send_success_message
from utils.models import validate_amount

logger = logging.getLogger(__name__)


async def _validate_amount_operation_permission(
    update: Update,
) -> tuple[bool, Optional[int], Optional[int], Optional[str]]:
    """验证金额操作的权限和基本条件

    Returns:
        (is_valid, user_id, chat_id, text)
    """
    if not is_group_chat(update):
        return False, None, None, None

    if not update.message or not update.message.text:
        return False, None, None, None

    from utils.handler_helpers import check_user_permissions, get_user_id

    user_id = get_user_id(update)
    if not user_id:
        return False, None, None, None

    is_admin, is_authorized, _ = await check_user_permissions(user_id)
    if not is_admin and not is_authorized:
        logger.debug(f"用户 {user_id} 无权限执行快捷操作")
        return False, None, None, None

    chat_id = update.message.chat_id
    text = update.message.text.strip()

    if not text.startswith("+"):
        return False, None, None, None

    logger.info(f"收到快捷操作消息: {text} (用户: {user_id}, 群组: {chat_id})")
    return True, user_id, chat_id, text


async def _parse_amount_text(amount_text: str) -> tuple[Optional[float], bool]:
    """解析金额文本

    Returns:
        (amount, is_principal_reduction)
    """
    if not amount_text:
        return None, False

    is_principal_reduction = amount_text.endswith("b")
    if is_principal_reduction:
        amount_text = amount_text[:-1]

    try:
        amount = validate_amount(float(amount_text))
        return amount, is_principal_reduction
    except ValueError:
        return None, is_principal_reduction


async def _handle_principal_reduction(
    update: Update,
    order: dict,
    amount: float,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
) -> None:
    """处理本金减少操作"""
    if not order:
        from utils.error_messages import ErrorMessages

        await update.message.reply_text(ErrorMessages.no_active_order())
        return

    try:
        await process_principal_reduction(update, order, amount, context, user_id)
    except ValueError as e:
        from utils.error_messages import ErrorMessages

        await update.message.reply_text(ErrorMessages.validation_error("金额", str(e)))


async def _handle_interest_income(
    update: Update,
    order: Optional[dict],
    amount: float,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
) -> None:
    """处理利息收入操作"""
    try:
        if order:
            await process_interest(update, order, amount, context, user_id)
        else:
            await process_interest_without_order(update, amount, context, user_id)
    except ValueError:
        from utils.error_messages import ErrorMessages

        await update.message.reply_text(ErrorMessages.invalid_amount_format())


@error_handler
async def handle_amount_operation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理金额操作（需要管理员权限）"""
    is_valid, user_id, chat_id, text = await _validate_amount_operation_permission(
        update
    )
    if not is_valid:
        return

    order = await db_operations.get_order_by_chat_id(chat_id)
    amount_text = text[1:].strip()

    if not amount_text:
        from utils.error_messages import ErrorMessages

        await update.message.reply_text(ErrorMessages.invalid_amount_format())
        return

    amount, is_principal_reduction = await _parse_amount_text(amount_text)
    if amount is None:
        message = "❌ Failed: Invalid format. Example: +1000 or +1000b"
        await update.message.reply_text(message)
        return

    try:
        if is_principal_reduction:
            await _handle_principal_reduction(update, order, amount, context, user_id)
        else:
            await _handle_interest_income(update, order, amount, context, user_id)
    except Exception as e:
        logger.error(f"处理金额操作时出错: {e}", exc_info=True)
        await update.message.reply_text("❌ Failed: An error occurred.")


async def process_principal_reduction(
    update: Update,
    order: dict,
    amount: float,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
):
    """处理本金减少（使用 AmountService）"""
    ctx = HandlerContext(update, context)

    # 调用服务层处理业务逻辑
    success, error_msg, operation_data = (
        await AmountService.process_principal_reduction(order, amount, user_id)
    )

    if not success:
        await ctx.send_error(error_msg or "❌ Failed to process principal reduction")
        return

    # 记录操作历史（用于撤销）
    current_chat_id = update.effective_chat.id if update.effective_chat else None
    if current_chat_id and user_id and operation_data:
        try:
            await db_operations.record_operation(
                user_id=user_id,
                operation_type="principal_reduction",
                operation_data=operation_data,
                chat_id=current_chat_id,
            )
        except Exception as e:
            logger.warning(f"记录操作历史失败（不影响主流程）: {e}", exc_info=True)

    # 重置撤销计数
    reset_undo_count(context, user_id)

    # 发送成功消息
    if operation_data:
        new_amount = operation_data.get("new_amount", 0)
        amount_validated = operation_data.get("amount", 0)
        order_id = operation_data.get("order_id", "N/A")

        message = send_success_message(
            update,
            f"✅ Principal Reduced: {amount_validated:.2f}\nRemaining: {new_amount:.2f}",
            f"✅ Principal Reduced Successfully!\n"
            f"Order ID: {order_id}\n"
            f"Reduced Amount: {amount_validated:.2f}\n"
            f"Remaining Amount: {new_amount:.2f}",
        )
        await ctx.send_message(message)


async def process_interest(
    update: Update,
    order: dict,
    amount: float,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
):
    """处理利息收入（使用 AmountService）"""
    ctx = HandlerContext(update, context)

    # 调用服务层处理业务逻辑
    success, error_msg, operation_data = await AmountService.process_interest(
        order, amount, user_id
    )

    if not success:
        await ctx.send_error(error_msg or "❌ Failed to process interest")
        return

    # 记录操作历史（用于撤销）
    current_chat_id = update.effective_chat.id if update.effective_chat else None
    if current_chat_id and user_id and operation_data:
        try:
            await db_operations.record_operation(
                user_id=user_id,
                operation_type="interest",
                operation_data=operation_data,
                chat_id=current_chat_id,
            )
        except Exception as e:
            logger.warning(f"记录操作历史失败（不影响主流程）: {e}", exc_info=True)

    # 重置撤销计数
    reset_undo_count(context, user_id)

    # 发送成功消息
    if ctx.is_group:
        await ctx.send_message("✅ Interest Received")
    else:
        financial_data = await db_operations.get_financial_data()
        amount_validated = (
            operation_data.get("amount", amount) if operation_data else amount
        )
        await ctx.send_message(
            f"✅ Interest Recorded!\n"
            f"Amount: {amount_validated:.2f}\n"
            f"Total Interest: {financial_data['interest']:.2f}"
        )


async def process_interest_without_order(
    update: Update,
    amount: float,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
):
    """处理无关联订单的利息收入（使用 AmountService）"""
    ctx = HandlerContext(update, context)

    # 调用服务层处理业务逻辑
    success, error_msg, operation_data = (
        await AmountService.process_interest_without_order(amount, user_id)
    )

    if not success:
        await ctx.send_error(error_msg or "❌ Failed to process interest")
        return

    # 记录操作历史（用于撤销）
    current_chat_id = update.effective_chat.id if update.effective_chat else None
    if current_chat_id and user_id and operation_data:
        try:
            await db_operations.record_operation(
                user_id=user_id,
                operation_type="interest",
                operation_data=operation_data,
                chat_id=current_chat_id,
            )
        except Exception as e:
            logger.warning(f"记录操作历史失败（不影响主流程）: {e}", exc_info=True)

    # 重置撤销计数
    reset_undo_count(context, user_id)

    # 发送成功消息
    if ctx.is_group:
        await ctx.send_message("✅ Success")
    else:
        financial_data = await db_operations.get_financial_data()
        amount_validated = (
            operation_data.get("amount", amount) if operation_data else amount
        )
        await ctx.send_message(
            f"✅ Interest Recorded!\n"
            f"Amount: {amount_validated:.2f}\n"
            f"Total Interest: {financial_data['interest']:.2f}"
        )
