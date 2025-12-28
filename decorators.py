"""装饰器定义"""

import os
import sys
from pathlib import Path

# 确保项目根目录在 Python 路径中
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import asyncio
import logging
from functools import wraps

from telegram import Update
from telegram.error import NetworkError, RetryAfter, TimedOut
from telegram.ext import ContextTypes

import db_operations
from config import ADMIN_IDS

logger = logging.getLogger(__name__)

# Telegram API 超时设置（秒）
TELEGRAM_API_TIMEOUT = 5.0  # 减少超时时间，快速失败
MAX_RETRY_ATTEMPTS = 1  # 减少重试次数，避免长时间等待

# 速率限制设置（保留配置，但装饰器未使用）
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "1") == "1"
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # 时间窗口（秒）
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "30"))  # 最大请求数


async def _safe_send_error_message(
    update: Update, error_msg: str, max_retries: int = MAX_RETRY_ATTEMPTS
):
    """安全地发送错误消息，带超时和重试机制

    Args:
        update: Telegram Update 对象
        error_msg: 错误消息文本
        max_retries: 最大重试次数
    """
    # 截断过长的错误消息
    if len(error_msg) > 4000:
        error_msg = error_msg[:4000] + "..."

    for attempt in range(max_retries + 1):
        try:
            # 使用超时保护，避免长时间等待
            if update.callback_query:
                query = update.callback_query
                if query.message:
                    await asyncio.wait_for(
                        query.message.reply_text(error_msg), timeout=TELEGRAM_API_TIMEOUT
                    )
                else:
                    # 如果 message 不存在，尝试使用 answer（更短的消息）
                    short_msg = error_msg[:200] if len(error_msg) > 200 else error_msg
                    await asyncio.wait_for(
                        query.answer(short_msg, show_alert=True), timeout=TELEGRAM_API_TIMEOUT
                    )
            elif update.message:
                await asyncio.wait_for(
                    update.message.reply_text(error_msg), timeout=TELEGRAM_API_TIMEOUT
                )
            # 成功发送，退出重试循环
            return
        except (asyncio.TimeoutError, TimedOut, NetworkError) as timeout_error:
            # 网络超时或连接错误，快速失败，不重试
            logger.warning(f"发送错误消息失败（网络超时/连接错误）: {type(timeout_error).__name__}")
            # 不重试，直接退出，避免浪费时间和流量
            break
        except RetryAfter as retry_error:
            # Telegram API 要求等待，只在第一次尝试时等待
            wait_time = retry_error.retry_after
            if attempt == 0 and wait_time < 10:  # 只等待短时间
                logger.warning(f"Telegram API 要求等待 {wait_time} 秒")
                await asyncio.sleep(wait_time)
            else:
                logger.warning(f"Telegram API 要求等待时间过长 ({wait_time}秒)，跳过")
                break
        except Exception as send_error:
            # 其他错误，记录但不重试
            logger.error(
                f"发送错误消息失败: {type(send_error).__name__}: {send_error}",
                exc_info=False,  # 不打印完整堆栈，节省日志
            )
            # 直接退出，不重试
            break


def error_handler(func):
    """统一错误处理装饰器，自动捕获异常并向用户发送错误消息

    改进：
    - 添加超时保护，避免长时间等待
    - 添加重试机制，处理网络错误
    - 确保错误处理本身不会导致程序崩溃
    """

    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        try:
            return await func(update, context, *args, **kwargs)
        except Exception as e:
            # 记录详细错误信息
            error_type = type(e).__name__
            error_str = str(e)
            logger.error(f"Error in {func.__name__}: {error_type}: {error_str}", exc_info=True)

            # 生成用户友好的错误消息
            if isinstance(e, NetworkError):
                # 网络连接错误，可能是临时性问题
                error_msg = "⚠️ 网络连接异常，请稍后重试。"
                logger.warning(f"网络连接错误（可能为临时性问题）: {e}")
            elif isinstance(e, TimedOut):
                error_msg = "⚠️ 网络连接超时，请稍后重试。"
            elif isinstance(e, RetryAfter):
                error_msg = f"⚠️ 请求过于频繁，请稍后再试。"
            else:
                # 对于其他错误，显示简化消息（避免暴露敏感信息）
                error_msg = f"⚠️ 操作失败: {error_type}"
                # 只在调试模式下显示详细错误
                if os.getenv("DEBUG", "0") == "1":
                    error_msg += f"\n详情: {error_str[:200]}"

            # 安全地发送错误消息（带超时，快速失败）
            # 使用 asyncio.wait_for 确保不会无限等待
            try:
                await asyncio.wait_for(
                    _safe_send_error_message(update, error_msg),
                    timeout=TELEGRAM_API_TIMEOUT * (MAX_RETRY_ATTEMPTS + 1) + 2,  # 总超时时间
                )
            except asyncio.TimeoutError:
                logger.warning("发送错误消息总超时，已跳过")
            except Exception as send_error:
                # 即使发送错误消息也失败，只记录日志，不抛出异常
                logger.warning(
                    f"发送错误消息失败: {type(send_error).__name__}",
                    exc_info=False,  # 不打印完整堆栈
                )

    return wrapped


def admin_required(func):
    """检查用户是否是管理员的装饰器"""

    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        # 添加日志追踪
        logger.info(f"admin_required: 检查函数 {func.__name__} 的权限")

        # 检查是否有消息对象
        if not update.message and not update.callback_query:
            logger.warning(f"admin_required: {func.__name__} - 没有消息对象，提前返回")
            return

        # 获取用户ID
        user_id = update.effective_user.id if update.effective_user else None

        # 确保类型一致（都是int）
        if user_id:
            user_id = int(user_id)

        logger.info(f"admin_required: {func.__name__} - 用户ID: {user_id}, 管理员列表: {ADMIN_IDS}")

        # 调试日志（仅在DEBUG模式下）
        if os.getenv("DEBUG", "0") == "1":
            logger.debug(
                f"权限检查 - 用户ID: {user_id}, 类型: {type(user_id)}, 管理员列表: {ADMIN_IDS}"
            )

        # 检查权限
        has_permission = user_id and user_id in ADMIN_IDS
        logger.info(
            f"admin_required: {func.__name__} - 权限检查结果: {has_permission} (用户ID: {user_id}, 在管理员列表中: {user_id in ADMIN_IDS if user_id and ADMIN_IDS else False})"
        )

        if not has_permission:
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
            logger.warning(
                f"权限检查失败 - 用户ID: {user_id}, 不在管理员列表中, 管理员列表: {ADMIN_IDS}"
            )

            try:
                if update.message:
                    await update.message.reply_text(error_msg)
                    logger.info(f"已向用户 {user_id} 发送权限错误消息")
                elif update.callback_query:
                    # 回调查询中显示简短消息，详细信息记录到日志
                    await update.callback_query.answer(
                        "⚠️ Admin permission required.", show_alert=True
                    )
                    logger.info(f"已向用户 {user_id} 发送权限错误提示（回调查询）")
            except Exception as send_error:
                logger.error(
                    f"发送权限错误消息失败: {type(send_error).__name__}: {send_error}",
                    exc_info=True,
                )
            return

        logger.info(f"admin_required: {func.__name__} - 权限检查通过，执行函数")
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
        chat_type = update.effective_chat.type if update.effective_chat else "unknown"
        logger.info(f"private_chat_only: {func.__name__} - 聊天类型: {chat_type}")

        if chat_type != "private":
            logger.warning(f"private_chat_only: {func.__name__} - 不在私聊中，拒绝执行")
            if update.message:
                await update.message.reply_text("⚠️ This command can only be used in private chat.")
            elif update.callback_query:
                await update.callback_query.answer(
                    "⚠️ This command can only be used in private chat.", show_alert=True
                )
            return

        logger.info(f"private_chat_only: {func.__name__} - 在私聊中，允许执行")
        return await func(update, context, *args, **kwargs)

    return wrapped


def group_chat_only(func):
    """检查是否在群组中使用命令的装饰器"""

    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        from utils.chat_helpers import is_group_chat

        if not is_group_chat(update):
            if update.message:
                await update.message.reply_text("⚠️ This command can only be used in group chat.")
            elif update.callback_query:
                await update.callback_query.answer(
                    "⚠️ This command can only be used in group chat.", show_alert=True
                )
            return
        return await func(update, context, *args, **kwargs)

    return wrapped
