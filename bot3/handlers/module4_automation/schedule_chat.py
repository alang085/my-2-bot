"""定时播报输入 - 群组处理模块

包含处理群组输入的逻辑。
"""

from telegram import Update
from telegram.ext import ContextTypes


async def handle_schedule_chat_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE, slot: int, text: str
) -> bool:
    """处理群组输入

    Args:
        update: Telegram更新对象
        context: 上下文对象
        slot: 播报槽位
        text: 输入文本

    Returns:
        bool: 是否处理成功
    """
    # 尝试查找群组
    chat_id = None
    chat_title = None

    try:
        # 尝试作为chat_id解析
        chat_id = int(text)
        chat_title = f"群组ID: {chat_id}"
    except ValueError:
        # 作为群名处理
        chat_title = text
        # 尝试从订单中查找匹配的chat_id
        # 这里简化：直接使用输入的文本作为群名

    # 保存群组信息
    if "schedule_data" not in context.user_data:
        context.user_data["schedule_data"] = {}
    if slot not in context.user_data["schedule_data"]:
        context.user_data["schedule_data"][slot] = {}
    context.user_data["schedule_data"][slot]["chat_id"] = chat_id
    context.user_data["schedule_data"][slot]["chat_title"] = chat_title

    await update.message.reply_text(
        f"✅ 群组已设置为: {chat_title}\n\n请输入播报内容："
    )
    context.user_data["state"] = f"SCHEDULE_MESSAGE_{slot}"
    return True
