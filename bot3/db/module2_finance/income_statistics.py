"""收入统计操作模块

包含收入相关的统计功能。
"""

from typing import Dict, List, Optional

# 本地模块
from db.base import db_query
from utils.income_helpers import calculate_income_statistics


@db_query
def get_customer_total_contribution(
    conn, cursor, customer: str, start_date: str = None, end_date: str = None
) -> Dict:
    """获取指定客户的总贡献（跨所有订单周期）

    参数:
        customer: 客户类型（'A'=新客户，'B'=老客户）
        start_date: 起始日期（可选，如果提供则只统计该日期之后的数据）
        end_date: 结束日期（可选，如果提供则只统计该日期之前的数据）

    返回:
        {
            'total_interest': 总利息收入,
            'total_completed': 总完成订单金额,
            'total_breach_end': 总违约完成金额,
            'total_principal_reduction': 总本金减少,
            'total_amount': 总贡献金额,
            'order_count': 订单数量,
            'interest_count': 利息收取次数,
            'first_order_date': 首次订单日期,
            'last_order_date': 最后订单日期
        }
    """
    from db.module2_finance.income_statistics_assemble import \
        assemble_customer_contribution
    from db.module2_finance.income_statistics_query import (
        build_customer_query_conditions, query_income_summary,
        query_order_stats)

    # 构建查询条件
    income_where, income_params, order_where, order_params = (
        build_customer_query_conditions(customer, start_date, end_date)
    )

    # 查询收入汇总
    income_rows = query_income_summary(cursor, income_where, income_params)

    # 查询订单统计
    order_row = query_order_stats(cursor, order_where, order_params)

    # 组装结果
    return assemble_customer_contribution(
        income_rows, order_row, calculate_income_statistics
    )


@db_query
def get_customer_orders_summary(
    conn, cursor, customer: str, start_date: str = None, end_date: str = None
) -> List[Dict]:
    """获取指定客户的所有订单及每笔订单的贡献汇总

    返回每个订单的详细信息，包括：
    - 订单基本信息
    - 该订单的利息总额
    - 该订单的完成金额
    - 该订单的总贡献
    """
    from db.module2_finance.income_summary_assemble import \
        assemble_order_summary
    from db.module2_finance.income_summary_query import (query_customer_orders,
                                                         query_order_incomes)

    # 查询订单
    orders = query_customer_orders(cursor, customer, start_date, end_date)

    if not orders:
        return []

    # 批量查询收入汇总
    order_ids = [order["order_id"] for order in orders]
    income_map = query_order_incomes(cursor, order_ids)

    # 组装结果
    result = assemble_order_summary(orders, income_map)

    return result


@db_query
def get_income_summary_by_type(
    conn, cursor, start_date: str, end_date: str = None, group_id: Optional[str] = None
) -> Dict:
    """按收入类型和客户类型汇总（排除已撤销的记录）"""
    query = """
    SELECT
        type,
        customer,
        COUNT(*) as count,
        SUM(amount) as total_amount
    FROM income_records
    WHERE date >= ? AND date <= ?
    AND (is_undone IS NULL OR is_undone = 0)
    """
    params = [start_date, end_date or start_date]

    if group_id:
        query += " AND group_id = ?"
        params.append(group_id)

    query += " GROUP BY type, customer ORDER BY type, customer"

    cursor.execute(query, params)
    rows = cursor.fetchall()

    # 构建汇总字典
    summary = {}
    for row in rows:
        type_name = row[0]
        customer_type = row[1] or "None"
        count = row[2]
        total = row[3]

        if type_name not in summary:
            summary[type_name] = {}
        summary[type_name][customer_type] = {"count": count, "total": total}

    return summary


@db_query
def get_income_summary_by_group(
    conn, cursor, start_date: str, end_date: str = None
) -> Dict:
    """按归属ID汇总收入（排除已撤销的记录）"""
    query = """
    SELECT
        group_id,
        COUNT(*) as count,
        SUM(amount) as total_amount
    FROM income_records
    WHERE date >= ? AND date <= ?
    AND (is_undone IS NULL OR is_undone = 0)
    GROUP BY group_id
    ORDER BY total_amount DESC
    """
    params = [start_date, end_date or start_date]

    cursor.execute(query, params)
    rows = cursor.fetchall()

    summary = {}
    for row in rows:
        group_id = row[0] or "NULL"
        count = row[1]
        total = row[2]
        summary[group_id] = {"count": count, "total": total}

    return summary
