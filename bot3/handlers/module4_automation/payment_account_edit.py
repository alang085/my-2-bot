"""支付账户编辑辅助函数"""

# 标准库
import logging
from typing import Optional, Tuple

# 第三方库
from telegram import Update
from telegram.ext import ContextTypes

# 本地模块
import db_operations
from utils.error_messages import ErrorMessages

logger = logging.getLogger(__name__)


def _parse_account_edit_input(text: str) -> Tuple[Optional[str], Optional[str]]:
    """解析账户编辑输入

    Args:
        text: 输入文本

    Returns:
        (账号号码, 账户名称) 或 (None, None)
    """
    parts = text.strip().split(maxsplit=1)
    if len(parts) < 2:
        return None, None
    return parts[0], parts[1]


async def _record_account_update_operation(
    update: Update, account_type: str, account_number: str, account_name: str
) -> None:
    """记录账户更新操作历史

    Args:
        update: Telegram更新对象
        account_type: 账户类型
        account_number: 账号号码
        account_name: 账户名称
    """
    user_id = update.effective_user.id if update.effective_user else None
    current_chat_id = update.effective_chat.id if update.effective_chat else None
    if current_chat_id and user_id:
        await db_operations.record_operation(
            user_id=user_id,
            operation_type="payment_account_updated",
            operation_data={
                "account_type": account_type,
                "account_number": account_number,
                "account_name": account_name,
            },
            chat_id=current_chat_id,
        )


async def _refresh_account_display(
    update: Update, context: ContextTypes.DEFAULT_TYPE, account_type: str
) -> None:
    """刷新账户显示

    Args:
        update: Telegram更新对象
        context: 上下文对象
        account_type: 账户类型
    """
    if account_type == "gcash":
        from handlers.module2_finance.payment_handlers import show_gcash

        await show_gcash(update, context)
    else:
        from handlers.module2_finance.payment_handlers import show_paymaya

        await show_paymaya(update, context)


async def _handle_edit_account(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, account_type: str
):
    """处理编辑账号输入（兼容旧代码）"""
    account_number, account_name = _parse_account_edit_input(text)

    if not account_number or not account_name:
        await update.message.reply_text(
            f"{ErrorMessages.validation_error('格式', '格式: <账号号码> <账户名称>')}\n示例: 09171234567 张三"
        )
        return

    success = await db_operations.update_payment_account(
        account_type, account_number=account_number, account_name=account_name
    )

    if success:
        await _record_account_update_operation(
            update, account_type, account_number, account_name
        )

        account_name_display = "GCASH" if account_type == "gcash" else "PayMaya"
        await update.message.reply_text(
            f"✅ {account_name_display}账号信息已更新\n\n"
            f"账号号码: {account_number}\n"
            f"账户名称: {account_name}"
        )
        await _refresh_account_display(update, context, account_type)
    else:
        await update.message.reply_text("❌ 更新失败")

    context.user_data["state"] = None


async def _handle_delete_account(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    account_id: int,
    account_type: str,
) -> None:
    """处理删除账户"""
    success = await db_operations.delete_payment_account(account_id)
    if success:
        account_name_display = "GCASH" if account_type == "gcash" else "PayMaya"
        await update.message.reply_text(f"✅ {account_name_display}账户已删除")
        if account_type == "gcash":
            from handlers.module2_finance.payment_handlers import show_gcash

            await show_gcash(update, context)
        else:
            from handlers.module2_finance.payment_handlers import show_paymaya

            await show_paymaya(update, context)
    else:
        await update.message.reply_text("❌ 删除失败")
    context.user_data["state"] = None
    context.user_data.pop("editing_account_id", None)


async def _parse_account_input(text: str) -> Optional[Tuple[str, str]]:
    """解析账户输入，返回(账号号码, 账户名称)或None"""
    parts = text.strip().split(maxsplit=1)
    if len(parts) < 2:
        return None
    return parts[0], parts[1]


async def _update_account_info(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    account_id: int,
    account_type: str,
    account_number: str,
    account_name: str,
) -> bool:
    """更新账户信息，返回是否成功"""
    from services.module2_finance.payment_service import PaymentService

    success, error_msg = await PaymentService.update_account_by_id(
        account_id, account_number=account_number, account_name=account_name
    )

    if success:
        user_id = update.effective_user.id if update.effective_user else None
        current_chat_id = update.effective_chat.id if update.effective_chat else None
        if current_chat_id and user_id:
            await db_operations.record_operation(
                user_id=user_id,
                operation_type="payment_account_updated",
                operation_data={
                    "account_id": account_id,
                    "account_type": account_type,
                    "account_number": account_number,
                    "account_name": account_name,
                },
                chat_id=current_chat_id,
            )

        account_name_display = "GCASH" if account_type == "gcash" else "PayMaya"
        await update.message.reply_text(
            f"✅ {account_name_display}账户信息已更新\n\n"
            f"账号号码: {account_number}\n"
            f"账户名称: {account_name}"
        )
        if account_type == "gcash":
            from handlers.module2_finance.payment_handlers import show_gcash

            await show_gcash(update, context)
        else:
            from handlers.module2_finance.payment_handlers import show_paymaya

            await show_paymaya(update, context)
    else:
        await update.message.reply_text(error_msg or "❌ 更新失败")

    return success


async def _handle_edit_account_by_id(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, account_type: str
):
    """处理编辑账户输入（按ID）"""
    account_id = context.user_data.get("editing_account_id")
    if not account_id:
        await update.message.reply_text("❌ 错误：找不到账户ID")
        context.user_data["state"] = None
        return

    if text.strip().lower() == "delete":
        await _handle_delete_account(update, context, account_id, account_type)
        return

    parsed = await _parse_account_input(text)
    if not parsed:
        await update.message.reply_text(
            "❌ 格式错误\n"
            "格式: <账号号码> <账户名称>\n"
            "示例: 09171234567 张三\n\n"
            "💡 提示：输入 'delete' 可以删除此账户"
        )
        return

    account_number, account_name = parsed
    success = await _update_account_info(
        update, context, account_id, account_type, account_number, account_name
    )

    if success:
        context.user_data["state"] = None
        context.user_data.pop("editing_account_id", None)
