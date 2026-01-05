"""支付回调账户编辑模块

包含账户编辑相关的回调处理逻辑。
"""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from handlers.data_access import get_payment_account_by_id_for_callback

logger = logging.getLogger(__name__)


async def handle_payment_edit_gcash(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """编辑GCASH账户"""
    try:
        if query.message:
            await query.message.reply_text(
                "请输入GCASH账号信息：\n"
                "格式: <账号号码> <账户名称>\n"
                "示例: 09171234567 张三\n"
                "输入 'cancel' 取消"
            )
        else:
            await query.answer("请输入GCASH账号信息", show_alert=True)
    except Exception as e:
        logger.error(f"发送GCASH账号提示失败: {e}", exc_info=True)
        await query.answer("请输入GCASH账号信息", show_alert=True)
    context.user_data["state"] = "EDITING_ACCOUNT_GCASH"
    await query.answer()


async def handle_payment_edit_paymaya(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """编辑PayMaya账户"""
    try:
        if query.message:
            await query.message.reply_text(
                "请输入PayMaya账号信息：\n"
                "格式: <账号号码> <账户名称>\n"
                "示例: 09171234567 李四\n"
                "输入 'cancel' 取消"
            )
        else:
            await query.answer("请输入PayMaya账号信息", show_alert=True)
    except Exception as e:
        logger.error(f"发送PayMaya账号提示失败: {e}", exc_info=True)
        await query.answer("请输入PayMaya账号信息", show_alert=True)
    context.user_data["state"] = "EDITING_ACCOUNT_PAYMAYA"
    await query.answer()


async def handle_payment_edit_account(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query, data: str
) -> None:
    """显示账户详情，提供编辑选项"""
    try:
        account_id = int(data.split("_")[-1])
        account = await get_payment_account_by_id_for_callback(account_id)
        if not account:
            await query.answer("❌ 账户不存在", show_alert=True)
            return

        account_type = account.get("account_type", "")
        account_name = account.get("account_name", "未设置")
        account_number = account.get("account_number", "未设置")
        balance = account.get("balance", 0)

        type_name = "GCASH" if account_type == "gcash" else "PayMaya"
        display_name = (
            account_name
            if account_name and account_name != "未设置"
            else account_number
        )

        msg = (
            f"💳 {type_name} 账户详情\n\n"
            f"账户名称: {display_name}\n"
            f"账号号码: {account_number}\n"
            f"当前余额: {balance:,.2f}\n\n"
            f"请选择操作："
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "💰 修改余额", callback_data=f"payment_update_balance_{account_id}"
                ),
                InlineKeyboardButton(
                    "✏️ 编辑信息", callback_data=f"payment_edit_info_{account_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔙 返回",
                    callback_data=(
                        "payment_view_gcash"
                        if account_type == "gcash"
                        else "payment_view_paymaya"
                    ),
                )
            ],
        ]

        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
        await query.answer()
    except (ValueError, IndexError):
        await query.answer("❌ 无效的账户ID", show_alert=True)


async def handle_payment_edit_info(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query, data: str
) -> None:
    """编辑指定ID的账户信息"""
    try:
        account_id = int(data.split("_")[-1])
        account = await get_payment_account_by_id_for_callback(account_id)
        if not account:
            await query.answer("❌ 账户不存在", show_alert=True)
            return

        context.user_data["editing_account_id"] = account_id
        account_type = account.get("account_type", "")

        try:
            if query.message:
                await query.message.reply_text(
                    "请输入账户信息：\n"
                    f"格式: <账号号码> <账户名称>\n"
                    f"示例: 09171234567 {'张三' if account_type == 'gcash' else '李四'}\n"
                    f"输入 'cancel' 取消"
                )
            else:
                await query.answer("请输入账户信息", show_alert=True)
        except Exception as e:
            logger.error(f"发送账户编辑提示失败: {e}", exc_info=True)
            await query.answer("请输入账户信息", show_alert=True)

        context.user_data["state"] = f"EDITING_ACCOUNT_BY_ID_{account_type.upper()}"
        await query.answer()
    except (ValueError, IndexError):
        await query.answer("❌ 无效的账户ID", show_alert=True)
