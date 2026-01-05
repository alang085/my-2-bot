"""定时播报回调处理器 - 输入设置模块

包含时间、群组、内容输入设置相关的回调处理逻辑。
"""

from telegram.ext import ContextTypes


async def handle_schedule_time(
    query, data: str, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """处理设置时间回调"""
    slot = int(data.split("_")[-1])
    context.user_data["state"] = f"SCHEDULE_TIME_{slot}"
    await query.edit_message_text(
        f"⏰ 设置播报 {slot} 的时间\n\n"
        "请输入时间（24小时制）：\n"
        "格式：小时（如 22）或 小时:分钟（如 22:30）\n\n"
        "示例：\n"
        "- 22 （表示22:00）\n"
        "- 22:30 （表示22:30）\n\n"
        "输入 'cancel' 取消"
    )


async def handle_schedule_chat(
    query, data: str, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """处理设置群组回调"""
    slot = int(data.split("_")[-1])
    context.user_data["state"] = f"SCHEDULE_CHAT_{slot}"
    await query.edit_message_text(
        f"👥 设置播报 {slot} 的群组\n\n"
        "请输入群组名称或群组ID：\n\n"
        "示例：\n"
        "- 群组三\n"
        "- -1001234567890 （群组ID）\n\n"
        "输入 'cancel' 取消"
    )


async def handle_schedule_message(
    query, data: str, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """处理设置内容回调"""
    slot = int(data.split("_")[-1])
    context.user_data["state"] = f"SCHEDULE_MESSAGE_{slot}"
    await query.edit_message_text(
        f"📝 设置播报 {slot} 的内容\n\n"
        "请输入要播报的消息内容：\n\n"
        "示例：\n"
        "- 请大家准时换钱 有惊喜\n\n"
        "输入 'cancel' 取消"
    )
