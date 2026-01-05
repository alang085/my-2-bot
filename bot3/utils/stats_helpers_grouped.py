"""统计辅助函数 - 分组累计数据更新

包含分组累计统计数据更新的逻辑。
"""

import logging
from typing import Optional

import db_operations

logger = logging.getLogger(__name__)


async def update_grouped_amount(
    group_id: str, group_amount_field: str, amount: float
) -> None:
    """更新分组累计金额字段

    Args:
        group_id: 分组ID
        group_amount_field: 分组金额字段名
        amount: 金额增量
    """
    if amount == 0:
        return

    try:
        await db_operations.update_grouped_data(
            group_id=group_id, field=group_amount_field, amount=amount
        )
        logger.debug(f"✅ 已更新分组累计: {group_id} {group_amount_field} += {amount}")
    except Exception as e:
        logger.error(
            f"❌ 更新分组累计失败 ({group_id}, {group_amount_field}): {e}",
            exc_info=True,
        )
        raise


async def update_grouped_count(
    group_id: str, group_count_field: str, count: int
) -> None:
    """更新分组累计计数字段

    Args:
        group_id: 分组ID
        group_count_field: 分组计数字段名
        count: 计数增量
    """
    if count == 0:
        return

    try:
        await db_operations.update_grouped_data(
            group_id=group_id, field=group_count_field, amount=float(count)
        )
        logger.debug(
            f"✅ 已更新分组累计计数: {group_id} {group_count_field} += {count}"
        )
    except Exception as e:
        logger.error(
            f"❌ 更新分组累计计数失败 ({group_id}, {group_count_field}): {e}",
            exc_info=True,
        )
        raise
