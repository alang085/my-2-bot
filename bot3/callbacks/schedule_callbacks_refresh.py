"""定时播报回调处理器 - 刷新模块

包含刷新菜单相关的回调处理逻辑。
"""

from typing import Any, Dict

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from handlers.data_access import get_all_scheduled_broadcasts_for_callback


async def handle_schedule_refresh(query) -> None:
    """处理刷新菜单回调"""
    broadcasts = await get_all_scheduled_broadcasts_for_callback()

    slots: Dict[int, Any] = {1: None, 2: None, 3: None}
    for broadcast in broadcasts:
        slots[broadcast["slot"]] = broadcast

    message = "⏰ 定时播报管理\n\n"
    for slot in [1, 2, 3]:
        broadcast = slots[slot]
        if broadcast and broadcast["is_active"]:
            status = "✅ 激活"
            time_str = broadcast["time"]
            chat_str = _get_chat_display_text(broadcast)
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

        message += f"📌 播报 {slot}:\n"
        message += f"   状态: {status}\n"
        message += f"   时间: {time_str}\n"
        message += f"   群组: {chat_str}\n"
        message += f"   内容: {msg_preview}\n\n"

    keyboard = _build_refresh_keyboard(slots)
    await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard))


def _get_chat_display_text(broadcast: Dict[str, Any]) -> str:
    """获取群组显示文本"""
    if broadcast["chat_title"]:
        return broadcast["chat_title"]
    elif broadcast["chat_id"]:
        return f"群组ID: {broadcast['chat_id']}"
    else:
        return "未设置"


def _build_refresh_keyboard(slots: Dict[int, Any]) -> list:
    """构建刷新菜单键盘"""
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
