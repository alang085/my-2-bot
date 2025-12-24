"""主回调处理器"""

# 标准库
import logging

# 第三方库
from telegram import Update
from telegram.ext import ContextTypes

# 本地模块
import db_operations
from callbacks.payment_callbacks import handle_payment_callback
from callbacks.report_callbacks import handle_report_callback
from callbacks.search_callbacks import handle_search_callback

logger = logging.getLogger(__name__)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """主按钮回调入口"""
    query = update.callback_query
    data = query.data

    # 获取用户ID
    user_id = update.effective_user.id if update.effective_user else None

    # 对于报表回调、收入明细回调和订单总表回调，允许受限用户使用（只要他们有 user_group_id）
    # 权限检查在各自的回调处理器内部进行
    if data.startswith("report_") or data.startswith("income_") or data.startswith("order_table_"):
        if data.startswith("report_"):
            callback_name = "handle_report_callback"
            handler = handle_report_callback
        elif data.startswith("order_table_"):
            # 订单总表回调已集成在 report_callbacks 中，路由到报表回调处理器
            callback_name = "handle_report_callback (order_table)"
            handler = handle_report_callback
        else:
            # 收入明细回调已集成在 report_callbacks 中，路由到报表回调处理器
            callback_name = "handle_report_callback (income)"
            handler = handle_report_callback

        logger.info(f"button_callback: routing {data} to {callback_name}")
        try:
            await handler(update, context)
        except Exception as e:
            logger.error(f"button_callback: error in {callback_name}: {e}", exc_info=True)
            try:
                await query.answer("❌ 处理回调时出错", show_alert=True)
            except Exception:
                pass
        return

    # 其他回调需要授权（管理员或员工）
    from decorators import authorized_required

    # 检查是否是管理员或授权员工
    if not user_id:
        await query.answer("❌ 无法获取用户信息", show_alert=True)
        return

    from config import ADMIN_IDS

    is_admin = user_id in ADMIN_IDS
    is_authorized = await db_operations.is_user_authorized(user_id)

    if not is_admin and not is_authorized:
        await query.answer("⚠️ Permission denied.", show_alert=True)
        return

    # 必须先 answer，防止客户端转圈
    try:
        await query.answer()
    except Exception:
        pass  # 忽略 answer 错误（例如 query 已过期）

    # 记录日志以便排查
    logger.info(f"Processing callback: {data} from user {update.effective_user.id}")

    if data.startswith("search_"):
        await handle_search_callback(update, context)
    elif data.startswith("payment_"):
        await handle_payment_callback(update, context)
    elif data.startswith("merge_incremental_"):
        from callbacks.incremental_merge_callbacks import handle_incremental_merge_callback

        await handle_incremental_merge_callback(update, context)
    elif data == "broadcast_start":
        locked_groups = context.user_data.get("locked_groups", [])
        if not locked_groups:
            try:
                if query.message:
                    await query.message.reply_text("⚠️ 没有锁定的群组。请先使用查找功能锁定群组。")
                else:
                    await query.answer(
                        "⚠️ 没有锁定的群组。请先使用查找功能锁定群组。", show_alert=True
                    )
            except Exception as e:
                logger.error(f"发送锁定群组提示失败: {e}", exc_info=True)
                await query.answer("⚠️ 没有锁定的群组", show_alert=True)
            return

        try:
            if query.message:
                await query.message.reply_text(
                    f"📢 准备向 {len(locked_groups)} 个群组发送消息。\n"
                    "请输入消息内容：\n"
                    "（输入 'cancel' 取消）"
                )
            else:
                await query.answer("请输入消息内容", show_alert=True)
        except Exception as e:
            logger.error(f"发送播报提示失败: {e}", exc_info=True)
            await query.answer("请输入消息内容", show_alert=True)
        context.user_data["state"] = "BROADCASTING"
    elif data == "broadcast_send_12":
        # 处理发送本金12%版本
        principal_12 = context.user_data.get("broadcast_principal_12", 0)
        outstanding_interest = context.user_data.get("broadcast_outstanding_interest", 0)
        date_str = context.user_data.get("broadcast_date_str", "")
        weekday_str = context.user_data.get("broadcast_weekday_str", "Friday")

        if principal_12 == 0:
            from utils.chat_helpers import is_group_chat

            is_group = is_group_chat(update)
            msg = "❌ Data error" if is_group else "❌ 数据错误"
            await query.answer(msg, show_alert=True)
            return

        # 使用统一的播报模板函数
        # 本金12%版本：只显示本金12%金额
        from utils.broadcast_helpers import format_broadcast_message

        message = format_broadcast_message(
            principal=principal_12,  # 本金12%版本，只显示这个金额
            principal_12=principal_12,
            outstanding_interest=outstanding_interest,
            date_str=date_str,
            weekday_str=weekday_str,
        )

        try:
            from utils.chat_helpers import is_group_chat

            is_group = is_group_chat(update)
            await context.bot.send_message(chat_id=query.message.chat_id, text=message)
            success_msg = "✅ 12% version sent" if is_group else "✅ 本金12%版本已发送"
            await query.answer(success_msg)
            done_msg = "✅ Broadcast completed" if is_group else "✅ 播报完成"
            await query.edit_message_text(done_msg)
            # 清除临时数据
            context.user_data.pop("broadcast_principal_12", None)
            context.user_data.pop("broadcast_outstanding_interest", None)
            context.user_data.pop("broadcast_date_str", None)
            context.user_data.pop("broadcast_weekday_str", None)
        except Exception as e:
            logger.error(f"发送播报消息失败: {e}", exc_info=True)
            from utils.chat_helpers import is_group_chat

            is_group = is_group_chat(update)
            error_msg = f"❌ Send failed: {e}" if is_group else f"❌ 发送失败: {e}"
            await query.answer(error_msg, show_alert=True)
    elif data == "broadcast_done":
        from utils.chat_helpers import is_group_chat

        is_group = is_group_chat(update)
        done_msg = "✅ Broadcast completed" if is_group else "✅ 播报完成"
        await query.answer(done_msg)
        await query.edit_message_text(done_msg)
        # 清除临时数据
        context.user_data.pop("broadcast_principal_12", None)
        context.user_data.pop("broadcast_outstanding_interest", None)
        context.user_data.pop("broadcast_date_str", None)
        context.user_data.pop("broadcast_weekday_str", None)
    elif data == "start_show_admin_commands":
        # 显示管理员命令
        from config import ADMIN_IDS

        user_id = update.effective_user.id if update.effective_user else None
        if not user_id or user_id not in ADMIN_IDS:
            await query.answer("❌ 此功能仅限管理员使用", show_alert=True)
            return

        await query.answer()

        # 获取财务数据
        financial_data = await db_operations.get_financial_data()

        # 员工命令
        employee_commands = (
            "📋 订单管理系统\n\n"
            "💰 当前流动资金: {:.2f}\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💬 群聊命令 (Group Commands)\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "📝 订单操作:\n"
            "/create - 读取群名创建新订单\n"
            "/order - 管理当前订单\n\n"
            "⚡ 快捷操作:\n"
            "+<金额>b - 减少本金\n"
            "+<金额> - 利息收入\n\n"
            "🔄 状态变更:\n"
            "/normal - 设为正常\n"
            "/overdue - 设为逾期\n"
            "/end - 标记为完成\n"
            "/breach - 标记为违约\n"
            "/breach_end - 违约完成\n\n"
            "📢 播报:\n"
            "/broadcast - 播报付款提醒\n\n"
            "🔄 撤销操作:\n"
            "/undo - 撤销上一个操作（最多连续3次）\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💼 私聊命令 (Private Commands)\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "📊 查询:\n"
            "/report [归属ID] - 查看报表\n"
            "/myreport - 查看我的报表（仅限有权限的归属ID）\n"
            "/search <类型> <值> - 搜索订单\n"
            "  类型: order_id/group_id/customer/state/date\n\n"
            "📢 播报:\n"
            "/schedule - 管理定时播报（最多3个）\n\n"
            "💳 支付账号:\n"
            "/accounts - 查看所有账户数据表格\n"
            "/gcash - 查看GCASH账号\n"
            "/paymaya - 查看PayMaya账号\n\n"
            "🔄 撤销操作:\n"
            "/undo - 撤销上一个操作（最多连续3次）\n"
        ).format(financial_data["liquid_funds"])

        # 管理员命令
        admin_commands = (
            "\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "⚙️ 管理员命令 (Admin Commands)\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "📊 高级查询:\n"
            "/ordertable - 订单总表\n"
            "/daily_operations [日期] - 查看操作记录\n"
            "/daily_operations_summary [日期] - 查看操作汇总\n\n"
            "💰 资金管理:\n"
            "/adjust <金额> [备注] - 调整资金\n\n"
            "🏢 归属ID管理:\n"
            "/create_attribution <ID> - 创建归属ID\n"
            "/list_attributions - 列出归属ID\n\n"
            "👥 员工管理:\n"
            "/add_employee <ID> - 添加员工\n"
            "/remove_employee <ID> - 移除员工\n"
            "/list_employees - 列出员工\n\n"
            "🔐 权限管理:\n"
            "/set_user_group_id <用户ID> <归属ID> - 设置用户归属ID权限\n"
            "/remove_user_group_id <用户ID> - 移除用户归属ID权限\n"
            "/list_user_group_mappings - 列出所有用户归属ID映射\n\n"
            "🔧 系统维护:\n"
            "/update_weekday_groups - 更新星期分组\n"
            "/fix_statistics - 修复统计数据\n"
            "/fix_income_statistics - 修复收入统计数据\n"
            "/find_tail_orders - 查找尾数订单\n"
            "/check_mismatch [日期] - 检查收入明细和统计数据不一致\n\n"
            "📝 消息管理:\n"
            "/init_templates [force] - 初始化消息范本\n"
            "/fill_empty_messages - 填充空消息范本\n"
            "/test_broadcast - 测试发送语录\n"
            "/groupmsg - 管理群组消息\n"
            "/announcement - 管理公司公告\n"
            "/antifraud - 管理防诈骗消息\n"
            "/promotion - 管理宣传语录\n"
            "/batch_set_messages - 批量设置消息\n"
        )

        full_message = employee_commands + admin_commands

        # 使用内联按钮隐藏管理员命令
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        keyboard = [
            [InlineKeyboardButton("🔒 隐藏管理员命令", callback_data="start_hide_admin_commands")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            await query.edit_message_text(full_message, reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"编辑消息失败: {e}", exc_info=True)
            await query.answer("显示失败", show_alert=True)

    elif data.startswith("show_all_operations_"):
        # 显示完整操作记录
        date = data.replace("show_all_operations_", "")
        await query.answer("正在加载完整记录...")

        try:
            operations = await db_operations.get_operations_by_date(date)

            if not operations:
                await query.edit_message_text(f"📋 完整操作记录 ({date})\n\n暂无操作记录")
                return

            # 分段发送完整记录
            max_length = 4000
            current_message = f"📋 完整操作记录 ({date})\n"
            current_message += "═══════════════════════════════════════\n"
            current_message += f"总操作数: {len(operations)}\n\n"

            message_parts = [current_message]
            current_part = ""

            from handlers.daily_operations_handlers import format_operation_detail

            for i, op in enumerate(operations, 1):
                op_detail = f"{i}. {format_operation_detail(op)}\n"

                if len(current_part + op_detail) > max_length:
                    message_parts.append(current_part)
                    current_part = op_detail
                else:
                    current_part += op_detail

            if current_part:
                message_parts.append(current_part)

            # 发送第一部分（带按钮）
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup

            keyboard = [
                [
                    InlineKeyboardButton(
                        "🔄 还原当天数据", callback_data=f"restore_daily_data_{date}"
                    )
                ],
                [InlineKeyboardButton("📊 查看汇总", callback_data=f"daily_ops_summary_{date}")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            try:
                await query.edit_message_text(message_parts[0], reply_markup=reply_markup)
            except Exception as e:
                logger.error(f"编辑消息失败: {e}", exc_info=True)
                await query.answer("显示失败", show_alert=True)
                return

            # 发送其余部分
            for part in message_parts[1:]:
                try:
                    await query.message.reply_text(part)
                except Exception as e:
                    logger.error(f"发送消息部分失败: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"显示完整操作记录失败: {e}", exc_info=True)
            await query.answer(f"显示失败: {str(e)[:50]}", show_alert=True)

    elif data.startswith("restore_daily_data_"):
        # 还原当天数据（显示确认）
        date = data.replace("restore_daily_data_", "")
        await query.answer()

        try:
            operations = await db_operations.get_operations_by_date(date)
            valid_operations = [op for op in operations if op.get("is_undone", 0) == 0]

            if not valid_operations:
                await query.edit_message_text(
                    f"📋 操作记录 ({date})\n\n" "所有操作都已被撤销，无需还原"
                )
                return

            operation_count = len(valid_operations)
            message = (
                f"⚠️ 确认还原数据\n\n"
                f"日期: {date}\n"
                f"操作数: {operation_count} 条\n\n"
                f"此操作将按时间倒序撤销该日期的所有操作，还原到该日期开始前的状态。\n\n"
                f"⚠️ 警告：此操作不可恢复！"
            )

            from telegram import InlineKeyboardButton, InlineKeyboardMarkup

            keyboard = [
                [
                    InlineKeyboardButton("✅ 确认还原", callback_data=f"confirm_restore_{date}"),
                    InlineKeyboardButton("❌ 取消", callback_data="cancel_restore"),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            try:
                await query.edit_message_text(message, reply_markup=reply_markup)
            except Exception as e:
                logger.error(f"编辑消息失败: {e}", exc_info=True)
                await query.answer("显示失败", show_alert=True)

        except Exception as e:
            logger.error(f"准备还原数据失败: {e}", exc_info=True)
            await query.answer(f"准备失败: {str(e)[:50]}", show_alert=True)

    elif data.startswith("confirm_restore_"):
        # 确认还原数据
        date = data.replace("confirm_restore_", "")
        await query.answer("正在还原数据，请稍候...")

        try:
            from handlers.restore_handlers import execute_restore_daily_data

            result = await execute_restore_daily_data(date)

            # 记录操作历史
            user_id = query.from_user.id if query.from_user else None
            current_chat_id = query.message.chat.id if query.message else None
            if current_chat_id and user_id:
                await db_operations.record_operation(
                    user_id=user_id,
                    operation_type="daily_data_restored",
                    operation_data={
                        "date": date,
                        "total": result.get("total", 0),
                        "success_count": result.get("success_count", 0),
                        "fail_count": result.get("fail_count", 0),
                    },
                    chat_id=current_chat_id,
                )

            if result["success"]:
                message = (
                    f"✅ 数据还原完成\n\n"
                    f"日期: {date}\n"
                    f"总操作数: {result['total']}\n"
                    f"成功还原: {result['success_count']}\n"
                    f"失败: {result['fail_count']}\n\n"
                    f"所有操作已标记为已撤销"
                )
            else:
                message = (
                    f"⚠️ 数据还原部分完成\n\n"
                    f"日期: {date}\n"
                    f"总操作数: {result['total']}\n"
                    f"成功还原: {result['success_count']}\n"
                    f"失败: {result['fail_count']}\n\n"
                )

                if result["errors"]:
                    message += "错误信息:\n"
                    for error in result["errors"][:5]:
                        message += f"  - {error}\n"
                    if len(result["errors"]) > 5:
                        message += f"  ... 还有 {len(result['errors']) - 5} 个错误\n"

            try:
                await query.edit_message_text(message)
            except Exception as e:
                logger.error(f"编辑消息失败: {e}", exc_info=True)
                await query.answer("还原完成，但显示失败", show_alert=True)

        except Exception as e:
            logger.error(f"还原数据失败: {e}", exc_info=True)
            await query.answer(f"还原失败: {str(e)[:50]}", show_alert=True)

    elif data == "cancel_restore":
        await query.answer("已取消")
        await query.edit_message_text("❌ 还原操作已取消")

    elif data.startswith("daily_ops_summary_"):
        # 查看操作汇总
        date = data.replace("daily_ops_summary_", "")
        await query.answer("正在加载汇总...")

        try:
            from handlers.daily_operations_handlers import show_daily_operations_summary

            # 临时设置context.args来传递日期
            context.args = [date]
            await show_daily_operations_summary(update, context)
            await query.delete_message()
        except Exception as e:
            logger.error(f"显示汇总失败: {e}", exc_info=True)
            await query.answer(f"显示失败: {str(e)[:50]}", show_alert=True)

    elif data == "start_hide_admin_commands":
        # 隐藏管理员命令
        from config import ADMIN_IDS

        user_id = update.effective_user.id if update.effective_user else None
        if not user_id or user_id not in ADMIN_IDS:
            await query.answer("❌ 此功能仅限管理员使用", show_alert=True)
            return

        await query.answer()

        # 获取财务数据
        financial_data = await db_operations.get_financial_data()

        # 只显示员工命令
        employee_commands = (
            "📋 订单管理系统\n\n"
            "💰 当前流动资金: {:.2f}\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💬 群聊命令 (Group Commands)\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "📝 订单操作:\n"
            "/create - 读取群名创建新订单\n"
            "/order - 管理当前订单\n\n"
            "⚡ 快捷操作:\n"
            "+<金额>b - 减少本金\n"
            "+<金额> - 利息收入\n\n"
            "🔄 状态变更:\n"
            "/normal - 设为正常\n"
            "/overdue - 设为逾期\n"
            "/end - 标记为完成\n"
            "/breach - 标记为违约\n"
            "/breach_end - 违约完成\n\n"
            "📢 播报:\n"
            "/broadcast - 播报付款提醒\n\n"
            "🔄 撤销操作:\n"
            "/undo - 撤销上一个操作（最多连续3次）\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💼 私聊命令 (Private Commands)\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "📊 查询:\n"
            "/report [归属ID] - 查看报表\n"
            "/myreport - 查看我的报表（仅限有权限的归属ID）\n"
            "/search <类型> <值> - 搜索订单\n"
            "  类型: order_id/group_id/customer/state/date\n\n"
            "📢 播报:\n"
            "/schedule - 管理定时播报（最多3个）\n\n"
            "💳 支付账号:\n"
            "/accounts - 查看所有账户数据表格\n"
            "/gcash - 查看GCASH账号\n"
            "/paymaya - 查看PayMaya账号\n\n"
            "🔄 撤销操作:\n"
            "/undo - 撤销上一个操作（最多连续3次）\n"
        ).format(financial_data["liquid_funds"])

        # 使用内联按钮显示管理员命令
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        keyboard = [
            [InlineKeyboardButton("🔧 显示管理员命令", callback_data="start_show_admin_commands")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            await query.edit_message_text(employee_commands, reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"编辑消息失败: {e}", exc_info=True)
            await query.answer("隐藏失败", show_alert=True)

    else:
        logger.warning(f"Unhandled callback data: {data}")
        try:
            if query.message:
                await query.message.reply_text(f"⚠️ 未知的操作: {data}")
            else:
                await query.answer("⚠️ 未知的操作", show_alert=True)
        except Exception as e:
            logger.error(f"发送未知操作提示失败: {e}", exc_info=True)
            try:
                await query.answer("⚠️ 未知的操作", show_alert=True)
            except:
                pass
