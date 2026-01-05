"""管理员数据修正 - 删除模块

包含删除操作记录的逻辑。
"""

from telegram import Update
from telegram.ext import ContextTypes

import db_operations
from handlers.module5_data.daily_operations_handlers import \
    format_operation_type


async def handle_admin_correction_delete(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """处理删除操作记录的命令

    Args:
        update: Telegram 更新对象
        context: 上下文对象
    """
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ 请提供操作ID\n用法: /admin_correct delete <操作ID>"
        )
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
