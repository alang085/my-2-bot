"""统计数据相关工具函数"""

import logging
from typing import Optional

import db_operations
from constants import DAILY_ALLOWED_PREFIXES
from utils.date_helpers import get_daily_period_date

logger = logging.getLogger(__name__)


async def update_liquid_capital(amount: float):
    """更新流动资金（全局余额 + 日结流量）"""
    try:
        await db_operations.update_financial_data("liquid_funds", amount)
        date = get_daily_period_date()
        await db_operations.update_daily_data(date, "liquid_flow", amount, None)
    except Exception as e:
        logger.error(f"更新流动资金失败: {e}", exc_info=True)
        raise


def _calculate_stat_field_names(field: str) -> tuple[str, str]:
    """计算统计字段名

    Args:
        field: 基础字段名

    Returns:
        (amount_field, count_field)
    """
    global_amount_field = (
        field
        if field.endswith("_amount") or field in ["liquid_funds", "interest"]
        else f"{field}_amount"
    )
    global_count_field = (
        field
        if field.endswith("_orders") or field in ["new_clients", "old_clients"]
        else f"{field}_orders"
    )
    return global_amount_field, global_count_field


async def _update_global_statistics(
    amount_field: str, count_field: str, amount: float, count: int
) -> None:
    """更新全局统计数据

    Args:
        amount_field: 金额字段名
        count_field: 计数字段名
        amount: 金额
        count: 计数
    """
    from utils.stats_helpers_global import (update_global_amount,
                                            update_global_count)

    await update_global_amount(amount_field, amount)
    await update_global_count(count_field, count)


async def _update_daily_statistics(
    field: str,
    amount_field: str,
    count_field: str,
    amount: float,
    count: int,
    date: str,
    group_id: Optional[str],
) -> None:
    """更新日结统计数据

    Args:
        field: 基础字段名
        amount_field: 金额字段名
        count_field: 计数字段名
        amount: 金额
        count: 计数
        date: 日期
        group_id: 归属ID
    """
    from utils.stats_helpers_daily import (update_daily_amount,
                                           update_daily_count)

    daily_amount_field = (
        field if field.endswith("_amount") or field == "interest" else f"{field}_amount"
    )
    daily_count_field = (
        field
        if field.endswith("_orders") or field in ["new_clients", "old_clients"]
        else f"{field}_orders"
    )
    await update_daily_amount(date, daily_amount_field, amount, group_id)
    await update_daily_count(date, daily_count_field, count, group_id)


async def _update_grouped_statistics(
    amount_field: str, count_field: str, amount: float, count: int, group_id: str
) -> None:
    """更新分组累计统计数据

    Args:
        amount_field: 金额字段名
        count_field: 计数字段名
        amount: 金额
        count: 计数
        group_id: 归属ID
    """
    from utils.stats_helpers_grouped import (update_grouped_amount,
                                             update_grouped_count)

    await update_grouped_amount(group_id, amount_field, amount)
    await update_grouped_count(group_id, count_field, count)


async def update_all_stats(
    field: str,
    amount: float,
    count: int = 0,
    group_id: Optional[str] = None,
    skip_daily: bool = False,
) -> None:
    """统一更新所有统计数据（全局、日结、分组）

    注意：所有更新操作应该在同一日期下执行，以确保数据一致性。
    如果某个更新失败，前面的更新可能已经成功，需要手动修复或重新计算。
    """
    date = None
    is_daily_field = any(field.startswith(prefix) for prefix in DAILY_ALLOWED_PREFIXES)
    if is_daily_field and not skip_daily:
        date = get_daily_period_date()

    amount_field, count_field = _calculate_stat_field_names(field)

    try:
        await _update_global_statistics(amount_field, count_field, amount, count)

        if is_daily_field and not skip_daily and date:
            await _update_daily_statistics(
                field, amount_field, count_field, amount, count, date, group_id
            )

        if group_id:
            await _update_grouped_statistics(
                amount_field, count_field, amount, count, group_id
            )

        logger.info(
            f"✅ 统计更新完成: field={field}, amount={amount}, "
            f"count={count}, group_id={group_id}, date={date}"
        )

    except Exception as e:
        logger.error(
            f"❌ 更新统计数据失败: field={field}, amount={amount}, "
            f"count={count}, group_id={group_id}, date={date}, error={e}",
            exc_info=True,
        )
        raise
