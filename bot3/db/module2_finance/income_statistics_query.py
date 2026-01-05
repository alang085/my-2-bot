"""收入统计 - 查询模块

包含构建查询条件和执行查询的逻辑。
"""

import sqlite3
from typing import List, Optional, Tuple


def build_customer_query_conditions(
    customer: str, start_date: Optional[str] = None, end_date: Optional[str] = None
) -> Tuple[str, List, str, List]:
    """构建客户查询条件

    Args:
        customer: 客户类型
        start_date: 起始日期
        end_date: 结束日期

    Returns:
        Tuple: (income_where, income_params, order_where, order_params)
    """
    income_conditions = ["customer = ?"]
    income_params = [customer.upper()]

    order_conditions = ["customer = ?"]
    order_params = [customer.upper()]

    if start_date:
        income_conditions.append("date >= ?")
        income_params.append(start_date)
        order_conditions.append("date >= ?")
        order_params.append(start_date)

    if end_date:
        income_conditions.append("date <= ?")
        income_params.append(end_date)
        order_conditions.append("date <= ?")
        order_params.append(end_date)

    income_where = " AND ".join(income_conditions)
    order_where = " AND ".join(order_conditions)

    return income_where, income_params, order_where, order_params


def query_income_summary(
    cursor: sqlite3.Cursor, income_where: str, income_params: List
) -> List:
    """查询收入汇总

    Args:
        cursor: 数据库游标
        income_where: WHERE条件
        income_params: 参数列表

    Returns:
        List: 收入行数据
    """
    cursor.execute(
        f"""
    SELECT
        type,
        COUNT(*) as count,
        SUM(amount) as total_amount
    FROM income_records
    WHERE {income_where}
    GROUP BY type
    """,
        income_params,
    )

    return cursor.fetchall()


def query_order_stats(
    cursor: sqlite3.Cursor, order_where: str, order_params: List
) -> Optional[tuple]:
    """查询订单统计

    Args:
        cursor: 数据库游标
        order_where: WHERE条件
        order_params: 参数列表

    Returns:
        Optional[tuple]: 订单统计行数据
    """
    cursor.execute(
        f"""
    SELECT
        COUNT(*) as order_count,
        MIN(date) as first_date,
        MAX(date) as last_date
    FROM orders
    WHERE {order_where}
    """,
        order_params,
    )

    return cursor.fetchone()
