"""定时播报处理器"""

import logging
from typing import Dict, List, Optional, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

import db_operations

logger = logging.getLogger(__name__)


def _build_slots_dict(broadcasts: List[Dict]) -> Dict[int, Optional[Dict]]:
    """构建槽位字典

    Args:
        broadcasts: 播报列表

    Returns:
        槽位字典
    """
    slots = {1: None, 2: None, 3: None}
    for broadcast in broadcasts:
        slots[broadcast["slot"]] = broadcast
    return slots


def _format_broadcast_info(broadcast: Optional[Dict]) -> Tuple[str, str, str, str]:
    """格式化播报信息

    Args:
        broadcast: 播报字典

    Returns:
        (状态, 时间, 群组, 内容预览)
    """
    if broadcast and broadcast["is_active"]:
        status = "✅ 激活"
        time_str = broadcast["time"]
        if broadcast["chat_title"]:
            chat_str = broadcast["chat_title"]
        elif broadcast["chat_id"]:
            chat_str = f"群组ID: {broadcast['chat_id']}"
        else:
            chat_str = "未设置"
        msg_preview = (
            broadcast["message"][:20] + "..."
            if len(broadcast["message"]) > 20
            else broadcast["message"]
        )
    else:
        status = "❌ 未设置"
        time_str = "未设置"
        chat_str = "未设置"
        msg_preview = "未设置"

    return status, time_str, chat_str, msg_preview


def _build_schedule_message(slots: Dict[int, Optional[Dict]]) -> str:
    """构建定时播报菜单消息

    Args:
        slots: 槽位字典

    Returns:
        消息文本
    """
    message = "⏰ 定时播报管理\n\n"
    for slot in [1, 2, 3]:
        broadcast = slots[slot]
        status, time_str, chat_str, msg_preview = _format_broadcast_info(broadcast)

        message += f"📌 播报 {slot}:\n"
        message += f"   状态: {status}\n"
        message += f"   时间: {time_str}\n"
        message += f"   群组: {chat_str}\n"
        message += f"   内容: {msg_preview}\n\n"

    return message


def _build_schedule_keyboard(
    slots: Dict[int, Optional[Dict]],
) -> List[List[InlineKeyboardButton]]:
    """构建定时播报菜单键盘

    Args:
        slots: 槽位字典

    Returns:
        键盘按钮列表
    """
    keyboard = []
    for slot in [1, 2, 3]:
        broadcast = slots[slot]
        if broadcast:
            button_text = (
                f"编辑播报 {slot}" if broadcast["is_active"] else f"设置播报 {slot}"
            )
        else:
            button_text = f"设置播报 {slot}"
        keyboard.append(
            [InlineKeyboardButton(button_text, callback_data=f"schedule_setup_{slot}")]
        )

    keyboard.append([InlineKeyboardButton("刷新", callback_data="schedule_refresh")])
    return keyboard


async def show_schedule_menu(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """显示定时播报菜单"""
    broadcasts = await db_operations.get_all_scheduled_broadcasts()
    slots = _build_slots_dict(broadcasts)
    message = _build_schedule_message(slots)
    keyboard = _build_schedule_keyboard(slots)

    await update.message.reply_text(
        message, reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_schedule_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理定时播报的文本输入"""
    from handlers.module4_automation.schedule_chat import \
        handle_schedule_chat_input
    from handlers.module4_automation.schedule_message import \
        handle_schedule_message_input
    from handlers.module4_automation.schedule_time import \
        handle_schedule_time_input

    user_state = context.user_data.get("state", "")

    if not user_state.startswith("SCHEDULE_"):
        return False

    # 解析状态：SCHEDULE_TIME_1, SCHEDULE_CHAT_1, SCHEDULE_MESSAGE_1
    parts = user_state.split("_")
    if len(parts) < 3:
        return False

    field = parts[1]  # TIME, CHAT, MESSAGE
    slot = int(parts[2])  # 1, 2, 3

    text = update.message.text.strip()

    # 处理不同类型的输入
    if field == "TIME":
        return await handle_schedule_time_input(update, context, slot, text)
    elif field == "CHAT":
        return await handle_schedule_chat_input(update, context, slot, text)
    elif field == "MESSAGE":
        return await handle_schedule_message_input(update, context, slot, text)

    return False
