"""管理员数据修正处理器"""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

import db_operations
from config import ADMIN_IDS
from decorators import admin_required, error_handler, private_chat_only
from handlers.module5_data.daily_operations_handlers import (
    format_operation_detail, format_operation_type)
from utils.date_helpers import get_daily_period_date

logger = logging.getLogger(__name__)


@error_handler
@private_chat_only
@admin_required
async def admin_correct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """管理员数据修正命令 - 查看、修改、删除操作历史记录"""
    from handlers.module5_data.admin_correction_delete import \
        handle_admin_correction_delete
    from handlers.module5_data.admin_correction_help import \
        show_admin_correction_help
    from handlers.module5_data.admin_correction_list import \
        handle_admin_correction_list
    from handlers.module5_data.admin_correction_modify import \
        handle_admin_correction_modify
    from handlers.module5_data.admin_correction_view import \
        handle_admin_correction_view

    if not context.args:
        await show_admin_correction_help(update, context)
        return

    command = context.args[0].lower()

    if command == "list":
        await handle_admin_correction_list(update, context)
    elif command == "view":
        await handle_admin_correction_view(update, context)
    elif command == "delete":
        await handle_admin_correction_delete(update, context)
    elif command == "modify":
        await handle_admin_correction_modify(update, context)
    else:
        await update.message.reply_text(
            f"❌ 未知命令: {command}\n使用 /admin_correct 查看帮助"
        )


async def _handle_admin_correct_refresh(
    query, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """处理刷新操作列表"""
    await query.answer("🔄 刷新中...")
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

    keyboard.append(
        [InlineKeyboardButton("🔄 刷新", callback_data="admin_correct_refresh")]
    )
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))


async def _handle_admin_correct_view(query) -> None:
    """处理查看操作详情"""
    try:
        operation_id = int(query.data.split("_")[-1])
        operation = await db_operations.get_operation_by_id(operation_id)

        if not operation:
            await query.answer("❌ 操作记录不存在", show_alert=True)
            return

        msg = format_operation_detail(operation)
        await query.answer()
        await query.message.reply_text(msg)
    except (ValueError, IndexError):
        await query.answer("❌ 无效的操作ID", show_alert=True)


async def _handle_admin_correct_delete(
    query, user_id: int, update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """处理删除操作记录"""
    try:
        operation_id = int(query.data.split("_")[-1])
        operation = await db_operations.get_operation_by_id(operation_id)

        if not operation:
            await query.answer("❌ 操作记录不存在", show_alert=True)
            return

        success = await db_operations.delete_operation(operation_id)

        if success:
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


async def handle_admin_correction_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
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
        await _handle_admin_correct_refresh(query, context)
    elif data.startswith("admin_correct_view_"):
        await _handle_admin_correct_view(query)
    elif data.startswith("admin_correct_delete_"):
        await _handle_admin_correct_delete(query, user_id, update, context)


async def _handle_confirm_delete_operation(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str
) -> None:
    """处理确认删除操作"""
    if text.strip().lower() not in ["确认删除", "confirm", "yes"]:
        await update.message.reply_text("❌ 已取消删除操作")
        context.user_data["state"] = None
        context.user_data.pop("pending_delete_operation_id", None)
        return

    operation_id = context.user_data.get("pending_delete_operation_id")
    if not operation_id:
        await update.message.reply_text("❌ 未找到待删除的操作记录")
        context.user_data["state"] = None
        context.user_data.pop("pending_delete_operation_id", None)
        return

    operation = await db_operations.get_operation_by_id(operation_id)
    if not operation:
        await update.message.reply_text(f"❌ 操作记录不存在")
        context.user_data["state"] = None
        context.user_data.pop("pending_delete_operation_id", None)
        return

    success = await db_operations.delete_operation(operation_id)
    if success:
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
                chat_id=update.effective_chat.id if update.effective_chat else user_id,
            )
        await update.message.reply_text(f"✅ 操作记录 {operation_id} 已删除")
    else:
        await update.message.reply_text(f"❌ 删除失败")

    context.user_data["state"] = None
    context.user_data.pop("pending_delete_operation_id", None)


async def _handle_modify_operation(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str
) -> None:
    """处理修改操作"""
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
                    chat_id=(
                        update.effective_chat.id if update.effective_chat else user_id
                    ),
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


async def handle_admin_correction_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str
):
    """处理管理员数据修正的文本输入"""
    user_state = context.user_data.get("state")

    if user_state == "ADMIN_CONFIRM_DELETE_OPERATION":
        await _handle_confirm_delete_operation(update, context, text)
    elif user_state == "ADMIN_MODIFY_OPERATION":
        await _handle_modify_operation(update, context, text)
