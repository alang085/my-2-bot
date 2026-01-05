"""支付回调账户查看模块

包含账户查看相关的回调处理逻辑。
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from handlers.data_access import get_payment_account_for_callback

logger = logging.getLogger(__name__)


async def handle_payment_view_gcash(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """查看GCASH账户"""
    from handlers.payment_handlers import show_gcash

    await show_gcash(update, context)


async def handle_payment_view_paymaya(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """查看PayMaya账户"""
    from handlers.payment_handlers import show_paymaya

    await show_paymaya(update, context)


async def handle_payment_view_all_accounts(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """查看所有账户"""
    from handlers.payment_handlers import show_all_accounts

    try:
        # 如果是回调，先关闭内联键盘
        if query.message:
            await query.edit_message_text("💳 正在加载账户信息...")
        await show_all_accounts(update, context)
    except Exception as e:
        logger.error(f"显示所有账户失败: {e}", exc_info=True)
        await query.answer("❌ 加载失败", show_alert=True)


async def handle_payment_view_balance_history(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """查看余额历史"""
    from handlers.payment_handlers import balance_history

    try:
        # 如果是回调，先关闭内联键盘
        if query.message:
            await query.edit_message_text("📊 正在加载余额历史...")
        await balance_history(update, context)
    except Exception as e:
        logger.error(f"显示余额历史失败: {e}", exc_info=True)
        await query.answer("❌ 加载失败", show_alert=True)


async def handle_payment_refresh_table(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """刷新账户表格"""
    from handlers.payment_handlers import show_all_accounts

    await show_all_accounts(update, context)


async def handle_payment_copy_gcash(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """复制GCASH账号号码"""
    account = await get_payment_account_for_callback("gcash")
    if account:
        account_number = account.get("account_number", "")
        await query.answer(f"账号号码: {account_number}", show_alert=True)
    else:
        await query.answer("❌ 账号未设置", show_alert=True)


async def handle_payment_copy_paymaya(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """复制PayMaya账号号码"""
    account = await get_payment_account_for_callback("paymaya")
    if account:
        account_number = account.get("account_number", "")
        await query.answer(f"账号号码: {account_number}", show_alert=True)
    else:
        await query.answer("❌ 账号未设置", show_alert=True)


async def handle_payment_back_gcash(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """返回GCASH页面"""
    from handlers.payment_handlers import show_gcash

    await show_gcash(update, context)


async def handle_payment_back_paymaya(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """返回PayMaya页面"""
    from handlers.payment_handlers import show_paymaya

    await show_paymaya(update, context)
