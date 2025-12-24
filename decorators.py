"""装饰器定义"""

import os
import sys
from pathlib import Path

# 确保项目根目录在 Python 路径中
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import logging
from functools import wraps

from telegram import Update
from telegram.ext import ContextTypes

import db_operations
from config import ADMIN_IDS

logger = logging.getLogger(__name__)


def error_handler(func):
    """统一错误处理装饰器，自动捕获异常并向用户发送错误消息"""

    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        try:
            return await func(update, context, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            error_msg = f"⚠️ Operation Failed: {str(e)}"

            # 尝试回复用户
            try:
                if update.callback_query:
                    # 检查 callback_query.message 是否存在
                    if update.callback_query.message:
                        await update.callback_query.message.reply_text(error_msg)
                    else:
                        # 如果 message 不存在，尝试使用 answer
                        await update.callback_query.answer(error_msg, show_alert=True)
                elif update.message:
                    await update.message.reply_text(error_msg)
            except Exception as send_error:
                logger.error(f"Failed to send error message: {send_error}")

    return wrapped


def admin_required(func):
    """检查用户是否是管理员的装饰器"""

    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        # 检查是否有消息对象
        if not update.message and not update.callback_query:
            return

        # 获取用户ID
        user_id = update.effective_user.id if update.effective_user else None

        # 确保类型一致（都是int）
        if user_id:
            user_id = int(user_id)

        # 调试日志（仅在DEBUG模式下）
        if os.getenv("DEBUG", "0") == "1":
            logger.debug(
                f"权限检查 - 用户ID: {user_id}, 类型: {type(user_id)}, 管理员列表: {ADMIN_IDS}"
            )

        if not user_id or user_id not in ADMIN_IDS:
            # 提供更详细的错误信息，帮助用户排查问题
            error_msg = "⚠️ Admin permission required.\n\n"
            error_msg += f"Your User ID: {user_id} (type: {type(user_id).__name__})\n"
            error_msg += f"Admin IDs: {ADMIN_IDS if ADMIN_IDS else 'Not configured'}\n"
            if ADMIN_IDS:
                error_msg += f"Admin ID types: {[type(x).__name__ for x in ADMIN_IDS]}\n"
            error_msg += "\nPlease check:\n"
            error_msg += "1. ADMIN_USER_IDS environment variable is set\n"
            error_msg += "2. Your User ID is in the list\n"
            error_msg += "3. Format: ADMIN_USER_IDS=id1,id2,id3 (no spaces)\n"
            error_msg += "4. Application was restarted after changing env vars"

            # 记录警告日志（生产环境简化日志）
            logger.warning(f"权限检查失败 - 用户ID: {user_id}, 不在管理员列表中")

            if update.message:
                await update.message.reply_text(error_msg)
            elif update.callback_query:
                # 回调查询中显示简短消息，详细信息记录到日志
                await update.callback_query.answer("⚠️ Admin permission required.", show_alert=True)
            return

        return await func(update, context, *args, **kwargs)

    return wrapped


def authorized_required(func):
    """检查用户是否有操作权限（管理员或员工）"""

    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        # 检查是否有消息对象
        if not update.message and not update.callback_query:
            return

        # 获取用户ID
        user_id = update.effective_user.id if update.effective_user else None

        if not user_id:
            return

        # 检查是否是管理员
        if user_id in ADMIN_IDS:
            return await func(update, context, *args, **kwargs)

        # 检查是否是授权员工
        if await db_operations.is_user_authorized(user_id):
            return await func(update, context, *args, **kwargs)

        error_msg = "⚠️ Permission denied."
        if update.message:
            await update.message.reply_text(error_msg)
        elif update.callback_query:
            await update.callback_query.answer(error_msg, show_alert=True)
        return

    return wrapped


def private_chat_only(func):
    """检查是否在私聊中使用命令的装饰器"""

    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.effective_chat.type != "private":
            await update.message.reply_text("⚠️ This command can only be used in private chat.")
            return
        return await func(update, context, *args, **kwargs)

    return wrapped


def group_chat_only(func):
    """检查是否在群组中使用命令的装饰器"""

    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        from utils.chat_helpers import is_group_chat

        if not is_group_chat(update):
            await update.message.reply_text("⚠️ This command can only be used in group chat.")
            return
        return await func(update, context, *args, **kwargs)

    return wrapped
