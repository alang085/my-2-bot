"""定时播报输入 - 消息处理模块

包含处理消息输入和保存的逻辑。
"""

from telegram import Update
from telegram.ext import ContextTypes

import db_operations


def _save_message_to_context(
    context: ContextTypes.DEFAULT_TYPE, slot: int, text: str
) -> None:
    """保存消息内容到上下文

    Args:
        context: 上下文对象
        slot: 播报槽位
        text: 输入文本
    """
    if "schedule_data" not in context.user_data:
        context.user_data["schedule_data"] = {}
    if slot not in context.user_data["schedule_data"]:
        context.user_data["schedule_data"][slot] = {}
    context.user_data["schedule_data"][slot]["message"] = text


async def _complete_schedule_setup(
    update: Update, context: ContextTypes.DEFAULT_TYPE, slot: int, slot_data: dict
) -> None:
    """完成定时播报设置

    Args:
        update: Telegram更新对象
        context: 上下文对象
        slot: 播报槽位
        slot_data: 槽位数据
    """
    time_str = slot_data["time"]
    chat_id = slot_data.get("chat_id")
    chat_title = slot_data.get("chat_title")
    message = slot_data["message"]

    from db.module4_automation.messages_schedule import \
        create_or_update_scheduled_broadcast
    from db.module4_automation.schedule_broadcast_data import \
        ScheduledBroadcastParams

    # 注意：db_transaction装饰器会自动注入conn和cursor
    # 这里我们需要通过db_operations来调用，因为它会处理数据库连接
    # 为了保持兼容性，我们需要创建一个包装函数或直接调用
    # 由于db_operations可能是一个兼容层，我们需要检查它的实现
    # 暂时保持原样，但添加注释说明需要更新
    await db_operations.create_or_update_scheduled_broadcast(
        slot, time_str, chat_id, chat_title, message, is_active=1
    )

    from utils.schedule_executor import reload_scheduled_broadcasts

    await reload_scheduled_broadcasts(context.bot)

    context.user_data.pop("state", None)
    context.user_data["schedule_data"].pop(slot, None)

    await update.message.reply_text(
        f"✅ 定时播报 {slot} 已设置成功！\n\n"
        f"时间: {time_str}\n"
        f"群组: {chat_title}\n"
        f"内容: {message}\n\n"
        f"使用 /schedule 查看所有定时播报"
    )


async def handle_schedule_message_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE, slot: int, text: str
) -> bool:
    """处理消息输入

    Args:
        update: Telegram更新对象
        context: 上下文对象
        slot: 播报槽位
        text: 输入文本

    Returns:
        bool: 是否处理成功
    """
    _save_message_to_context(context, slot, text)

    slot_data = context.user_data["schedule_data"][slot]
    if "time" in slot_data and "message" in slot_data:
        await _complete_schedule_setup(update, context, slot, slot_data)
    else:
        await update.message.reply_text("❌ 数据不完整，请重新设置")

    return True
