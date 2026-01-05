"""支付回调余额管理模块

包含余额更新相关的回调处理逻辑。
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from handlers.data_access import (get_all_payment_accounts_for_callback,
                                  get_payment_account_by_id_for_callback)

logger = logging.getLogger(__name__)


async def handle_payment_update_balance_gcash(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """更新GCASH余额"""
    try:
        if query.message:
            await query.message.reply_text(
                "请输入新的GCASH余额：\n"
                "格式: 数字（如：5000 或 5000.50）\n"
                "输入 'cancel' 取消"
            )
        else:
            await query.answer("请输入新的GCASH余额", show_alert=True)
    except Exception as e:
        logger.error(f"发送GCASH余额提示失败: {e}", exc_info=True)
        await query.answer("请输入新的GCASH余额", show_alert=True)
    context.user_data["state"] = "UPDATING_BALANCE_GCASH"
    await query.answer()


async def handle_payment_update_balance_paymaya(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """更新PayMaya余额"""
    try:
        if query.message:
            await query.message.reply_text(
                "请输入新的PayMaya余额：\n"
                "格式: 数字（如：5000 或 5000.50）\n"
                "输入 'cancel' 取消"
            )
        else:
            await query.answer("请输入新的PayMaya余额", show_alert=True)
    except Exception as e:
        logger.error(f"发送PayMaya余额提示失败: {e}", exc_info=True)
        await query.answer("请输入新的PayMaya余额", show_alert=True)
    context.user_data["state"] = "UPDATING_BALANCE_PAYMAYA"
    await query.answer()


async def handle_payment_update_balance_by_id(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query, data: str
) -> None:
    """修改指定ID的账户余额"""
    try:
        account_id = int(data.split("_")[-1])
        account = await get_payment_account_by_id_for_callback(account_id)
        if not account:
            await query.answer("❌ 账户不存在", show_alert=True)
            return

        context.user_data["updating_balance_account_id"] = account_id
        account_type = account.get("account_type", "")
        account_name = account.get("account_name", "未设置")
        account_number = account.get("account_number", "未设置")
        current_balance = account.get("balance", 0)

        type_name = "GCASH" if account_type == "gcash" else "PayMaya"
        display_name = (
            account_name
            if account_name and account_name != "未设置"
            else account_number
        )

        try:
            if query.message:
                await query.message.reply_text(
                    f"💰 修改 {type_name} 账户余额\n\n"
                    f"账户: {display_name}\n"
                    f"账号: {account_number}\n"
                    f"当前余额: {current_balance:,.2f}\n\n"
                    f"请输入新的余额：\n"
                    f"格式: 数字（如：5000 或 5000.50）\n"
                    f"输入 'cancel' 取消"
                )
            else:
                await query.answer("请输入新的余额", show_alert=True)
        except Exception as e:
            logger.error(f"发送余额修改提示失败: {e}", exc_info=True)
            await query.answer("请输入新的余额", show_alert=True)

        context.user_data["state"] = f"UPDATING_BALANCE_BY_ID_{account_id}"
        await query.answer()
    except (ValueError, IndexError):
        await query.answer("❌ 无效的账户ID", show_alert=True)


async def handle_payment_batch_update_balance(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """批量修改余额模式"""
    accounts = await get_all_payment_accounts_for_callback()
    if not accounts:
        await query.answer("❌ 没有账户", show_alert=True)
        return

    # 初始化批量修改状态
    context.user_data["batch_update_accounts"] = [acc.get("id") for acc in accounts]
    context.user_data["batch_update_index"] = 0
    context.user_data["batch_update_changes"] = []
    context.user_data["state"] = "BATCH_UPDATE_BALANCE"

    # 显示第一个账户
    first_account = accounts[0]
    account_id = first_account.get("id")
    account_type = first_account.get("account_type", "")
    account_name = first_account.get("account_name", "未设置")
    account_number = first_account.get("account_number", "未设置")
    current_balance = first_account.get("balance", 0)

    type_name = "GCASH" if account_type == "gcash" else "PayMaya"
    display_name = (
        account_name if account_name and account_name != "未设置" else account_number
    )

    msg = "💰 批量修改余额模式\n\n"
    msg += f"账户 {1}/{len(accounts)}: {type_name}\n"
    msg += f"账户: {display_name}\n"
    msg += f"账号: {account_number}\n"
    msg += f"当前余额: {current_balance:,.2f}\n\n"
    msg += "请输入新的余额：\n"
    msg += "格式: 数字（如：5000 或 5000.50）\n"
    msg += "输入 'done' 或 '完成' 完成所有修改并退出\n"
    msg += "输入 'cancel' 取消"

    try:
        if query.message:
            await query.message.reply_text(msg)
        else:
            await query.edit_message_text(msg)
    except Exception as e:
        logger.error(f"发送批量修改提示失败: {e}", exc_info=True)
        await query.answer("开始批量修改", show_alert=True)

    await query.answer()
