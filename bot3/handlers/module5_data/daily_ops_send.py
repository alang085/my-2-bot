"""每日操作记录 - 消息发送模块

包含发送操作记录消息的逻辑。
"""

from typing import List

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes


async def send_full_operations(
    update: Update, message_parts: List[str], date: str
) -> None:
    """发送完整操作记录（分段）

    Args:
        update: Telegram更新对象
        message_parts: 消息分段列表
        date: 日期字符串
    """
    for i, part in enumerate(message_parts, 1):
        if i == 1:
            # 第一段添加按钮
            keyboard = [
                [
                    InlineKeyboardButton(
                        "🔄 还原当天数据", callback_data=f"restore_daily_data_{date}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📊 查看汇总", callback_data=f"daily_ops_summary_{date}"
                    )
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(part, reply_markup=reply_markup)
        else:
            await update.message.reply_text(part)


async def send_summary_operations(update: Update, message: str, date: str) -> None:
    """发送摘要操作记录（前50条）

    Args:
        update: Telegram更新对象
        message: 消息文本
        date: 日期字符串
    """
    keyboard = [
        [
            InlineKeyboardButton(
                "📋 显示完整记录", callback_data=f"show_all_operations_{date}"
            )
        ],
        [
            InlineKeyboardButton(
                "🔄 还原当天数据", callback_data=f"restore_daily_data_{date}"
            )
        ],
        [
            InlineKeyboardButton(
                "📊 查看汇总", callback_data=f"daily_ops_summary_{date}"
            )
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(message, reply_markup=reply_markup)
