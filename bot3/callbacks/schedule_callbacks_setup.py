"""定时播报回调处理器 - 设置模块

包含设置播报相关的回调处理逻辑。
"""

from typing import Any, Dict

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from handlers.data_access import get_scheduled_broadcast_for_callback


async def handle_schedule_setup(query, data: str) -> None:
    """处理设置播报回调"""
    slot = int(data.split("_")[-1])

    # 检查是否已有播报
    existing = await get_scheduled_broadcast_for_callback(slot)

    if existing:
        message = _build_edit_message(slot, existing)
    else:
        message = _build_new_setup_message(slot)

    keyboard = _build_setup_keyboard(slot)
    await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard))


def _build_edit_message(slot: int, existing: Dict[str, Any]) -> str:
    """构建编辑消息"""
    message = f"📝 编辑定时播报 {slot}\n\n"
    message += "当前设置:\n"
    message += f"时间: {existing['time']}\n"
    group_display = _get_group_display_text(existing)
    message += f"群组: {group_display}\n"
    message += f"内容: {existing['message']}\n\n"
    message += "请选择要编辑的项："
    return message


def _build_new_setup_message(slot: int) -> str:
    """构建新设置消息"""
    message = f"📝 设置定时播报 {slot}\n\n"
    message += "请按顺序设置以下内容：\n"
    message += "1. 时间（每天的时间点）\n"
    message += "2. 群组（群名或群组ID）\n"
    message += "3. 内容（播报消息）\n\n"
    message += "首先，请输入时间："
    return message


def _get_group_display_text(existing: Dict[str, Any]) -> str:
    """获取群组显示文本"""
    if existing["chat_title"]:
        return existing["chat_title"]
    elif existing["chat_id"]:
        return f"群组ID: {existing['chat_id']}"
    else:
        return "未设置"


def _build_setup_keyboard(slot: int) -> list:
    """构建设置键盘"""
    return [
        [
            InlineKeyboardButton("⏰ 设置时间", callback_data=f"schedule_time_{slot}"),
            InlineKeyboardButton("👥 设置群组", callback_data=f"schedule_chat_{slot}"),
        ],
        [InlineKeyboardButton("📝 设置内容", callback_data=f"schedule_message_{slot}")],
        [
            InlineKeyboardButton(
                "❌ 删除播报", callback_data=f"schedule_delete_{slot}"
            ),
            InlineKeyboardButton("🔙 返回", callback_data="schedule_refresh"),
        ],
    ]
