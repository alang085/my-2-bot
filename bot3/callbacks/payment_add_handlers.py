"""支付回调 - 账户添加处理模块

包含处理账户添加相关回调的逻辑。
"""

from telegram import CallbackQuery, Update
from telegram.ext import ContextTypes

# 这些函数在 payment_callbacks_account_add.py 中定义
# 导入将在运行时动态处理


async def handle_payment_add_callbacks(
    data: str, update: Update, context: ContextTypes.DEFAULT_TYPE, query: CallbackQuery
) -> bool:
    """处理账户添加相关回调

    Args:
        data: 回调数据
        update: Telegram更新对象
        context: 上下文对象
        query: 回调查询对象

    Returns:
        bool: 是否已处理
    """
    from callbacks.payment_callbacks_account_add import (
        handle_payment_add_account, handle_payment_add_gcash,
        handle_payment_add_paymaya)

    if data == "payment_add_account":
        await handle_payment_add_account(update, context, query)
        return True
    elif data == "payment_add_gcash":
        await handle_payment_add_gcash(update, context, query)
        return True
    elif data == "payment_add_paymaya":
        await handle_payment_add_paymaya(update, context, query)
        return True

    return False
