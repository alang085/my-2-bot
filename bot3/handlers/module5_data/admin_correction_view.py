"""管理员数据修正 - 查看模块

包含查看操作详情的逻辑。
"""

from telegram import Update
from telegram.ext import ContextTypes

import db_operations
from handlers.module5_data.daily_operations_handlers import \
    format_operation_detail


async def handle_admin_correction_view(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """处理查看操作详情的命令

    Args:
        update: Telegram 更新对象
        context: 上下文对象
    """
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ 请提供操作ID\n用法: /admin_correct view <操作ID>"
        )
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
