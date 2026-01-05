"""支付余额更新 - 更新模块

包含更新账户余额的逻辑。
"""

from telegram import Update
from telegram.ext import ContextTypes

import db_operations
from services.module2_finance.payment_service import PaymentService


async def update_account_balance(
    account_id: int, new_balance: float
) -> tuple[bool, str, dict | None]:
    """更新账户余额

    Args:
        account_id: 账户ID
        new_balance: 新余额

    Returns:
        Tuple: (是否成功, 错误消息, 账户信息)
    """
    # 获取账户信息
    account = await PaymentService.get_account_by_id(account_id)
    if not account:
        return False, "❌ 账户不存在", None

    # 更新余额
    success, error_msg = await PaymentService.update_account_by_id(
        account_id, balance=new_balance
    )

    if not success:
        return False, error_msg or "❌ 更新失败", None

    # 验证更新是否成功
    updated_account = await PaymentService.get_account_by_id(account_id)
    if updated_account and abs(updated_account.get("balance", 0) - new_balance) < 0.01:
        return True, None, updated_account
    else:
        actual_balance = updated_account.get("balance", 0) if updated_account else 0
        return (
            False,
            f"⚠️ 更新可能未生效\n期望值: {new_balance:,.2f}\n实际值: {actual_balance:,.2f}\n请重试或检查数据库",
            updated_account,
        )


async def record_balance_update_operation(
    update: Update,
    account_id: int,
    account_type: str,
    old_balance: float,
    new_balance: float,
) -> None:
    """记录余额更新操作历史

    Args:
        update: Telegram更新对象
        account_id: 账户ID
        account_type: 账户类型
        old_balance: 旧余额
        new_balance: 新余额
    """
    user_id = update.effective_user.id if update.effective_user else None
    current_chat_id = update.effective_chat.id if update.effective_chat else None
    if current_chat_id and user_id:
        await db_operations.record_operation(
            user_id=user_id,
            operation_type="payment_account_balance_updated",
            operation_data={
                "account_id": account_id,
                "account_type": account_type,
                "old_balance": old_balance,
                "new_balance": new_balance,
            },
            chat_id=current_chat_id,
        )
