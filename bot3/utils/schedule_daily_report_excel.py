"""每日报表 - Excel生成模块

包含生成Excel文件的逻辑。
"""

import logging
from typing import Optional, Tuple

import db_operations
from utils.excel_export import (export_daily_changes_to_excel,
                                export_orders_to_excel)

logger = logging.getLogger(__name__)


async def generate_excel_files(report_date: str) -> Tuple[Optional[str], Optional[str]]:
    """生成Excel文件

    Args:
        report_date: 报表日期

    Returns:
        Tuple[Optional[str], Optional[str]]: (订单总表Excel路径, 每日变化数据Excel路径)
    """
    orders_excel_path = await _generate_orders_excel(report_date)
    changes_excel_path = await _generate_changes_excel(report_date)

    return orders_excel_path, changes_excel_path


async def _generate_orders_excel(report_date: str) -> Optional[str]:
    """生成订单总表Excel

    Args:
        report_date: 报表日期

    Returns:
        Optional[str]: Excel文件路径，如果失败则返回None
    """
    try:
        # 获取所有有效订单
        valid_orders = await db_operations.get_all_valid_orders()

        # 获取当日利息总额
        daily_interest = await db_operations.get_daily_interest_total(report_date)

        # 获取当日完成的订单
        completed_orders = await db_operations.get_completed_orders_by_date(report_date)

        # 获取当日违约的订单（仅当日有变动的）
        breach_orders = await db_operations.get_breach_orders_by_date(report_date)

        # 获取当日违约完成的订单（仅当日有变动的）
        breach_end_orders = await db_operations.get_breach_end_orders_by_date(
            report_date
        )

        # 获取日切数据
        daily_summary = await db_operations.get_daily_summary(report_date)

        # 导出订单总表Excel
        orders_excel_path = await export_orders_to_excel(
            valid_orders,
            completed_orders,
            breach_orders,
            breach_end_orders,
            daily_interest,
            daily_summary,
        )
        logger.info(f"订单总表Excel已生成: {orders_excel_path}")
        return orders_excel_path
    except Exception as e:
        logger.error(f"生成订单总表Excel失败: {e}", exc_info=True)
        return None


async def _generate_changes_excel(report_date: str) -> Optional[str]:
    """生成每日变化数据Excel

    Args:
        report_date: 报表日期

    Returns:
        Optional[str]: Excel文件路径，如果失败则返回None
    """
    try:
        # 导出每日变化数据Excel
        changes_excel_path = await export_daily_changes_to_excel(report_date)
        logger.info(f"每日变化数据Excel已生成: {changes_excel_path}")
        return changes_excel_path
    except Exception as e:
        logger.error(f"生成每日变化数据Excel失败: {e}", exc_info=True)
        return None
