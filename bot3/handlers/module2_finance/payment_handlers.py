"""支付账号管理处理器"""

import logging
from typing import Any, Dict, List, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

import db_operations
from decorators import (admin_required, authorized_required, error_handler,
                        private_chat_only)
from services.module2_finance.payment_service import PaymentService

logger = logging.getLogger(__name__)


def _build_accounts_table(accounts: list) -> str:
    """构建账户表格

    Args:
        accounts: 账户列表

    Returns:
        表格字符串
    """
    table = "💳 账户数据表格\n\n"
    table += "┌──────────────┬──────────────────────┬───────────────┐\n"
    table += "│ 账户类型     │ 账号号码              │ 余额          │\n"
    table += "├──────────────┼──────────────────────┼───────────────┤\n"

    for account in accounts:
        account_type = account.get("account_type", "")
        account_number = account.get("account_number", "未设置")
        balance = account.get("balance", 0)

        type_name = "GCASH" if account_type == "gcash" else "PayMaya"
        type_display = type_name.ljust(14)

        if len(account_number) > 20:
            number_display = account_number[:18] + ".."
        else:
            number_display = account_number.ljust(22)

        balance_display = f"{balance:,.2f}".rjust(13)
        table += f"│ {type_display} │ {number_display} │ {balance_display} │\n"

    table += "└──────────────┴──────────────────────┴───────────────┘\n\n"
    return table


def _build_accounts_details(accounts: list) -> str:
    """构建账户详细信息

    Args:
        accounts: 账户列表

    Returns:
        详细信息字符串
    """
    details = "📋 详细信息：\n\n"
    for account in accounts:
        account_type = account.get("account_type", "")
        account_number = account.get("account_number", "未设置")
        account_name = account.get("account_name", "未设置")
        balance = account.get("balance", 0)

        type_name = "GCASH" if account_type == "gcash" else "PayMaya"
        details += f"💳 {type_name}\n"
        details += f"   账号号码: {account_number}\n"
        details += f"   账户名称: {account_name}\n"
        details += f"   当前余额: {balance:,.2f}\n\n"
    return details


def _build_accounts_keyboard() -> InlineKeyboardMarkup:
    """构建账户操作键盘

    Returns:
        内联键盘
    """
    keyboard = [
        [
            InlineKeyboardButton("💳 GCASH", callback_data="payment_view_gcash"),
            InlineKeyboardButton("💳 PayMaya", callback_data="payment_view_paymaya"),
        ],
        [InlineKeyboardButton("➕ 添加账户", callback_data="payment_add_account")],
        [InlineKeyboardButton("🔄 刷新", callback_data="payment_refresh_table")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def _send_accounts_message(
    update: Update, table: str, reply_markup: InlineKeyboardMarkup
) -> None:
    """发送账户消息

    Args:
        update: Telegram更新对象
        table: 表格文本
        reply_markup: 内联键盘
    """
    if update.message:
        await update.message.reply_text(
            table, reply_markup=reply_markup, parse_mode=None
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            table, reply_markup=reply_markup, parse_mode=None
        )


@error_handler
@authorized_required
@private_chat_only
async def show_all_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """显示所有账户数据表格"""
    if update.effective_chat.type != "private":
        if update.message:
            await update.message.reply_text("⚠️ 此命令只能在私聊中使用")
        elif update.callback_query:
            await update.callback_query.answer(
                "⚠️ 此命令只能在私聊中使用", show_alert=True
            )
        return

    accounts = await PaymentService.get_all_accounts()
    if not accounts:
        msg = "❌ 没有账户数据"
        if update.message:
            await update.message.reply_text(msg)
        elif update.callback_query:
            await update.callback_query.edit_message_text(msg)
        return

    table = _build_accounts_table(accounts)
    table += _build_accounts_details(accounts)
    reply_markup = _build_accounts_keyboard()
    await _send_accounts_message(update, table, reply_markup)


@error_handler
@authorized_required
@private_chat_only
def _build_empty_gcash_message() -> Tuple[str, InlineKeyboardMarkup]:
    """构建空GCASH账户消息

    Returns:
        (消息文本, 键盘)
    """
    msg = "❌ 没有GCASH账户\n\n点击下方按钮添加账户"
    keyboard = [
        [InlineKeyboardButton("➕ 添加GCASH账户", callback_data="payment_add_gcash")],
        [InlineKeyboardButton("🔙 返回", callback_data="payment_refresh_table")],
    ]
    return msg, InlineKeyboardMarkup(keyboard)


def _build_gcash_accounts_message(
    accounts: List[Dict],
) -> Tuple[str, InlineKeyboardMarkup]:
    """构建GCASH账户列表消息

    Args:
        accounts: 账户列表

    Returns:
        (消息文本, 键盘)
    """
    msg = "💳 GCASH账户列表\n\n"
    keyboard = []

    for account in accounts:
        account_id = account.get("id")
        account_number = account.get("account_number", "未设置")
        account_name = account.get("account_name", "未设置")
        balance = account.get("balance", 0)

        display_name = _format_account_display_name(account_name, account_number)

        msg += f"💳 {display_name}\n"
        msg += f"   账号: {account_number}\n"
        msg += f"   余额: {balance:,.2f}\n\n"

        keyboard.append(
            [
                InlineKeyboardButton(
                    f"✏️ {display_name}",
                    callback_data=f"payment_edit_account_{account_id}",
                ),
                InlineKeyboardButton(
                    "💰 修改余额", callback_data=f"payment_update_balance_{account_id}"
                ),
            ]
        )

    keyboard.append(
        [InlineKeyboardButton("➕ 添加GCASH账户", callback_data="payment_add_gcash")]
    )
    keyboard.append(
        [
            InlineKeyboardButton(
                "💰 批量修改余额", callback_data="payment_batch_update_balance"
            )
        ]
    )
    keyboard.append(
        [InlineKeyboardButton("🔙 返回", callback_data="payment_refresh_table")]
    )

    return msg, InlineKeyboardMarkup(keyboard)


async def show_gcash(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """显示GCASH账户列表"""
    accounts = await PaymentService.get_accounts_by_type("gcash")

    if not accounts:
        msg, reply_markup = _build_empty_gcash_message()
    else:
        msg, reply_markup = _build_gcash_accounts_message(accounts)

    if update.message:
        await update.message.reply_text(msg, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(msg, reply_markup=reply_markup)


@error_handler
@authorized_required
@private_chat_only
def _build_empty_paymaya_message() -> Tuple[str, InlineKeyboardMarkup]:
    """构建空PayMaya账户消息

    Returns:
        (消息文本, 键盘)
    """
    msg = "❌ 没有PayMaya账户\n\n点击下方按钮添加账户"
    keyboard = [
        [
            InlineKeyboardButton(
                "➕ 添加PayMaya账户", callback_data="payment_add_paymaya"
            )
        ],
        [InlineKeyboardButton("🔙 返回", callback_data="payment_refresh_table")],
    ]
    return msg, InlineKeyboardMarkup(keyboard)


def _format_account_display_name(account_name: str, account_number: str) -> str:
    """格式化账户显示名称

    Args:
        account_name: 账户名称
        account_number: 账号号码

    Returns:
        显示名称
    """
    display_name = (
        account_name if account_name and account_name != "未设置" else account_number
    )
    if len(display_name) > 20:
        display_name = display_name[:18] + ".."
    return display_name


def _build_paymaya_accounts_message(
    accounts: List[Dict],
) -> Tuple[str, InlineKeyboardMarkup]:
    """构建PayMaya账户列表消息

    Args:
        accounts: 账户列表

    Returns:
        (消息文本, 键盘)
    """
    msg = "💳 PayMaya账户列表\n\n"
    keyboard = []

    for account in accounts:
        account_id = account.get("id")
        account_number = account.get("account_number", "未设置")
        account_name = account.get("account_name", "未设置")
        balance = account.get("balance", 0)

        display_name = _format_account_display_name(account_name, account_number)

        msg += f"💳 {display_name}\n"
        msg += f"   账号: {account_number}\n"
        msg += f"   余额: {balance:,.2f}\n\n"

        keyboard.append(
            [
                InlineKeyboardButton(
                    f"✏️ {display_name}",
                    callback_data=f"payment_edit_account_{account_id}",
                ),
                InlineKeyboardButton(
                    "💰 修改余额", callback_data=f"payment_update_balance_{account_id}"
                ),
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "➕ 添加PayMaya账户", callback_data="payment_add_paymaya"
            )
        ]
    )
    keyboard.append(
        [
            InlineKeyboardButton(
                "💰 批量修改余额", callback_data="payment_batch_update_balance"
            )
        ]
    )
    keyboard.append(
        [InlineKeyboardButton("🔙 返回", callback_data="payment_refresh_table")]
    )

    return msg, InlineKeyboardMarkup(keyboard)


async def show_paymaya(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """显示PayMaya账户列表"""
    accounts = await PaymentService.get_accounts_by_type("paymaya")

    if not accounts:
        msg, reply_markup = _build_empty_paymaya_message()
    else:
        msg, reply_markup = _build_paymaya_accounts_message(accounts)

    if update.message:
        await update.message.reply_text(msg, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(msg, reply_markup=reply_markup)


@error_handler
@admin_required
@private_chat_only
async def update_payment_balance(
    update: Update, context: ContextTypes.DEFAULT_TYPE, account_type: str
) -> None:
    """更新支付账号余额"""
    if not context.args:
        await update.message.reply_text(
            f"请输入新的余额金额\n"
            f"格式: /{'gcash' if account_type == 'gcash' else 'paymaya'}_balance <金额>\n"
            f"示例: /{'gcash' if account_type == 'gcash' else 'paymaya'}_balance 5000"
        )
        return

    try:
        new_balance = float(context.args[0])

        # 获取旧余额
        accounts = await PaymentService.get_accounts(account_type)
        old_balance = accounts[0].get("balance", 0) if accounts else 0

        success, error_msg = await PaymentService.update_account(
            account_type, balance=new_balance
        )

        if success:
            # 记录操作历史
            user_id = update.effective_user.id if update.effective_user else None
            current_chat_id = (
                update.effective_chat.id if update.effective_chat else None
            )
            if current_chat_id and user_id:
                await db_operations.record_operation(
                    user_id=user_id,
                    operation_type="payment_account_balance_updated",
                    operation_data={
                        "account_type": account_type,
                        "old_balance": old_balance,
                        "new_balance": new_balance,
                    },
                    chat_id=current_chat_id,
                )

            await update.message.reply_text(
                f"✅ {account_type.upper()}余额已更新为: {new_balance:,.2f}"
            )
        else:
            await update.message.reply_text(error_msg or "❌ 更新失败")
    except ValueError:
        await update.message.reply_text("❌ 请输入有效的数字")


@error_handler
@admin_required
@private_chat_only
async def edit_payment_account(
    update: Update, context: ContextTypes.DEFAULT_TYPE, account_type: str
) -> None:
    """编辑支付账号信息"""
    if len(context.args) < 2:
        await update.message.reply_text(
            f"请输入账号信息\n"
            f"格式: /edit_{account_type} <账号号码> <账户名称>\n"
            f"示例: /edit_{account_type} 09171234567 张三"
        )
        return

    account_number = context.args[0]
    account_name = " ".join(context.args[1:])

    success, error_msg = await PaymentService.update_account(
        account_type, account_number=account_number, account_name=account_name
    )

    if success:
        await update.message.reply_text(
            f"✅ {account_type.upper()}账号信息已更新\n\n"
            f"账号号码: {account_number}\n"
            f"账户名称: {account_name}"
        )
    else:
        await update.message.reply_text(error_msg or "❌ 更新失败")


@error_handler
@authorized_required
@private_chat_only
async def balance_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """查看GCash和Maya总余额（支持查看历史）

    用法：
    /balance_history - 查看当前余额
    /balance_history 2025-01-15 - 查看指定日期的余额
    /balance_history recent - 查看最近7天的余额统计
    """
    from datetime import datetime

    from handlers.module2_finance.payment_balance_current import \
        show_current_balance
    from handlers.module2_finance.payment_balance_date import show_date_balance
    from handlers.module2_finance.payment_balance_message import \
        send_error_message
    from handlers.module2_finance.payment_balance_recent import \
        show_recent_balance

    # 获取命令参数
    args = context.args if context.args else []

    # 如果没有参数，显示当前余额
    if not args:
        await show_current_balance(update, context)
        return

    # 处理参数
    arg = args[0].lower()

    # 查看最近几天的余额
    if arg == "recent":
        await show_recent_balance(update, context)
        return

    # 查看指定日期的余额
    try:
        date_str = args[0]
        # 验证日期格式
        datetime.strptime(date_str, "%Y-%m-%d")
        await show_date_balance(update, context, date_str)
    except ValueError:
        # 日期格式错误
        msg = "❌ 日期格式错误\n\n"
        msg += "正确格式：YYYY-MM-DD\n"
        msg += "示例：/balance_history 2025-01-15\n\n"
        msg += "或使用：/balance_history recent 查看最近7天"
        await send_error_message(update, msg)
