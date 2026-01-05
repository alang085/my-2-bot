"""访问控制系统

提供细粒度的访问控制功能。
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Set

from config import ADMIN_IDS

logger = logging.getLogger(__name__)

# 访问控制规则
_access_rules: Dict[str, Dict[str, Any]] = {}
_access_rules_lock = asyncio.Lock()

# 用户权限缓存
_user_permissions: Dict[int, Set[str]] = {}
_permission_cache_ttl: Dict[int, datetime] = {}
_cache_ttl_seconds = 300  # 5分钟


async def check_permission(user_id: int, resource: str, action: str) -> bool:
    """检查用户权限

    Args:
        user_id: 用户ID
        resource: 资源名称
        action: 操作名称

    Returns:
        是否有权限
    """
    # 管理员拥有所有权限
    if user_id in ADMIN_IDS:
        return True

    # 检查权限缓存
    f"{user_id}_{resource}_{action}"
    if user_id in _permission_cache_ttl:
        if datetime.now() < _permission_cache_ttl[user_id]:
            if user_id in _user_permissions:
                permissions = _user_permissions[user_id]
                return f"{resource}:{action}" in permissions

    # 从数据库查询权限（这里简化实现）
    # 注意：db.module5_user.users 中可能没有 get_user_permissions 函数
    # 这里使用占位符实现，实际应该根据实际数据库结构实现
    try:
        # TODO: 实现实际的权限查询逻辑
        # from db.module5_user.users import get_user_permissions
        # permissions = await get_user_permissions(user_id)
        permissions = None  # 占位符
        if permissions:
            # 更新缓存
            async with _access_rules_lock:
                _user_permissions[user_id] = set(permissions)
                _permission_cache_ttl[user_id] = datetime.now() + timedelta(
                    seconds=_cache_ttl_seconds
                )

            return f"{resource}:{action}" in permissions
    except Exception as e:
        logger.error(f"查询用户权限失败: {e}", exc_info=True)

    return False


async def grant_permission(user_id: int, resource: str, action: str) -> bool:
    """授予权限

    Args:
        user_id: 用户ID
        resource: 资源名称
        action: 操作名称

    Returns:
        是否成功
    """
    try:
        # TODO: 实现实际的权限添加逻辑
        # from db.module5_user.users import add_user_permission
        # success = await add_user_permission(user_id, f"{resource}:{action}")
        success = False  # 占位符
        if success:
            # 清除缓存
            async with _access_rules_lock:
                if user_id in _user_permissions:
                    del _user_permissions[user_id]
                if user_id in _permission_cache_ttl:
                    del _permission_cache_ttl[user_id]

        return success
    except Exception as e:
        logger.error(f"授予权限失败: {e}", exc_info=True)
        return False


async def revoke_permission(user_id: int, resource: str, action: str) -> bool:
    """撤销权限

    Args:
        user_id: 用户ID
        resource: 资源名称
        action: 操作名称

    Returns:
        是否成功
    """
    try:
        from db.module5_user.users import remove_user_permission

        success = await remove_user_permission(user_id, f"{resource}:{action}")
        if success:
            # 清除缓存
            async with _access_rules_lock:
                if user_id in _user_permissions:
                    del _user_permissions[user_id]
                if user_id in _permission_cache_ttl:
                    del _permission_cache_ttl[user_id]

        return success
    except Exception as e:
        logger.error(f"撤销权限失败: {e}", exc_info=True)
        return False


def require_permission(resource: str, action: str):
    """权限检查装饰器

    Args:
        resource: 资源名称
        action: 操作名称

    Usage:
        @require_permission("orders", "create")
        async def create_order(update, context):
            ...
    """

    def decorator(func):
        async def wrapper(update, context, *args, **kwargs):
            user_id = update.effective_user.id if update.effective_user else None
            if not user_id:
                await update.message.reply_text("❌ 无法获取用户ID")
                return

            has_permission = await check_permission(user_id, resource, action)
            if not has_permission:
                await update.message.reply_text("❌ 您没有执行此操作的权限")
                return

            return await func(update, context, *args, **kwargs)

        return wrapper

    return decorator


async def get_user_permissions(user_id: int) -> Set[str]:
    """获取用户所有权限

    Args:
        user_id: 用户ID

    Returns:
        权限集合
    """
    # 管理员拥有所有权限
    if user_id in ADMIN_IDS:
        return {"*:*"}  # 通配符表示所有权限

    # 检查缓存
    if user_id in _permission_cache_ttl:
        if datetime.now() < _permission_cache_ttl[user_id]:
            if user_id in _user_permissions:
                return _user_permissions[user_id]

    # 从数据库查询
    try:
        from db.module5_user.users import get_user_permissions

        permissions = await get_user_permissions(user_id)
        if permissions:
            async with _access_rules_lock:
                _user_permissions[user_id] = set(permissions)
                _permission_cache_ttl[user_id] = datetime.now() + timedelta(
                    seconds=_cache_ttl_seconds
                )

            return set(permissions)
    except Exception as e:
        logger.error(f"查询用户权限失败: {e}", exc_info=True)

    return set()
