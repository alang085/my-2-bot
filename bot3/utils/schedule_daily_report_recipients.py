"""每日报表 - 接收人模块

包含获取接收人列表的逻辑。
"""

import logging
from typing import List

import db_operations
from constants import ADMIN_IDS

logger = logging.getLogger(__name__)


async def get_all_recipients() -> List[int]:
    """获取所有接收人列表（管理员和授权员工）

    Returns:
        List[int]: 接收人ID列表
    """
    # 获取所有授权员工（业务员）
    authorized_users = await db_operations.get_authorized_users()

    # 合并管理员和授权员工列表（去重）
    all_recipients = list(set(ADMIN_IDS + authorized_users))

    logger.info(
        f"报表接收人: {len(ADMIN_IDS)} 个管理员, "
        f"{len(authorized_users)} 个业务员, 总计 {len(all_recipients)} 人"
    )

    return all_recipients
