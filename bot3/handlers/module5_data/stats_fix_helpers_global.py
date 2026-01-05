"""统计修复辅助函数 - 全局统计修复模块

包含全局统计数据修复的逻辑。
"""

from typing import Any, Dict, List

import db_operations


async def _fix_interest_statistics(
    income_summary: Dict[str, Any],
    financial_data: Dict[str, Any],
    fixed_items: List[str],
) -> None:
    """修复利息收入统计

    Args:
        income_summary: 收入汇总
        financial_data: 当前财务数据
        fixed_items: 修复项列表
    """
    interest_diff = income_summary["interest"] - financial_data.get("interest", 0.0)
    if abs(interest_diff) > 0.01:
        await db_operations.update_financial_data("interest", interest_diff)
        fixed_items.append(f"全局利息收入: {interest_diff:+,.2f}")


async def _fix_completed_statistics(
    income_summary: Dict[str, Any],
    financial_data: Dict[str, Any],
    fixed_items: List[str],
) -> None:
    """修复完成订单统计

    Args:
        income_summary: 收入汇总
        financial_data: 当前财务数据
        fixed_items: 修复项列表
    """
    completed_amount_diff = income_summary["completed_amount"] - financial_data.get(
        "completed_amount", 0.0
    )
    if abs(completed_amount_diff) > 0.01:
        await db_operations.update_financial_data(
            "completed_amount", completed_amount_diff
        )
        fixed_items.append(f"全局完成订单金额: {completed_amount_diff:+,.2f}")

    completed_count_diff = income_summary["completed_count"] - financial_data.get(
        "completed_orders", 0
    )
    if abs(completed_count_diff) > 0:
        await db_operations.update_financial_data(
            "completed_orders", float(completed_count_diff)
        )
        fixed_items.append(f"全局完成订单数: {completed_count_diff:+d}")


async def _fix_breach_end_statistics(
    income_summary: Dict[str, Any],
    financial_data: Dict[str, Any],
    fixed_items: List[str],
) -> None:
    """修复违约完成统计

    Args:
        income_summary: 收入汇总
        financial_data: 当前财务数据
        fixed_items: 修复项列表
    """
    breach_end_amount_diff = income_summary["breach_end_amount"] - financial_data.get(
        "breach_end_amount", 0.0
    )
    if abs(breach_end_amount_diff) > 0.01:
        await db_operations.update_financial_data(
            "breach_end_amount", breach_end_amount_diff
        )
        fixed_items.append(f"全局违约完成金额: {breach_end_amount_diff:+,.2f}")

    breach_end_count_diff = income_summary["breach_end_count"] - financial_data.get(
        "breach_end_orders", 0
    )
    if abs(breach_end_count_diff) > 0:
        await db_operations.update_financial_data(
            "breach_end_orders", float(breach_end_count_diff)
        )
        fixed_items.append(f"全局违约完成订单数: {breach_end_count_diff:+d}")


async def fix_global_statistics(
    income_summary: Dict[str, Any], financial_data: Dict[str, Any]
) -> List[str]:
    """修复全局统计数据（financial_data表）

    Args:
        income_summary: 收入汇总
        financial_data: 当前财务数据

    Returns:
        List[str]: 修复项列表
    """
    fixed_items: List[str] = []

    await _fix_interest_statistics(income_summary, financial_data, fixed_items)
    await _fix_completed_statistics(income_summary, financial_data, fixed_items)
    await _fix_breach_end_statistics(income_summary, financial_data, fixed_items)

    return fixed_items
