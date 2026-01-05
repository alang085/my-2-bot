"""支付回调 - 账户发送处理模块

包含处理账户发送相关回调的逻辑。
"""

from telegram import CallbackQuery, Update
from telegram.ext import ContextTypes

# 这些函数在 payment_callbacks_account_send.py 中定义
# 导入将在运行时动态处理


async def handle_payment_send_callbacks(
    data: str, update: Update, context: ContextTypes.DEFAULT_TYPE, query: CallbackQuery
) -> bool:
    """处理账户发送相关回调

    Args:
        data: 回调数据
        update: Telegram更新对象
        context: 上下文对象
        query: 回调查询对象

    Returns:
        bool: 是否已处理
    """
    from callbacks.payment_callbacks_account_send import (
        handle_order_action_back, handle_payment_send_account,
        handle_payment_send_gcash, handle_payment_send_paymaya)

    if data.startswith("payment_send_account_"):
        await handle_payment_send_account(update, context, query, data)
        return True
    elif data == "payment_send_gcash":
        await handle_payment_send_gcash(update, context, query)
        return True
    elif data == "payment_send_paymaya":
        await handle_payment_send_paymaya(update, context, query)
        return True
    elif data == "order_action_back":
        await handle_order_action_back(update, context, query)
        return True

    return False
