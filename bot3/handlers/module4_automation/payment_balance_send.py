"""支付余额更新 - 发送模块

包含发送更新结果消息的逻辑。
"""

from typing import Tuple

from telegram import Update
from telegram.ext import ContextTypes

from handlers.module4_automation.payment_balance_data import \
    BalanceUpdateResultParams


def _format_account_display_info(
    account_type: str, account_name: str, account_number: str
) -> Tuple[str, str]:
    """格式化账户显示信息

    Args:
        account_type: 账户类型
        account_name: 账户名称
        account_number: 账号

    Returns:
        (类型名称, 显示名称)
    """
    type_name = "GCASH" if account_type == "gcash" else "PayMaya"
    display_name = (
        account_name if account_name and account_name != "未设置" else account_number
    )
    return type_name, display_name


async def _send_success_balance_update(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    account_type: str,
    type_name: str,
    display_name: str,
    account_number: str,
    new_balance: float,
) -> None:
    """发送成功余额更新消息

    Args:
        update: Telegram更新对象
        context: 上下文对象
        account_type: 账户类型
        type_name: 类型名称
        display_name: 显示名称
        account_number: 账号
        new_balance: 新余额
    """
    await update.message.reply_text(
        f"✅ {type_name}账户余额已更新\n\n"
        f"账户: {display_name}\n"
        f"账号: {account_number}\n"
        f"新余额: {new_balance:,.2f}"
    )

    if account_type == "gcash":
        from handlers.module2_finance.payment_handlers import show_gcash

        await show_gcash(update, context)
    else:
        from handlers.module2_finance.payment_handlers import show_paymaya

        await show_paymaya(update, context)


async def _send_failed_balance_update(update: Update, error_msg: str) -> None:
    """发送失败余额更新消息

    Args:
        update: Telegram更新对象
        error_msg: 错误消息
    """
    if error_msg:
        await update.message.reply_text(error_msg)
    else:
        await update.message.reply_text(
            "❌ 更新失败\n"
            "请检查：\n"
            "1. 账户是否存在\n"
            "2. 数据库连接是否正常\n"
            "3. 是否有权限"
        )


async def send_balance_update_result(params: BalanceUpdateResultParams) -> None:
    """发送余额更新结果

    Args:
        params: 余额更新结果参数
    """
    if params.success:
        type_name, display_name = _format_account_display_info(
            params.account_type, params.account_name, params.account_number
        )
        await _send_success_balance_update(
            params.update,
            params.context,
            params.account_type,
            type_name,
            display_name,
            params.account_number,
            params.new_balance,
        )
    else:
        await _send_failed_balance_update(params.update, params.error_msg)
