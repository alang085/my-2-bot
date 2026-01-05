"""支付回调 - 账户查看处理模块

包含处理账户查看相关回调的逻辑。
"""

from telegram import CallbackQuery, Update
from telegram.ext import ContextTypes

# 这些函数在 payment_callbacks_account_view.py 中定义
# 导入将在运行时动态处理


async def handle_payment_view_callbacks(
    data: str, update: Update, context: ContextTypes.DEFAULT_TYPE, query: CallbackQuery
) -> bool:
    """处理账户查看相关回调

    Args:
        data: 回调数据
        update: Telegram更新对象
        context: 上下文对象
        query: 回调查询对象

    Returns:
        bool: 是否已处理
    """
    from callbacks.payment_callbacks_account_view import (
        handle_payment_back_gcash, handle_payment_back_paymaya,
        handle_payment_copy_gcash, handle_payment_copy_paymaya,
        handle_payment_refresh_table, handle_payment_view_all_accounts,
        handle_payment_view_balance_history, handle_payment_view_gcash,
        handle_payment_view_paymaya)

    if data == "payment_view_gcash":
        await handle_payment_view_gcash(update, context, query)
        return True
    elif data == "payment_view_paymaya":
        await handle_payment_view_paymaya(update, context, query)
        return True
    elif data == "payment_view_all_accounts":
        await handle_payment_view_all_accounts(update, context, query)
        return True
    elif data == "payment_view_balance_history":
        await handle_payment_view_balance_history(update, context, query)
        return True
    elif data == "payment_refresh_table":
        await handle_payment_refresh_table(update, context, query)
        return True
    elif data == "payment_copy_gcash":
        await handle_payment_copy_gcash(update, context, query)
        return True
    elif data == "payment_copy_paymaya":
        await handle_payment_copy_paymaya(update, context, query)
        return True
    elif data == "payment_back_gcash":
        await handle_payment_back_gcash(update, context, query)
        return True
    elif data == "payment_back_paymaya":
        await handle_payment_back_paymaya(update, context, query)
        return True

    return False
