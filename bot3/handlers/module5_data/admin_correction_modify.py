"""管理员数据修正 - 修改模块

包含修改操作数据的逻辑。
"""

from telegram import Update
from telegram.ext import ContextTypes

import db_operations
from handlers.module5_data.daily_operations_handlers import \
    format_operation_detail


async def handle_admin_correction_modify(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """处理修改操作数据的命令

    Args:
        update: Telegram 更新对象
        context: 上下文对象
    """
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ 请提供操作ID\n用法: /admin_correct modify <操作ID>"
        )
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

        msg = f"📝 修改操作记录 {operation_id}\n\n"
        msg += f"当前操作数据：\n"
        msg += format_operation_detail(operation)
        msg += "\n\n请输入新的操作数据（JSON格式）：\n"
        msg += '示例：{"amount": 1000, "group_id": "A"}\n'
        msg += "输入 'cancel' 取消"

        await update.message.reply_text(msg)
    except ValueError:
        await update.message.reply_text("❌ 操作ID必须是数字")
