"""撤销操作处理器 - 通知模块

包含撤销操作的通知逻辑。
"""

import logging
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_IDS
from handlers.module5_data.undo_handlers_validation import MAX_UNDO_COUNT
from handlers.module5_data.undo_notification_data import (
    AdminNotificationParams, ExceptionAdminNotificationParams,
    FailureAdminNotificationParams)

logger = logging.getLogger(__name__)


async def send_admin_notification(
    context: ContextTypes.DEFAULT_TYPE, message: str
) -> None:
    """向所有管理员发送通知

    Args:
        context: 上下文对象
        message: 通知消息
    """
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=message)
        except Exception as e:
            logger.error(f"向管理员 {admin_id} 发送通知失败: {e}")


def build_success_admin_message(params: AdminNotificationParams) -> str:
    """构建成功撤销的管理员通知消息

    Args:
        params: 管理员通知参数

    Returns:
        str: 管理员通知消息
    """
    return (
        "⚠️ 撤销操作通知（成功）\n\n"
        f"用户: {params.user_full_name} (@{params.username})\n"
        f"用户ID: {params.user_id}\n"
        f"{params.chat_info}"
        f"操作类型: {params.operation_type}\n"
        f"撤销详情: {params.undo_message if not params.is_group else params.undo_message_en}\n"
        f"连续撤销次数: {params.undo_count + 1}/{MAX_UNDO_COUNT}\n"
        f"操作时间: {params.created_at}\n"
        f"\n{params.consistency_status}"
    )


def build_failure_admin_message(params: FailureAdminNotificationParams) -> str:
    """构建失败撤销的管理员通知消息

    Args:
        params: 失败撤销管理员通知参数

    Returns:
        str: 管理员通知消息
    """
    from utils.error_messages import ErrorMessages

    return (
        f"{ErrorMessages.operation_failed('撤销操作通知')}\n\n"
        f"用户: {params.user_full_name} (@{params.username})\n"
        f"用户ID: {params.user_id}\n"
        f"{params.chat_info}"
        f"操作类型: {params.operation_type}\n"
        f"操作ID: {params.operation_id}\n"
        f"操作时间: {params.created_at}\n"
        f"连续撤销次数: {params.undo_count}/{MAX_UNDO_COUNT}\n"
        f"\n⚠️ 撤销操作失败，请检查数据状态和日志。"
    )


def build_exception_admin_message(params: ExceptionAdminNotificationParams) -> str:
    """构建异常撤销的管理员通知消息

    Args:
        params: 异常撤销管理员通知参数

    Returns:
        str: 管理员通知消息
    """
    return (
        "❌ 撤销操作通知（异常）\n\n"
        f"用户: {params.user_full_name} (@{params.username})\n"
        f"用户ID: {params.user_id_str}\n"
        f"{params.chat_info}"
        f"错误类型: {type(params.error).__name__}\n"
        f"错误信息: {str(params.error)}\n"
        f"\n⚠️ 撤销操作发生异常，请检查日志和数据库状态。"
    )


def get_username(update: Update) -> str:
    """获取用户名

    Args:
        update: Telegram更新对象

    Returns:
        str: 用户名，如果不存在则返回 "N/A"
    """
    if update.effective_user and update.effective_user.username:
        return update.effective_user.username
    return "N/A"
