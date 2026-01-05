"""开始页面 - 发送模块

包含发送管理员命令消息的逻辑。
"""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)


async def send_admin_commands_message(query, message: str) -> None:
    """发送管理员命令消息

    Args:
        query: 回调查询对象
        message: 消息文本
    """
    # 使用内联按钮隐藏管理员命令
    keyboard = [
        [
            InlineKeyboardButton(
                "🔒 隐藏管理员命令", callback_data="start_hide_admin_commands"
            )
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(message, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"编辑消息失败: {e}", exc_info=True)
        await query.answer("显示失败", show_alert=True)
