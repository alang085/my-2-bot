"""用户服务 - 封装用户相关的业务逻辑"""

import logging
from typing import Optional

import db_operations

logger = logging.getLogger(__name__)


class UserService:
    """用户业务服务"""

    @staticmethod
    async def is_authorized(user_id: int) -> bool:
        """检查用户是否已授权"""
        return await db_operations.is_user_authorized(user_id)

    @staticmethod
    async def get_user_group_id(user_id: int) -> Optional[str]:
        """获取用户的归属ID"""
        return await db_operations.get_user_group_id(user_id)
