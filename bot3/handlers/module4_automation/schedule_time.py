"""定时播报输入 - 时间处理模块

包含处理时间输入的逻辑。
"""

from telegram import Update
from telegram.ext import ContextTypes

from utils.validation_helpers import validate_time_format


async def handle_schedule_time_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE, slot: int, text: str
) -> bool:
    """处理时间输入

    Args:
        update: Telegram更新对象
        context: 上下文对象
        slot: 播报槽位
        text: 输入文本

    Returns:
        bool: 是否处理成功
    """
    # 验证时间格式
    is_valid, time_str, error_msg = validate_time_format(text)
    if not is_valid:
        await update.message.reply_text(error_msg or "❌ 时间格式错误")
        return True

    # 保存时间
    if "schedule_data" not in context.user_data:
        context.user_data["schedule_data"] = {}
    if slot not in context.user_data["schedule_data"]:
        context.user_data["schedule_data"][slot] = {}
    context.user_data["schedule_data"][slot]["time"] = time_str

    await update.message.reply_text(
        f"✅ 时间已设置为: {time_str}\n\n请选择或输入群组："
    )
    context.user_data["state"] = f"SCHEDULE_CHAT_{slot}"
    return True
