"""支付回调账户添加模块

包含账户添加相关的回调处理逻辑。
"""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def handle_payment_add_account(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """选择要添加的账户类型"""
    keyboard = [
        [
            InlineKeyboardButton("💳 添加GCASH账户", callback_data="payment_add_gcash"),
            InlineKeyboardButton(
                "💳 添加PayMaya账户", callback_data="payment_add_paymaya"
            ),
        ],
        [InlineKeyboardButton("🔙 返回", callback_data="payment_refresh_table")],
    ]
    await query.edit_message_text(
        "💳 选择要添加的账户类型：", reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await query.answer()


async def handle_payment_add_gcash(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """添加GCASH账户"""
    try:
        if query.message:
            await query.message.reply_text(
                "请输入新的GCASH账户信息：\n"
                "格式: <账号号码> <账户名称>\n"
                "示例: 09171234567 张三\n"
                "输入 'cancel' 取消"
            )
        else:
            await query.answer("请输入新的GCASH账户信息", show_alert=True)
    except Exception as e:
        logger.error(f"发送GCASH账户提示失败: {e}", exc_info=True)
        await query.answer("请输入新的GCASH账户信息", show_alert=True)
    context.user_data["state"] = "ADDING_ACCOUNT_GCASH"
    await query.answer()


async def handle_payment_add_paymaya(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """添加PayMaya账户"""
    try:
        if query.message:
            await query.message.reply_text(
                "请输入新的PayMaya账户信息：\n"
                "格式: <账号号码> <账户名称>\n"
                "示例: 09171234567 李四\n"
                "输入 'cancel' 取消"
            )
        else:
            await query.answer("请输入新的PayMaya账户信息", show_alert=True)
    except Exception as e:
        logger.error(f"发送PayMaya账户提示失败: {e}", exc_info=True)
        await query.answer("请输入新的PayMaya账户信息", show_alert=True)
    context.user_data["state"] = "ADDING_ACCOUNT_PAYMAYA"
    await query.answer()
