"""日切报表生成器"""

# 标准库
import logging
from typing import Dict

# 本地模块
import db_operations
from utils.order_table_helpers import (generate_breach_end_orders_table,
                                       generate_completed_orders_table,
                                       generate_order_table)

logger = logging.getLogger(__name__)


def _calculate_new_orders_stats(new_orders: list) -> Dict:
    """计算新增订单统计

    Args:
        new_orders: 新增订单列表

    Returns:
        统计字典
    """
    new_clients_count = 0
    new_clients_amount = 0.0
    old_clients_count = 0
    old_clients_amount = 0.0

    for order in new_orders:
        customer = order.get("customer", "")
        amount = order.get("amount", 0) or 0
        if customer == "A":
            new_clients_count += 1
            new_clients_amount += amount
        elif customer == "B":
            old_clients_count += 1
            old_clients_amount += amount

    return {
        "new_clients_count": new_clients_count,
        "new_clients_amount": new_clients_amount,
        "old_clients_count": old_clients_count,
        "old_clients_amount": old_clients_amount,
    }


def _calculate_orders_stats(orders: list) -> tuple[int, float]:
    """计算订单统计

    Args:
        orders: 订单列表

    Returns:
        (count, total_amount)
    """
    count = len(orders)
    total_amount = sum(order.get("amount", 0) or 0 for order in orders)
    return count, total_amount


async def _get_daily_orders_data(date: str) -> Dict:
    """获取当日订单数据

    Args:
        date: 日期字符串

    Returns:
        订单数据字典
    """
    new_orders = await db_operations.get_new_orders_by_date(date)
    completed_orders = await db_operations.get_completed_orders_by_date(date)
    breach_orders = await db_operations.get_breach_orders_by_date(date)
    breach_end_orders = await db_operations.get_breach_end_orders_by_date(date)

    new_stats = _calculate_new_orders_stats(new_orders)
    completed_count, completed_amount = _calculate_orders_stats(completed_orders)
    breach_count, breach_amount = _calculate_orders_stats(breach_orders)
    breach_end_count, breach_end_amount = _calculate_orders_stats(breach_end_orders)

    return {
        **new_stats,
        "completed_orders_count": completed_count,
        "completed_amount": completed_amount,
        "breach_orders_count": breach_count,
        "breach_amount": breach_amount,
        "breach_end_orders_count": breach_end_count,
        "breach_end_amount": breach_end_amount,
    }


async def _get_daily_financial_data(date: str) -> Dict:
    """获取当日财务数据

    Args:
        date: 日期字符串

    Returns:
        财务数据字典
    """
    daily_interest = await db_operations.get_daily_interest_total(date)
    expenses = await db_operations.get_daily_expenses(date)

    return {
        "daily_interest": daily_interest,
        "company_expenses": expenses.get("company_expenses", 0.0),
        "other_expenses": expenses.get("other_expenses", 0.0),
    }


def _get_empty_summary() -> Dict:
    """获取空摘要数据

    Returns:
        空摘要字典
    """
    return {
        "new_clients_count": 0,
        "new_clients_amount": 0.0,
        "old_clients_count": 0,
        "old_clients_amount": 0.0,
        "completed_orders_count": 0,
        "completed_amount": 0.0,
        "breach_orders_count": 0,
        "breach_amount": 0.0,
        "breach_end_orders_count": 0,
        "breach_end_amount": 0.0,
        "daily_interest": 0.0,
        "company_expenses": 0.0,
        "other_expenses": 0.0,
    }


async def calculate_daily_summary(date: str) -> Dict:
    """计算指定日期的日切数据"""
    try:
        orders_data = await _get_daily_orders_data(date)
        financial_data = await _get_daily_financial_data(date)
        return {**orders_data, **financial_data}
    except Exception as e:
        logger.error(f"计算日切数据失败: {e}", exc_info=True)
        return _get_empty_summary()


async def _prepare_daily_report_data(date: str) -> Tuple[Dict, str]:
    """准备日切报表数据

    Args:
        date: 日期

    Returns:
        (汇总数据, 订单总表文本)
    """
    summary = await calculate_daily_summary(date)
    await db_operations.save_daily_summary(date, summary)

    valid_orders = await db_operations.get_all_valid_orders()
    daily_interest = summary.get("daily_interest", 0.0)
    order_table = await generate_order_table(valid_orders, daily_interest)

    return summary, order_table


def _build_daily_summary_section(summary: Dict) -> str:
    """构建日切数据汇总部分

    Args:
        summary: 汇总数据

    Returns:
        汇总部分文本
    """
    report = "日切数据汇总\n"
    report += "═══════════════════════════════════════\n"
    report += f"新客户订单: {summary.get('new_clients_count', 0)} 个, "
    report += f"金额: {summary.get('new_clients_amount', 0.0):,.2f}\n"
    report += f"老客户订单: {summary.get('old_clients_count', 0)} 个, "
    report += f"金额: {summary.get('old_clients_amount', 0.0):,.2f}\n"
    report += f"完成订单: {summary.get('completed_orders_count', 0)} 个, "
    report += f"金额: {summary.get('completed_amount', 0.0):,.2f}\n"
    report += f"违约订单: {summary.get('breach_orders_count', 0)} 个, "
    report += f"金额: {summary.get('breach_amount', 0.0):,.2f}\n"
    report += f"违约完成: {summary.get('breach_end_orders_count', 0)} 个, "
    report += f"金额: {summary.get('breach_end_amount', 0.0):,.2f}\n"
    report += f"当日利息: {summary.get('daily_interest', 0.0):,.2f}\n"
    report += f"公司开销: {summary.get('company_expenses', 0.0):,.2f}\n"
    report += f"其他开销: {summary.get('other_expenses', 0.0):,.2f}\n"
    total_expenses = summary.get("company_expenses", 0.0) + summary.get(
        "other_expenses", 0.0
    )
    report += f"总开销: {total_expenses:,.2f}\n"
    report += "═══════════════════════════════════════\n\n"
    return report


async def _build_daily_orders_sections(date: str) -> str:
    """构建订单列表部分

    Args:
        date: 日期

    Returns:
        订单列表部分文本
    """
    sections = ""

    completed_orders = await db_operations.get_completed_orders_by_date(date)
    if completed_orders:
        completed_table = await generate_completed_orders_table(completed_orders)
        sections += completed_table + "\n"

    breach_end_orders = await db_operations.get_breach_end_orders_by_date(date)
    if breach_end_orders:
        breach_table = await generate_breach_end_orders_table(breach_end_orders)
        sections += breach_table + "\n"

    return sections


async def generate_daily_report(date: str) -> str:
    """生成日切报表"""
    try:
        summary, order_table = await _prepare_daily_report_data(date)

        report = f"📊 日切报表 ({date})\n"
        report += "═══════════════════════════════════════\n\n"
        report += order_table + "\n\n"

        report += _build_daily_summary_section(summary)
        report += await _build_daily_orders_sections(date)

        return report
    except Exception as e:
        logger.error(f"生成日切报表失败: {e}", exc_info=True)
        return f"❌ 生成日切报表失败: {e}"
