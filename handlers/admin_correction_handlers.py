"""管理员数据修正处理器"""

import logging
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

import db_operations
from config import ADMIN_IDS
from decorators import admin_required, error_handler, private_chat_only
from handlers.daily_operations_handlers import format_operation_detail, format_operation_type
from utils.date_helpers import get_daily_period_date

logger = logging.getLogger(__name__)


@error_handler
@private_chat_only
@admin_required
async def admin_correct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """管理员数据修正命令 - 查看、修改、删除操作历史记录"""
    if not context.args:
        # 显示帮助信息
        await update.message.reply_text(
            "🔧 管理员数据修正工具\n\n"
            "用法：\n"
            "/admin_correct list [日期] [用户ID] [操作类型]\n"
            "  查看操作历史记录\n"
            "  示例：/admin_correct list 2025-01-15\n"
            "  示例：/admin_correct list 2025-01-15 123456789\n"
            "  示例：/admin_correct list 2025-01-15 123456789 interest\n\n"
            "/admin_correct view <操作ID>\n"
            "  查看指定操作的详细信息\n\n"
            "/admin_correct delete <操作ID>\n"
            "  删除指定操作记录（会同步回滚相关统计数据）\n\n"
            "/admin_correct modify <操作ID>\n"
            "  修改指定操作的数据\n\n"
            "⚠️ 警告：此功能会直接修改历史数据，请谨慎使用！"
        )
        return

    command = context.args[0].lower()

    if command == "list":
        # 列出操作历史
        date = context.args[1] if len(context.args) > 1 else get_daily_period_date()
        user_id = int(context.args[2]) if len(context.args) > 2 else None
        operation_type = context.args[3] if len(context.args) > 3 else None

        operations = await db_operations.get_operations_by_filters(
            date=date, user_id=user_id, operation_type=operation_type, limit=50
        )

        if not operations:
            await update.message.reply_text(f"❌ 未找到符合条件的操作记录")
            return

        msg = f"📋 操作历史记录（共 {len(operations)} 条）\n\n"
        msg += f"日期: {date}\n"
        if user_id:
            msg += f"用户ID: {user_id}\n"
        if operation_type:
            msg += f"操作类型: {operation_type}\n"
        msg += "\n"

        keyboard = []
        for op in operations[:20]:  # 只显示前20条
            op_id = op.get("id")
            op_type = op.get("operation_type", "unknown")
            op_data = op.get("operation_data", {})
            created_at = op.get("created_at", "")
            is_undone = op.get("is_undone", 0)

            status = "❌ 已撤销" if is_undone else "✅"
            type_name = format_operation_type(op_type)

            # 显示金额（如果有）
            amount = op_data.get("amount", "")
            amount_str = f" {amount:,.2f}" if isinstance(amount, (int, float)) else ""

            msg += f"{status} [{op_id}] {type_name}{amount_str}\n"
            msg += f"   时间: {created_at}\n"
            msg += f"   用户: {op.get('user_id', 'N/A')}\n\n"

            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"查看 [{op_id}]", callback_data=f"admin_correct_view_{op_id}"
                    ),
                    InlineKeyboardButton(
                        f"删除 [{op_id}]", callback_data=f"admin_correct_delete_{op_id}"
                    ),
                ]
            )

        if len(operations) > 20:
            msg += f"\n... 还有 {len(operations) - 20} 条记录未显示"

        keyboard.append([InlineKeyboardButton("🔄 刷新", callback_data="admin_correct_refresh")])

        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

    elif command == "view":
        if len(context.args) < 2:
            await update.message.reply_text("❌ 请提供操作ID\n用法: /admin_correct view <操作ID>")
            return

        try:
            operation_id = int(context.args[1])
            operation = await db_operations.get_operation_by_id(operation_id)

            if not operation:
                await update.message.reply_text(f"❌ 操作记录 {operation_id} 不存在")
                return

            msg = format_operation_detail(operation)
            await update.message.reply_text(msg)
        except ValueError:
            await update.message.reply_text("❌ 操作ID必须是数字")

    elif command == "delete":
        if len(context.args) < 2:
            await update.message.reply_text("❌ 请提供操作ID\n用法: /admin_correct delete <操作ID>")
            return

        try:
            operation_id = int(context.args[1])
            operation = await db_operations.get_operation_by_id(operation_id)

            if not operation:
                await update.message.reply_text(f"❌ 操作记录 {operation_id} 不存在")
                return

            # 显示确认信息
            op_type = format_operation_type(operation.get("operation_type", "unknown"))
            msg = f"⚠️ 确认删除操作记录？\n\n"
            msg += f"操作ID: {operation_id}\n"
            msg += f"操作类型: {op_type}\n"
            msg += f"创建时间: {operation.get('created_at', 'N/A')}\n\n"
            msg += "此操作不可恢复！\n"
            msg += "回复 '确认删除' 以确认删除"

            context.user_data["pending_delete_operation_id"] = operation_id
            context.user_data["state"] = "ADMIN_CONFIRM_DELETE_OPERATION"

            await update.message.reply_text(msg)
        except ValueError:
            await update.message.reply_text("❌ 操作ID必须是数字")

    elif command == "modify":
        if len(context.args) < 2:
            await update.message.reply_text("❌ 请提供操作ID\n用法: /admin_correct modify <操作ID>")
            return

        try:
            operation_id = int(context.args[1])
            operation = await db_operations.get_operation_by_id(operation_id)

            if not operation:
                await update.message.reply_text(f"❌ 操作记录 {operation_id} 不存在")
                return

            # 进入修改模式
            context.user_data["modifying_operation_id"] = operation_id
            context.user_data["state"] = "ADMIN_MODIFY_OPERATION"

            op_data = operation.get("operation_data", {})
            msg = f"📝 修改操作记录 {operation_id}\n\n"
            msg += f"当前操作数据：\n"
            msg += format_operation_detail(operation)
            msg += "\n\n请输入新的操作数据（JSON格式）：\n"
            msg += '示例：{"amount": 1000, "group_id": "A"}\n'
            msg += "输入 'cancel' 取消"

            await update.message.reply_text(msg)
        except ValueError:
            await update.message.reply_text("❌ 操作ID必须是数字")

    else:
        await update.message.reply_text(f"❌ 未知命令: {command}\n使用 /admin_correct 查看帮助")


async def handle_admin_correction_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理管理员数据修正的回调"""
    query = update.callback_query
    if not query:
        return

    user_id = query.from_user.id if query.from_user else None
    if not user_id or user_id not in ADMIN_IDS:
        await query.answer("❌ 仅管理员可使用此功能", show_alert=True)
        return

    data = query.data

    if data == "admin_correct_refresh":
        await query.answer("🔄 刷新中...")
        # 重新显示列表（需要从上下文获取之前的筛选条件）
        # 这里简化处理，直接显示今天的记录
        date = get_daily_period_date()
        operations = await db_operations.get_operations_by_filters(date=date, limit=50)

        if not operations:
            await query.edit_message_text("❌ 未找到操作记录")
            return

        msg = f"📋 操作历史记录（共 {len(operations)} 条）\n\n"
        msg += f"日期: {date}\n\n"

        keyboard = []
        for op in operations[:20]:
            op_id = op.get("id")
            op_type = format_operation_type(op.get("operation_type", "unknown"))
            is_undone = op.get("is_undone", 0)
            status = "❌ 已撤销" if is_undone else "✅"

            msg += f"{status} [{op_id}] {op_type}\n"
            msg += f"   时间: {op.get('created_at', '')}\n\n"

            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"查看 [{op_id}]", callback_data=f"admin_correct_view_{op_id}"
                    ),
                    InlineKeyboardButton(
                        f"删除 [{op_id}]", callback_data=f"admin_correct_delete_{op_id}"
                    ),
                ]
            )

        keyboard.append([InlineKeyboardButton("🔄 刷新", callback_data="admin_correct_refresh")])

        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("admin_correct_view_"):
        try:
            operation_id = int(data.split("_")[-1])
            operation = await db_operations.get_operation_by_id(operation_id)

            if not operation:
                await query.answer("❌ 操作记录不存在", show_alert=True)
                return

            msg = format_operation_detail(operation)
            await query.answer()
            await query.message.reply_text(msg)
        except (ValueError, IndexError):
            await query.answer("❌ 无效的操作ID", show_alert=True)

    elif data.startswith("admin_correct_delete_"):
        try:
            operation_id = int(data.split("_")[-1])
            operation = await db_operations.get_operation_by_id(operation_id)

            if not operation:
                await query.answer("❌ 操作记录不存在", show_alert=True)
                return

            # 直接删除（管理员操作不需要二次确认）
            success = await db_operations.delete_operation(operation_id)

            if success:
                # 记录修正操作
                await db_operations.record_operation(
                    user_id=user_id,
                    operation_type="operation_deleted",
                    operation_data={
                        "deleted_operation_id": operation_id,
                        "deleted_operation_type": operation.get("operation_type"),
                        "deleted_operation_data": operation.get("operation_data", {}),
                    },
                    chat_id=query.message.chat_id if query.message else user_id,
                )

                await query.answer("✅ 操作记录已删除")
                # 刷新列表
                await handle_admin_correction_callback(update, context)
            else:
                await query.answer("❌ 删除失败", show_alert=True)
        except (ValueError, IndexError):
            await query.answer("❌ 无效的操作ID", show_alert=True)


async def handle_admin_correction_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str
):
    """处理管理员数据修正的文本输入"""
    user_state = context.user_data.get("state")

    if user_state == "ADMIN_CONFIRM_DELETE_OPERATION":
        if text.strip().lower() in ["确认删除", "confirm", "yes"]:
            operation_id = context.user_data.get("pending_delete_operation_id")
            if operation_id:
                operation = await db_operations.get_operation_by_id(operation_id)
                if operation:
                    success = await db_operations.delete_operation(operation_id)
                    if success:
                        # 记录修正操作
                        user_id = update.effective_user.id if update.effective_user else None
                        if user_id:
                            await db_operations.record_operation(
                                user_id=user_id,
                                operation_type="operation_deleted",
                                operation_data={
                                    "deleted_operation_id": operation_id,
                                    "deleted_operation_type": operation.get("operation_type"),
                                    "deleted_operation_data": operation.get("operation_data", {}),
                                },
                                chat_id=(
                                    update.effective_chat.id if update.effective_chat else user_id
                                ),
                            )
                        await update.message.reply_text(f"✅ 操作记录 {operation_id} 已删除")
                    else:
                        await update.message.reply_text(f"❌ 删除失败")
                else:
                    await update.message.reply_text(f"❌ 操作记录不存在")
            else:
                await update.message.reply_text("❌ 未找到待删除的操作记录")
        else:
            await update.message.reply_text("❌ 已取消删除操作")

        context.user_data["state"] = None
        context.user_data.pop("pending_delete_operation_id", None)

    elif user_state == "ADMIN_MODIFY_OPERATION":
        if text.strip().lower() == "cancel":
            await update.message.reply_text("❌ 已取消修改")
            context.user_data["state"] = None
            context.user_data.pop("modifying_operation_id", None)
            return

        try:
            import json

            new_data = json.loads(text.strip())

            operation_id = context.user_data.get("modifying_operation_id")
            if not operation_id:
                await update.message.reply_text("❌ 未找到待修改的操作记录")
                context.user_data["state"] = None
                return

            success = await db_operations.update_operation_data(operation_id, new_data)
            if success:
                # 记录修正操作
                user_id = update.effective_user.id if update.effective_user else None
                if user_id:
                    operation = await db_operations.get_operation_by_id(operation_id)
                    await db_operations.record_operation(
                        user_id=user_id,
                        operation_type="operation_modified",
                        operation_data={
                            "modified_operation_id": operation_id,
                            "old_operation_data": (
                                operation.get("operation_data", {}) if operation else {}
                            ),
                            "new_operation_data": new_data,
                        },
                        chat_id=update.effective_chat.id if update.effective_chat else user_id,
                    )
                await update.message.reply_text(f"✅ 操作记录 {operation_id} 已修改")
            else:
                await update.message.reply_text("❌ 修改失败")
        except json.JSONDecodeError:
            await update.message.reply_text("❌ JSON格式错误，请检查输入")
        except Exception as e:
            logger.error(f"修改操作记录失败: {e}", exc_info=True)
            await update.message.reply_text(f"❌ 修改失败: {str(e)}")

        context.user_data["state"] = None
        context.user_data.pop("modifying_operation_id", None)
