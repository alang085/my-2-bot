"""支付账户余额更新辅助函数"""

# 标准库
import logging
from typing import Optional, Tuple

# 第三方库
from telegram import Update
from telegram.ext import ContextTypes

# 本地模块
import db_operations

logger = logging.getLogger(__name__)


async def _validate_account_for_balance_update(
    update: Update, context: ContextTypes.DEFAULT_TYPE, account_type: str
) -> tuple[bool, Optional[float]]:
    """验证账户是否存在并获取旧余额

    Returns:
        (is_valid, old_balance)
    """
    from services.module2_finance.payment_service import PaymentService

    accounts = await PaymentService.get_accounts_by_type(account_type)
    if not accounts:
        await update.message.reply_text(
            f"❌ 未找到{account_type.upper()}账户，请先添加账户"
        )
        context.user_data["state"] = None
        return False, None

    old_balance = accounts[0].get("balance", 0) if accounts else 0
    return True, old_balance


async def _record_balance_update_operation(
    update: Update, account_type: str, old_balance: float, new_balance: float
) -> None:
    """记录余额更新操作历史"""
    user_id = update.effective_user.id if update.effective_user else None
    current_chat_id = update.effective_chat.id if update.effective_chat else None
    if current_chat_id and user_id:
        await db_operations.record_operation(
            user_id=user_id,
            operation_type="payment_account_balance_updated",
            operation_data={
                "account_type": account_type,
                "old_balance": old_balance,
                "new_balance": new_balance,
            },
            chat_id=current_chat_id,
        )


async def _verify_and_display_balance_update(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    account_type: str,
    new_balance: float,
) -> None:
    """验证更新结果并显示账户信息"""
    from services.module2_finance.payment_service import PaymentService

    account_name = "GCASH" if account_type == "gcash" else "PayMaya"
    accounts = await PaymentService.get_accounts_by_type(account_type)
    updated_account = accounts[0] if accounts else None

    if updated_account and abs(updated_account.get("balance", 0) - new_balance) < 0.01:
        await update.message.reply_text(
            f"✅ {account_name}余额已更新为: {new_balance:,.2f}"
        )

        if account_type == "gcash":
            from handlers.module2_finance.payment_handlers import show_gcash

            await show_gcash(update, context)
        else:
            from handlers.module2_finance.payment_handlers import show_paymaya

            await show_paymaya(update, context)
    else:
        actual_balance = updated_account.get("balance", 0) if updated_account else 0
        await update.message.reply_text(
            f"⚠️ 更新可能未生效\n"
            f"期望值: {new_balance:,.2f}\n"
            f"实际值: {actual_balance:,.2f}\n"
            f"请重试或检查数据库"
        )


async def _handle_update_balance(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, account_type: str
):
    """处理更新余额输入"""
    try:
        new_balance = float(text)

        is_valid, old_balance = await _validate_account_for_balance_update(
            update, context, account_type
        )
        if not is_valid:
            return

        from services.module2_finance.payment_service import PaymentService

        success, error_msg = await PaymentService.update_account(
            account_type, balance=new_balance
        )

        if success:
            await _record_balance_update_operation(
                update, account_type, old_balance, new_balance
            )
            await _verify_and_display_balance_update(
                update, context, account_type, new_balance
            )
        else:
            await update.message.reply_text(
                error_msg
                or "❌ 更新失败\n"
                "请检查：\n"
                "1. 账户是否存在\n"
                "2. 数据库连接是否正常\n"
                "3. 是否有权限"
            )

        context.user_data["state"] = None
    except ValueError:
        await update.message.reply_text("❌ 请输入有效的数字")
    except Exception as e:
        logger.error(f"更新余额时出错: {e}", exc_info=True)
        await update.message.reply_text(f"❌ 更新时发生错误: {e}")


async def _validate_and_get_account_for_balance_update(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str
) -> tuple[bool, Optional[dict], Optional[int], Optional[float], Optional[str]]:
    """验证请求并获取账户信息

    Returns:
        (is_valid, account, account_id, new_balance, error_msg)
    """
    from handlers.module4_automation.payment_balance_validate import \
        validate_balance_update_request

    is_valid, error_msg, account_id, new_balance = validate_balance_update_request(
        update, context, text
    )
    if not is_valid:
        return False, None, None, None, error_msg

    from services.module2_finance.payment_service import PaymentService

    account = await PaymentService.get_account_by_id(account_id)
    if not account:
        return False, None, None, None, "❌ 账户不存在"

    return True, account, account_id, new_balance, None


def _clear_balance_update_state(context: ContextTypes.DEFAULT_TYPE) -> None:
    """清除余额更新状态"""
    context.user_data["state"] = None
    context.user_data.pop("updating_balance_account_id", None)


async def _process_balance_update(
    update: Update,
    account_id: int,
    account_type: str,
    old_balance: float,
    new_balance: float,
) -> Tuple[bool, Optional[str]]:
    """处理余额更新操作

    Args:
        update: Telegram更新对象
        account_id: 账户ID
        account_type: 账户类型
        old_balance: 旧余额
        new_balance: 新余额

    Returns:
        (是否成功, 错误消息)
    """
    from handlers.module4_automation.payment_balance_update import (
        record_balance_update_operation, update_account_balance)

    success, error_msg, updated_account = await update_account_balance(
        account_id, new_balance
    )

    if success:
        await record_balance_update_operation(
            update, account_id, account_type, old_balance, new_balance
        )

    return success, error_msg


async def _handle_update_balance_by_id(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str
):
    """处理按ID更新余额输入"""
    from handlers.module4_automation.payment_balance_send import \
        send_balance_update_result

    try:
        is_valid, account, account_id, new_balance, error_msg = (
            await _validate_and_get_account_for_balance_update(update, context, text)
        )
        if not is_valid:
            await update.message.reply_text(error_msg)
            _clear_balance_update_state(context)
            return

        account_type = account.get("account_type", "")
        account_name = account.get("account_name", "未设置")
        account_number = account.get("account_number", "未设置")
        old_balance = account.get("balance", 0)

        success, error_msg = await _process_balance_update(
            update, account_id, account_type, old_balance, new_balance
        )

        from handlers.module4_automation.payment_balance_data import \
            BalanceUpdateResultParams

        result_params = BalanceUpdateResultParams(
            update=update,
            context=context,
            success=success,
            account_type=account_type,
            account_name=account_name,
            account_number=account_number,
            new_balance=new_balance,
            error_msg=error_msg,
        )
        await send_balance_update_result(result_params)

        _clear_balance_update_state(context)

    except ValueError:
        await update.message.reply_text("❌ 请输入有效的金额")
        _clear_balance_update_state(context)
    except Exception as e:
        logger.error(f"按ID更新余额时出错: {e}", exc_info=True)
        await update.message.reply_text(f"❌ 更新时发生错误: {e}")
        _clear_balance_update_state(context)
