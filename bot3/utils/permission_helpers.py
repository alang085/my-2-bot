"""权限检查辅助模块

包含用户权限检查相关的辅助函数。
"""

# 标准库
import logging
from typing import Optional, Tuple

from telegram import Update

import db_operations
from config import ADMIN_IDS
from utils.message_helpers import send_error_message
from utils.update_info import get_user_id

logger = logging.getLogger(__name__)


async def check_user_permissions(
    user_id: Optional[int],
) -> Tuple[bool, bool, Optional[str]]:
    """检查用户权限（管理员和授权用户）

    Args:
        user_id: 用户ID

    Returns:
        Tuple[is_admin, is_authorized, error_message]:
            - is_admin: 是否为管理员
            - is_authorized: 是否为授权用户
            - error_message: 错误消息，如果没有错误则为None
    """
    if not user_id:
        return False, False, "❌ 无法获取用户ID"

    is_admin = user_id in ADMIN_IDS
    is_authorized = await db_operations.is_user_authorized(user_id)

    return is_admin, is_authorized, None


def is_admin_user(user_id: Optional[int]) -> bool:
    """检查用户是否为管理员

    Args:
        user_id: 用户ID

    Returns:
        是否为管理员
    """
    if not user_id:
        return False

    return user_id in ADMIN_IDS


async def is_authorized_user(user_id: Optional[int]) -> bool:
    """检查用户是否为授权用户

    Args:
        user_id: 用户ID

    Returns:
        是否为授权用户
    """
    if not user_id:
        return False

    return await db_operations.is_user_authorized(user_id)


async def require_permission(
    update: Update,
    require_admin: bool = False,
    require_authorized: bool = False,
) -> Tuple[bool, Optional[str]]:
    """检查用户权限，如果不满足则发送错误消息

    Args:
        update: Telegram Update 对象
        require_admin: 是否要求管理员权限
        require_authorized: 是否要求授权用户权限（如果require_admin=True则忽略此参数）

    Returns:
        Tuple[has_permission, error_message]:
            - has_permission: 是否有权限
            - error_message: 错误消息，如果有权限则为None
    """
    user_id = get_user_id(update)
    if not user_id:
        error_msg = "❌ 无法获取用户信息"
        await send_error_message(update, error_msg)
        return False, error_msg

    is_admin, is_authorized, check_error = await check_user_permissions(user_id)
    if check_error:
        await send_error_message(update, check_error)
        return False, check_error

    if require_admin:
        if not is_admin:
            error_msg = "❌ 此操作需要管理员权限"
            await send_error_message(update, error_msg)
            return False, error_msg
    elif require_authorized:
        if not is_authorized and not is_admin:
            error_msg = "❌ 此操作需要授权用户权限"
            await send_error_message(update, error_msg)
            return False, error_msg

    return True, None
