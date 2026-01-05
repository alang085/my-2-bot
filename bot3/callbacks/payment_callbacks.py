"""支付账号回调处理器"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from callbacks.payment_callbacks_account_add import (
    handle_payment_add_account, handle_payment_add_gcash,
    handle_payment_add_paymaya)
from callbacks.payment_callbacks_account_edit import (
    handle_payment_edit_account, handle_payment_edit_gcash,
    handle_payment_edit_info, handle_payment_edit_paymaya)
from callbacks.payment_callbacks_account_selection import (
    handle_payment_choose_gcash_type, handle_payment_choose_paymaya_type,
    handle_payment_select_account)
from callbacks.payment_callbacks_account_send import (
    handle_order_action_back, handle_payment_send_account,
    handle_payment_send_gcash, handle_payment_send_paymaya)
from callbacks.payment_callbacks_account_view import (
    handle_payment_back_gcash, handle_payment_back_paymaya,
    handle_payment_copy_gcash, handle_payment_copy_paymaya,
    handle_payment_refresh_table, handle_payment_view_all_accounts,
    handle_payment_view_balance_history, handle_payment_view_gcash,
    handle_payment_view_paymaya)
from callbacks.payment_callbacks_balance import (
    handle_payment_batch_update_balance, handle_payment_update_balance_by_id,
    handle_payment_update_balance_gcash, handle_payment_update_balance_paymaya)
from decorators import authorized_required

logger = logging.getLogger(__name__)


@authorized_required
async def handle_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理支付账号相关的回调"""
    from callbacks.payment_add_handlers import handle_payment_add_callbacks
    from callbacks.payment_balance_handlers import \
        handle_payment_balance_callbacks
    from callbacks.payment_edit_handlers import handle_payment_edit_callbacks
    from callbacks.payment_select_handlers import \
        handle_payment_select_callbacks
    from callbacks.payment_send_handlers import handle_payment_send_callbacks
    from callbacks.payment_view_handlers import handle_payment_view_callbacks

    query = update.callback_query
    if not query:
        logger.error("handle_payment_callback: query is None")
        return

    data = query.data
    if not data:
        logger.error("handle_payment_callback: data is None")
        return

    try:
        await query.answer()
    except Exception:
        pass

    # 处理各类回调
    # 1. 账户选择相关
    if await handle_payment_select_callbacks(data, update, context, query):
        return

    # 2. 账户发送相关
    if await handle_payment_send_callbacks(data, update, context, query):
        return

    # 3. 账户查看相关
    if await handle_payment_view_callbacks(data, update, context, query):
        return

    # 4. 账户编辑相关
    if await handle_payment_edit_callbacks(data, update, context, query):
        return

    # 5. 余额更新相关
    if await handle_payment_balance_callbacks(data, update, context, query):
        return

    # 6. 账户添加相关
    if await handle_payment_add_callbacks(data, update, context, query):
        return

    # 未处理的回调
    logger.warning(f"Unhandled payment callback data: {data}")
    await query.answer("⚠️ 未知的操作", show_alert=True)
