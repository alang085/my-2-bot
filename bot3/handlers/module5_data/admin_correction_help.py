"""管理员数据修正 - 帮助模块

包含显示帮助信息的逻辑。
"""

from telegram import Update
from telegram.ext import ContextTypes


async def show_admin_correction_help(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """显示管理员数据修正工具的帮助信息

    Args:
        update: Telegram 更新对象
        context: 上下文对象
    """
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
