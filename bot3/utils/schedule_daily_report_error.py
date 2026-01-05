"""每日报表 - 错误处理模块

包含错误处理和通知的逻辑。
"""

import logging
from typing import TYPE_CHECKING

from constants import ADMIN_IDS

if TYPE_CHECKING:
    from telegram import Bot

logger = logging.getLogger(__name__)


async def send_error_notification(bot: "Bot", error: Exception) -> None:
    """发送错误通知给管理员

    Args:
        bot: Telegram Bot实例
        error: 错误异常
    """
    try:
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=(
                        f"❌ 每日报表生成失败\n\n错误: {str(error)}\n\n"
                        f"请检查日志获取详细信息"
                    ),
                )
            except Exception as notify_error:
                logger.error(
                    f"发送错误通知给管理员 {admin_id} 失败: {notify_error}",
                    exc_info=True,
                )
    except Exception as notify_error:
        logger.error(f"发送错误通知失败: {notify_error}", exc_info=True)
