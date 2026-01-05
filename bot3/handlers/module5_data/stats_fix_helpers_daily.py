"""统计修复辅助函数 - 日结统计修复模块

包含日结统计数据修复的逻辑。
"""

from typing import Any, Dict

import db_operations


async def fix_daily_statistics(
    daily_income: Dict[str, Dict[str, Dict[str, Any]]],
) -> int:
    """修复日结统计数据（daily_data表）

    Args:
        daily_income: 按日期和归属ID分组的收入数据

    Returns:
        int: 修复的记录数
    """
    daily_fixed_count = 0

    for date, groups in daily_income.items():
        for group_id, income_data in groups.items():
            # 获取当前日结数据
            current_daily = await db_operations.get_stats_by_date_range(
                date, date, group_id
            )

            # 修复利息收入
            if "interest" in income_data:
                interest_diff = income_data["interest"] - current_daily.get(
                    "interest", 0.0
                )
                if abs(interest_diff) > 0.01:
                    await db_operations.update_daily_data(
                        date, "interest", interest_diff, group_id
                    )
                    daily_fixed_count += 1

            # 修复完成订单
            daily_fixed_count += await _fix_daily_completed(
                date, group_id, income_data, current_daily
            )

            # 修复违约完成
            daily_fixed_count += await _fix_daily_breach_end(
                date, group_id, income_data, current_daily
            )

    return daily_fixed_count


async def _fix_daily_completed(
    date: str,
    group_id: str,
    income_data: Dict[str, Any],
    current_daily: Dict[str, Any],
) -> int:
    """修复日结完成订单统计

    Returns:
        int: 修复的记录数
    """
    fixed_count = 0

    if "completed_amount" in income_data:
        completed_amount_diff = income_data["completed_amount"] - current_daily.get(
            "completed_amount", 0.0
        )
        if abs(completed_amount_diff) > 0.01:
            await db_operations.update_daily_data(
                date, "completed_amount", completed_amount_diff, group_id
            )
            fixed_count += 1

    if "completed_count" in income_data:
        completed_count_diff = income_data["completed_count"] - current_daily.get(
            "completed_orders", 0
        )
        if abs(completed_count_diff) > 0:
            await db_operations.update_daily_data(
                date, "completed_orders", float(completed_count_diff), group_id
            )
            fixed_count += 1

    return fixed_count


async def _fix_daily_breach_end(
    date: str,
    group_id: str,
    income_data: Dict[str, Any],
    current_daily: Dict[str, Any],
) -> int:
    """修复日结违约完成统计

    Returns:
        int: 修复的记录数
    """
    fixed_count = 0

    if "breach_end_amount" in income_data:
        breach_end_amount_diff = income_data["breach_end_amount"] - current_daily.get(
            "breach_end_amount", 0.0
        )
        if abs(breach_end_amount_diff) > 0.01:
            await db_operations.update_daily_data(
                date, "breach_end_amount", breach_end_amount_diff, group_id
            )
            fixed_count += 1

    if "breach_end_count" in income_data:
        breach_end_count_diff = income_data["breach_end_count"] - current_daily.get(
            "breach_end_orders", 0
        )
        if abs(breach_end_count_diff) > 0:
            await db_operations.update_daily_data(
                date, "breach_end_orders", float(breach_end_count_diff), group_id
            )
            fixed_count += 1

    return fixed_count
