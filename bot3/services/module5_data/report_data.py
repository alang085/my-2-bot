"""报表生成 - 数据获取模块

包含获取报表数据的逻辑。
"""

import logging
from typing import Dict, Optional

import db_operations

logger = logging.getLogger(__name__)


async def get_report_current_data(group_id: Optional[str]) -> Dict:
    """获取当前状态数据

    Args:
        group_id: 归属ID，None表示全局报表

    Returns:
        Dict: 当前状态数据
    """
    if group_id:
        # 归属报表：使用grouped_data表获取该归属ID的累计统计数据
        current_data = await db_operations.get_grouped_data(group_id)
        if not current_data:
            current_data = {"valid_orders": 0, "valid_amount": 0.0, "liquid_funds": 0.0}
    else:
        # 全局报表：使用financial_data表获取全局统计数据
        current_data = await db_operations.get_financial_data()
        if not current_data:
            current_data = {"valid_orders": 0, "valid_amount": 0.0, "liquid_funds": 0.0}

    return current_data


def _get_default_stats() -> Dict:
    """获取默认统计数据

    Returns:
        默认统计数据字典
    """
    return {
        "liquid_flow": 0.0,
        "new_clients": 0,
        "new_clients_amount": 0.0,
        "old_clients": 0,
        "old_clients_amount": 0.0,
        "interest": 0.0,
        "completed_orders": 0,
        "completed_amount": 0.0,
        "breach_orders": 0,
        "breach_amount": 0.0,
        "breach_end_orders": 0,
        "breach_end_amount": 0.0,
        "company_expenses": 0.0,
        "other_expenses": 0.0,
    }


async def _update_group_stats_with_global_expenses(
    stats: Dict, start_date: str, end_date: str
) -> None:
    """更新归属统计的全局开销数据

    Args:
        stats: 统计数据字典
        start_date: 开始日期
        end_date: 结束日期
    """
    try:
        global_expense_stats = await db_operations.get_stats_by_date_range(
            start_date, end_date, None
        )
        if global_expense_stats:
            stats["company_expenses"] = global_expense_stats.get(
                "company_expenses", 0.0
            )
            stats["other_expenses"] = global_expense_stats.get("other_expenses", 0.0)
    except Exception as e:
        logger.error(f"获取全局开销数据失败: {e}", exc_info=True)
        stats["company_expenses"] = stats.get("company_expenses", 0.0)
        stats["other_expenses"] = stats.get("other_expenses", 0.0)


async def _update_group_stats_with_global_funds(stats: Dict) -> None:
    """更新归属统计的全局现金余额

    Args:
        stats: 统计数据字典
    """
    try:
        global_financial_data = await db_operations.get_financial_data()
        if global_financial_data:
            stats["liquid_funds"] = global_financial_data.get("liquid_funds", 0.0)
    except Exception as e:
        logger.error(f"获取全局现金余额失败: {e}", exc_info=True)


async def get_report_stats(
    start_date: str, end_date: str, group_id: Optional[str]
) -> Dict:
    """获取周期统计数据

    Args:
        start_date: 开始日期
        end_date: 结束日期
        group_id: 归属ID，None表示全局报表

    Returns:
        Dict: 统计数据
    """
    stats = await db_operations.get_stats_by_date_range(start_date, end_date, group_id)
    if not stats:
        stats = _get_default_stats()

    if group_id:
        await _update_group_stats_with_global_expenses(stats, start_date, end_date)
        await _update_group_stats_with_global_funds(stats)

    return stats
