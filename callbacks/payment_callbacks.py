"""支付账号回调处理器"""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

import db_operations
from decorators import authorized_required
from utils.chat_helpers import is_group_chat

logger = logging.getLogger(__name__)


@authorized_required
async def handle_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理支付账号相关的回调"""
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

    if data == "payment_select_account":
        # 在群聊中选择账户
        is_group = is_group_chat(update)
        keyboard = [
            [
                InlineKeyboardButton("💳 GCASH", callback_data="payment_choose_gcash_type"),
                InlineKeyboardButton("💳 PayMaya", callback_data="payment_choose_paymaya_type"),
            ],
            [
                InlineKeyboardButton(
                    "🔙 Back" if is_group else "🔙 返回", callback_data="order_action_back"
                )
            ],
        ]

        msg_text = "💳 Select Account:" if is_group else "💳 选择要发送的账户："
        await query.edit_message_text(msg_text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data == "payment_choose_gcash_type":
        # 显示GCASH所有账户名字列表
        is_group = is_group_chat(update)
        accounts = await db_operations.get_payment_accounts_by_type("gcash")

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
                            f"💳 {account_name}", callback_data=f"payment_send_account_{account_id}"
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
                    "🔙 Back" if is_group else "🔙 返回", callback_data="payment_select_account"
                )
            ]
        )

        msg_text = "💳 GCASH - Select Account:" if is_group else "💳 GCASH - 选择账户："
        await query.edit_message_text(msg_text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data == "payment_choose_paymaya_type":
        # 显示PayMaya所有账户名字列表
        is_group = is_group_chat(update)
        accounts = await db_operations.get_payment_accounts_by_type("paymaya")

        if not accounts or not any(acc.get("account_name") for acc in accounts):
            msg = "❌ No available PayMaya account" if is_group else "❌ 没有可用的PayMaya账户"
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
                            f"💳 {account_name}", callback_data=f"payment_send_account_{account_id}"
                        )
                    ]
                )

        if not keyboard:
            msg = "❌ No available PayMaya account" if is_group else "❌ 没有可用的PayMaya账户"
            await query.answer(msg, show_alert=True)
            return

        keyboard.append(
            [
                InlineKeyboardButton(
                    "🔙 Back" if is_group else "🔙 返回", callback_data="payment_select_account"
                )
            ]
        )

        msg_text = "💳 PayMaya - Select Account:" if is_group else "💳 PayMaya - 选择账户："
        await query.edit_message_text(msg_text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data.startswith("payment_send_account_"):
        # 根据账户ID发送完整账户信息到群组
        is_group = is_group_chat(update)
        try:
            account_id = int(data.split("_")[-1])
        except (ValueError, IndexError):
            msg = "❌ Invalid account ID" if is_group else "❌ 无效的账户ID"
            await query.answer(msg, show_alert=True)
            return

        account = await db_operations.get_payment_account_by_id(account_id)
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
        return

    if data == "order_action_back":
        # 返回到订单界面
        is_group = is_group_chat(update)
        chat_id = query.message.chat_id
        order = await db_operations.get_order_by_chat_id(chat_id)
        if not order:
            msg = "❌ No active order in this group" if is_group else "❌ 当前群组没有活跃订单"
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
                [InlineKeyboardButton("💸 Breach End", callback_data="order_action_breach_end")],
                [InlineKeyboardButton("💳 Send Account", callback_data="payment_select_account")],
                [
                    InlineKeyboardButton(
                        "🔄 Change Attribution", callback_data="order_action_change_attribution"
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
                [InlineKeyboardButton("💸 违约完成", callback_data="order_action_breach_end")],
                [InlineKeyboardButton("💳 发送账户", callback_data="payment_select_account")],
                [
                    InlineKeyboardButton(
                        "🔄 更改归属", callback_data="order_action_change_attribution"
                    )
                ],
            ]

        await query.edit_message_text(
            msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )
        return

    if data == "payment_send_gcash":
        try:
            account = await db_operations.get_payment_account("gcash")
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
                [InlineKeyboardButton("📋 复制账号号码", callback_data="payment_copy_gcash")],
                [InlineKeyboardButton("🔙 返回", callback_data="payment_back_gcash")],
            ]

            await query.edit_message_text(
                message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
            )
            await query.answer("✅ 账号信息已显示，可以复制发送给客户")
        except Exception as e:
            logger.error(f"处理payment_send_gcash出错: {e}", exc_info=True)
            await query.answer(f"❌ 错误: {e}", show_alert=True)

    elif data == "payment_send_paymaya":
        try:
            account = await db_operations.get_payment_account("paymaya")
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
                [InlineKeyboardButton("📋 复制账号号码", callback_data="payment_copy_paymaya")],
                [InlineKeyboardButton("🔙 返回", callback_data="payment_back_paymaya")],
            ]

            await query.edit_message_text(
                message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
            )
            await query.answer("✅ 账号信息已显示，可以复制发送给客户")
        except Exception as e:
            logger.error(f"处理payment_send_paymaya出错: {e}", exc_info=True)
            await query.answer(f"❌ 错误: {e}", show_alert=True)

    elif data == "payment_update_balance_gcash":
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

    elif data == "payment_update_balance_paymaya":
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

    elif data == "payment_edit_gcash":
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

    elif data == "payment_edit_paymaya":
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

    elif data == "payment_back_gcash":
        from handlers.payment_handlers import show_gcash

        await show_gcash(update, context)

    elif data == "payment_back_paymaya":
        from handlers.payment_handlers import show_paymaya

        await show_paymaya(update, context)

    elif data == "payment_copy_gcash":
        account = await db_operations.get_payment_account("gcash")
        if account:
            account_number = account.get("account_number", "")
            await query.answer(f"账号号码: {account_number}", show_alert=True)
        else:
            await query.answer("❌ 账号未设置", show_alert=True)

    elif data == "payment_copy_paymaya":
        account = await db_operations.get_payment_account("paymaya")
        if account:
            account_number = account.get("account_number", "")
            await query.answer(f"账号号码: {account_number}", show_alert=True)
        else:
            await query.answer("❌ 账号未设置", show_alert=True)

    elif data == "payment_view_gcash":
        from handlers.payment_handlers import show_gcash

        await show_gcash(update, context)

    elif data == "payment_view_paymaya":
        from handlers.payment_handlers import show_paymaya

        await show_paymaya(update, context)

    elif data == "payment_refresh_table":
        from handlers.payment_handlers import show_all_accounts

        await show_all_accounts(update, context)

    elif data == "payment_add_account":
        # 选择要添加的账户类型
        keyboard = [
            [
                InlineKeyboardButton("💳 添加GCASH账户", callback_data="payment_add_gcash"),
                InlineKeyboardButton("💳 添加PayMaya账户", callback_data="payment_add_paymaya"),
            ],
            [InlineKeyboardButton("🔙 返回", callback_data="payment_refresh_table")],
        ]
        await query.edit_message_text(
            "💳 选择要添加的账户类型：", reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await query.answer()

    elif data == "payment_add_gcash":
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

    elif data == "payment_add_paymaya":
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

    elif data.startswith("payment_update_balance_"):
        # 修改指定ID的账户余额
        try:
            account_id = int(data.split("_")[-1])
            account = await db_operations.get_payment_account_by_id(account_id)
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
                account_name if account_name and account_name != "未设置" else account_number
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

    elif data == "payment_batch_update_balance":
        # 批量修改余额模式
        accounts = await db_operations.get_all_payment_accounts()
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
        display_name = account_name if account_name and account_name != "未设置" else account_number

        msg = f"💰 批量修改余额模式\n\n"
        msg += f"账户 {1}/{len(accounts)}: {type_name}\n"
        msg += f"账户: {display_name}\n"
        msg += f"账号: {account_number}\n"
        msg += f"当前余额: {current_balance:,.2f}\n\n"
        msg += f"请输入新的余额：\n"
        msg += f"格式: 数字（如：5000 或 5000.50）\n"
        msg += f"输入 'done' 或 '完成' 完成所有修改并退出\n"
        msg += f"输入 'cancel' 取消"

        try:
            if query.message:
                await query.message.reply_text(msg)
            else:
                await query.edit_message_text(msg)
        except Exception as e:
            logger.error(f"发送批量修改提示失败: {e}", exc_info=True)
            await query.answer("开始批量修改", show_alert=True)

        await query.answer()

    elif data.startswith("payment_edit_account_"):
        # 显示账户详情，提供编辑选项
        try:
            account_id = int(data.split("_")[-1])
            account = await db_operations.get_payment_account_by_id(account_id)
            if not account:
                await query.answer("❌ 账户不存在", show_alert=True)
                return

            account_type = account.get("account_type", "")
            account_name = account.get("account_name", "未设置")
            account_number = account.get("account_number", "未设置")
            balance = account.get("balance", 0)

            type_name = "GCASH" if account_type == "gcash" else "PayMaya"
            display_name = (
                account_name if account_name and account_name != "未设置" else account_number
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

    elif data.startswith("payment_edit_info_"):
        # 编辑指定ID的账户信息
        try:
            account_id = int(data.split("_")[-1])
            account = await db_operations.get_payment_account_by_id(account_id)
            if not account:
                await query.answer("❌ 账户不存在", show_alert=True)
                return

            context.user_data["editing_account_id"] = account_id
            account_type = account.get("account_type", "")

            try:
                if query.message:
                    await query.message.reply_text(
                        f"请输入账户信息：\n"
                        f"格式: <账号号码> <账户名称>\n"
                        f"示例: 09171234567 张三\n"
                        f"输入 'cancel' 取消\n\n"
                        f"💡 提示：输入 'delete' 可以删除此账户"
                    )
                else:
                    await query.answer("请输入账户信息", show_alert=True)
            except Exception as e:
                logger.error(f"发送账户信息提示失败: {e}", exc_info=True)
                await query.answer("请输入账户信息", show_alert=True)

            if account_type == "gcash":
                context.user_data["state"] = "EDITING_ACCOUNT_BY_ID_GCASH"
            else:
                context.user_data["state"] = "EDITING_ACCOUNT_BY_ID_PAYMAYA"

            await query.answer()
        except (ValueError, IndexError):
            await query.answer("❌ 无效的账户ID", show_alert=True)
