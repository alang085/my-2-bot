"""管理员数据修正 - 列表模块

包含列出操作历史的逻辑。
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

import db_operations
from handlers.module5_data.daily_operations_handlers import \
    format_operation_type
from utils.date_helpers import get_daily_period_date


async def handle_admin_correction_list(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """处理列出操作历史的命令

    Args:
        update: Telegram 更新对象
        context: 上下文对象
    """
    date = context.args[1] if len(context.args) > 1 else get_daily_period_date()
    user_id = int(context.args[2]) if len(context.args) > 2 else None
    operation_type = context.args[3] if len(context.args) > 3 else None

    operations = await db_operations.get_operations_by_filters(
        date=date, user_id=user_id, operation_type=operation_type, limit=50
    )

    if not operations:
        await update.message.reply_text(f"❌ 未找到符合条件的操作记录")
        return

    msg = _build_list_message(operations, date, user_id, operation_type)
    keyboard = _build_list_keyboard(operations)

    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))


def _build_list_message(
    operations: list, date: str, user_id: int = None, operation_type: str = None
) -> str:
    """构建列表消息

    Args:
        operations: 操作列表
        date: 日期
        user_id: 用户ID
        operation_type: 操作类型

    Returns:
        str: 消息内容
    """
    msg = f"📋 操作历史记录（共 {len(operations)} 条）\n\n"
    msg += f"日期: {date}\n"
    if user_id:
        msg += f"用户ID: {user_id}\n"
    if operation_type:
        msg += f"操作类型: {operation_type}\n"
    msg += "\n"

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

    if len(operations) > 20:
        msg += f"\n... 还有 {len(operations) - 20} 条记录未显示"

    return msg


def _build_list_keyboard(operations: list) -> list:
    """构建列表键盘

    Args:
        operations: 操作列表

    Returns:
        list: 键盘按钮列表
    """
    keyboard = []
    for op in operations[:20]:  # 只显示前20条
        op_id = op.get("id")
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
    return keyboard
