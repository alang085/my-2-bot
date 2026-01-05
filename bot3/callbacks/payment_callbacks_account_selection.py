"""支付回调账户选择模块

包含账户选择相关的回调处理逻辑。
"""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from handlers.data_access import get_payment_accounts_by_type_for_callback
from utils.chat_helpers import is_group_chat

logger = logging.getLogger(__name__)


async def handle_payment_select_account(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """在群聊中选择账户"""
    is_group = is_group_chat(update)
    keyboard = [
        [
            InlineKeyboardButton("💳 GCASH", callback_data="payment_choose_gcash_type"),
            InlineKeyboardButton(
                "💳 PayMaya", callback_data="payment_choose_paymaya_type"
            ),
        ],
        [
            InlineKeyboardButton(
                "🔙 Back" if is_group else "🔙 返回", callback_data="order_action_back"
            )
        ],
    ]

    msg_text = "💳 Select Account:" if is_group else "💳 选择要发送的账户："
    await query.edit_message_text(msg_text, reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_payment_choose_gcash_type(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """显示GCASH所有账户名字列表"""
    is_group = is_group_chat(update)
    accounts = await get_payment_accounts_by_type_for_callback("gcash")

    if not accounts or not any(acc.get("account_name") for acc in accounts):
        msg = "❌ No available GCASH account" if is_group else "❌ 没有可用的GCASH账户"
        await query.answer(msg, show_alert=True)
        return

    keyboard = []
    for account in accounts:
        account_name = account.get("account_name", "")
        if account_name:  # 只显示有名字的账户
            account_id = account.get("id")
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"💳 {account_name}",
                        callback_data=f"payment_send_account_{account_id}",
                    )
                ]
            )

    if not keyboard:
        msg = "❌ No available GCASH account" if is_group else "❌ 没有可用的GCASH账户"
        await query.answer(msg, show_alert=True)
        return

    keyboard.append(
        [
            InlineKeyboardButton(
                "🔙 Back" if is_group else "🔙 返回",
                callback_data="payment_select_account",
            )
        ]
    )

    msg_text = "💳 GCASH - Select Account:" if is_group else "💳 GCASH - 选择账户："
    await query.edit_message_text(msg_text, reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_payment_choose_paymaya_type(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """显示PayMaya所有账户名字列表"""
    is_group = is_group_chat(update)
    accounts = await get_payment_accounts_by_type_for_callback("paymaya")

    if not accounts or not any(acc.get("account_name") for acc in accounts):
        msg = (
            "❌ No available PayMaya account"
            if is_group
            else "❌ 没有可用的PayMaya账户"
        )
        await query.answer(msg, show_alert=True)
        return

    keyboard = []
    for account in accounts:
        account_name = account.get("account_name", "")
        if account_name:  # 只显示有名字的账户
            account_id = account.get("id")
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"💳 {account_name}",
                        callback_data=f"payment_send_account_{account_id}",
                    )
                ]
            )

    if not keyboard:
        msg = (
            "❌ No available PayMaya account"
            if is_group
            else "❌ 没有可用的PayMaya账户"
        )
        await query.answer(msg, show_alert=True)
        return

    keyboard.append(
        [
            InlineKeyboardButton(
                "🔙 Back" if is_group else "🔙 返回",
                callback_data="payment_select_account",
            )
        ]
    )

    msg_text = "💳 PayMaya - Select Account:" if is_group else "💳 PayMaya - 选择账户："
    await query.edit_message_text(msg_text, reply_markup=InlineKeyboardMarkup(keyboard))
