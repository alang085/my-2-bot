"""统计辅助函数 - 日结数据更新

包含日结统计数据更新的逻辑。
"""

import logging
from typing import Optional

import db_operations

logger = logging.getLogger(__name__)


async def update_daily_amount(
    date: str, daily_amount_field: str, amount: float, group_id: Optional[str] = None
) -> None:
    """更新日结金额字段

    Args:
        date: 日期
        daily_amount_field: 日结金额字段名
        amount: 金额增量
        group_id: 分组ID（可选）
    """
    if amount == 0:
        return

    # 更新全局日结
    try:
        await db_operations.update_daily_data(date, daily_amount_field, amount, None)
        logger.debug(f"✅ 已更新全局日结: {date} {daily_amount_field} += {amount}")
    except Exception as e:
        logger.error(
            f"❌ 更新全局日结失败 ({date}, {daily_amount_field}): {e}", exc_info=True
        )
        raise

    # 更新分组日结
    if group_id:
        try:
            await db_operations.update_daily_data(
                date, daily_amount_field, amount, group_id
            )
            logger.debug(
                f"✅ 已更新分组日结: {date} {group_id} {daily_amount_field} += {amount}"
            )
        except Exception as e:
            logger.error(
                f"❌ 更新分组日结失败 ({date}, {group_id}, {daily_amount_field}): {e}",
                exc_info=True,
            )
            raise


async def update_daily_count(
    date: str, daily_count_field: str, count: int, group_id: Optional[str] = None
) -> None:
    """更新日结计数字段

    Args:
        date: 日期
        daily_count_field: 日结计数字段名
        count: 计数增量
        group_id: 分组ID（可选）
    """
    if count == 0:
        return

    # 更新全局日结计数
    try:
        await db_operations.update_daily_data(date, daily_count_field, count, None)
        logger.debug(f"✅ 已更新全局日结计数: {date} {daily_count_field} += {count}")
    except Exception as e:
        logger.error(
            f"❌ 更新全局日结计数失败 ({date}, {daily_count_field}): {e}", exc_info=True
        )
        raise

    # 更新分组日结计数
    if group_id:
        try:
            await db_operations.update_daily_data(
                date, daily_count_field, count, group_id
            )
            logger.debug(
                f"✅ 已更新分组日结计数: {date} {group_id} {daily_count_field} += {count}"
            )
        except Exception as e:
            logger.error(
                f"❌ 更新分组日结计数失败 ({date}, {group_id}, {daily_count_field}): {e}",
                exc_info=True,
            )
            raise
