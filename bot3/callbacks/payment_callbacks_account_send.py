"""支付回调账户发送模块

包含账户发送相关的回调处理逻辑。
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from handlers.data_access import (get_order_by_chat_id_for_callback,
                                  get_payment_account_by_id_for_callback,
                                  get_payment_account_for_callback)
from utils.chat_helpers import is_group_chat

logger = logging.getLogger(__name__)


async def handle_payment_send_account(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query, data: str
) -> None:
    """根据账户ID发送完整账户信息到群组"""
    is_group = is_group_chat(update)
    try:
        account_id = int(data.split("_")[-1])
    except (ValueError, IndexError):
        msg = "❌ Invalid account ID" if is_group else "❌ 无效的账户ID"
        await query.answer(msg, show_alert=True)
        return

    account = await get_payment_account_by_id_for_callback(account_id)
    if not account:
        msg = "❌ Account not found" if is_group else "❌ 账户不存在"
        await query.answer(msg, show_alert=True)
        return

    if not account.get("account_number"):
        msg = "❌ Account number not set" if is_group else "❌ 账户号码未设置"
        await query.answer(msg, show_alert=True)
        return

    account_type = account.get("account_type", "").upper()
    account_number = account.get("account_number", "")
    account_name = account.get("account_name", "")

    message = (
        f"💳 {account_type} Payment Account\n\n"
        f"Account Number: {account_number}\n"
        f"Account Name: {account_name}"
    )

    chat_id = query.message.chat_id
    try:
        await context.bot.send_message(chat_id=chat_id, text=message)
        success_msg = "✅ Account sent" if is_group else "✅ 账户已发送到群组"
        await query.answer(success_msg)
        edit_msg = "✅ Account sent" if is_group else "✅ 账户已发送"
        await query.edit_message_text(edit_msg, reply_markup=None)
    except Exception as e:
        logger.error(f"发送账户失败: {e}", exc_info=True)
        error_msg = f"❌ Send failed: {e}" if is_group else f"❌ 发送失败: {e}"
        await query.answer(error_msg, show_alert=True)


async def handle_payment_send_gcash(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """发送GCASH账户信息"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    from handlers.data_access import get_payment_account_for_callback

    try:
        account = await get_payment_account_for_callback("gcash")
        if not account or not account.get("account_number"):
            await query.answer("❌ GCASH账号未设置", show_alert=True)
            return

        account_number = account.get("account_number", "")
        account_name = account.get("account_name", "")

        # 格式化消息，方便发送给客户
        message = (
            f"💳 GCASH Payment Account\n\n"
            f"Account Number: `{account_number}`\n"
            f"Account Name: {account_name}\n\n"
            f"请将上述账号信息发送给客户。"
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "📋 复制账号号码", callback_data="payment_copy_gcash"
                )
            ],
            [InlineKeyboardButton("🔙 返回", callback_data="payment_back_gcash")],
        ]

        await query.edit_message_text(
            message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )
        await query.answer("✅ 账号信息已显示，可以复制发送给客户")
    except Exception as e:
        logger.error(f"处理payment_send_gcash出错: {e}", exc_info=True)
        await query.answer(f"❌ 错误: {e}", show_alert=True)


async def handle_payment_send_paymaya(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """发送PayMaya账户信息"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    from handlers.data_access import get_payment_account_for_callback

    try:
        account = await get_payment_account_for_callback("paymaya")
        if not account or not account.get("account_number"):
            await query.answer("❌ PayMaya账号未设置", show_alert=True)
            return

        account_number = account.get("account_number", "")
        account_name = account.get("account_name", "")

        # 格式化消息，方便发送给客户
        message = (
            f"💳 PayMaya Payment Account\n\n"
            f"Account Number: `{account_number}`\n"
            f"Account Name: {account_name}\n\n"
            f"请将上述账号信息发送给客户。"
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "📋 复制账号号码", callback_data="payment_copy_paymaya"
                )
            ],
            [InlineKeyboardButton("🔙 返回", callback_data="payment_back_paymaya")],
        ]

        await query.edit_message_text(
            message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )
        await query.answer("✅ 账号信息已显示，可以复制发送给客户")
    except Exception as e:
        logger.error(f"处理payment_send_paymaya出错: {e}", exc_info=True)
        await query.answer(f"❌ 错误: {e}", show_alert=True)


async def handle_order_action_back(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """返回到订单界面"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    from handlers.data_access import get_order_by_chat_id_for_callback
    from utils.chat_helpers import is_group_chat

    is_group = is_group_chat(update)
    chat_id = query.message.chat_id
    order = await get_order_by_chat_id_for_callback(chat_id)
    if not order:
        msg = (
            "❌ No active order in this group"
            if is_group
            else "❌ 当前群组没有活跃订单"
        )
        await query.edit_message_text(msg)
        return

    msg = (
        f"📋 Current Order Status:\n"
        f"──────────────────\n"
        f"📝 Order ID: `{order['order_id']}`\n"
        f"🏷️ Group ID: `{order['group_id']}`\n"
        f"📅 Date: {order['date']}\n"
        f"👥 Week Group: {order['weekday_group']}\n"
        f"👤 Customer: {order['customer']}\n"
        f"💰 Amount: {order['amount']:.2f}\n"
        f"📊 State: {order['state']}\n"
        f"──────────────────"
    )

    # 群聊使用英文按钮，私聊使用中文
    if is_group:
        keyboard = [
            [
                InlineKeyboardButton("✅ Normal", callback_data="order_action_normal"),
                InlineKeyboardButton("⚠️ Overdue", callback_data="order_action_overdue"),
            ],
            [
                InlineKeyboardButton("🏁 End", callback_data="order_action_end"),
                InlineKeyboardButton("🚫 Breach", callback_data="order_action_breach"),
            ],
            [
                InlineKeyboardButton(
                    "💸 Breach End", callback_data="order_action_breach_end"
                )
            ],
            [
                InlineKeyboardButton(
                    "💳 Send Account", callback_data="payment_select_account"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔄 Change Attribution",
                    callback_data="order_action_change_attribution",
                )
            ],
        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton("✅ 正常", callback_data="order_action_normal"),
                InlineKeyboardButton("⚠️ 逾期", callback_data="order_action_overdue"),
            ],
            [
                InlineKeyboardButton("🏁 完成", callback_data="order_action_end"),
                InlineKeyboardButton("🚫 违约", callback_data="order_action_breach"),
            ],
            [
                InlineKeyboardButton(
                    "💸 违约完成", callback_data="order_action_breach_end"
                )
            ],
            [
                InlineKeyboardButton(
                    "💳 发送账户", callback_data="payment_select_account"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔄 更改归属", callback_data="order_action_change_attribution"
                )
            ],
        ]

    await query.edit_message_text(
        msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
    )
