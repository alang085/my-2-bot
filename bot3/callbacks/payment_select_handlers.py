"""支付回调 - 账户选择处理模块

包含处理账户选择相关回调的逻辑。
"""

from telegram import CallbackQuery, Update
from telegram.ext import ContextTypes

# 这些函数在 payment_callbacks_account_selection.py 中定义
# 导入将在运行时动态处理


async def handle_payment_select_callbacks(
    data: str, update: Update, context: ContextTypes.DEFAULT_TYPE, query: CallbackQuery
) -> bool:
    """处理账户选择相关回调

    Args:
        data: 回调数据
        update: Telegram更新对象
        context: 上下文对象
        query: 回调查询对象

    Returns:
        bool: 是否已处理
    """
    from callbacks.payment_callbacks_account_selection import (
        handle_payment_choose_gcash_type, handle_payment_choose_paymaya_type,
        handle_payment_select_account)

    if data == "payment_select_account":
        await handle_payment_select_account(update, context, query)
        return True
    elif data == "payment_choose_gcash_type":
        await handle_payment_choose_gcash_type(update, context, query)
        return True
    elif data == "payment_choose_paymaya_type":
        await handle_payment_choose_paymaya_type(update, context, query)
        return True

    return False
