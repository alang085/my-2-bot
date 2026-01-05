"""订单搜索操作模块

包含订单的搜索功能。
"""

from typing import Dict, List, Optional

# 本地模块
from db.base import db_query


@db_query
def search_orders_by_group_id(
    conn, cursor, group_id: str, state: Optional[str] = None
) -> List[Dict]:
    """根据归属ID查找订单"""
    if state:
        cursor.execute(
            "SELECT * FROM orders WHERE group_id = ? AND state = ? ORDER BY date DESC",
            (group_id, state),
        )
    else:
        # 默认排除完成和违约完成的订单
        cursor.execute(
            (
                "SELECT * FROM orders WHERE group_id = ? "
                "AND state NOT IN ('end', 'breach_end') ORDER BY date DESC"
            ),
            (group_id,),
        )
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


@db_query
def search_orders_by_date_range(
    conn, cursor, start_date: str, end_date: str
) -> List[Dict]:
    """根据日期范围查找订单"""
    cursor.execute(
        """
    SELECT * FROM orders
    WHERE date >= ? AND date <= ?
    ORDER BY date DESC
    """,
        (start_date, end_date),
    )
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


@db_query
def search_orders_by_customer(conn, cursor, customer: str) -> List[Dict]:
    """根据客户类型查找订单"""
    cursor.execute(
        "SELECT * FROM orders WHERE customer = ? ORDER BY date DESC",
        (customer.upper(),),
    )
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


@db_query
def search_orders_by_state(conn, cursor, state: str) -> List[Dict]:
    """根据状态查找订单"""
    cursor.execute("SELECT * FROM orders WHERE state = ? ORDER BY date DESC", (state,))
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


@db_query
def search_orders_all(conn, cursor) -> List[Dict]:
    """查找所有订单"""
    cursor.execute("SELECT * FROM orders ORDER BY date DESC")
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


@db_query
def search_orders_advanced(conn, cursor, criteria: Dict) -> List[Dict]:
    """
    高级查找订单（支持混合条件）
    """
    query = "SELECT * FROM orders WHERE 1=1"
    params = []

    if "group_id" in criteria and criteria["group_id"]:
        query += " AND group_id = ?"
        params.append(criteria["group_id"])

    if "state" in criteria and criteria["state"]:
        query += " AND state = ?"
        params.append(criteria["state"])
    else:
        # 默认只查找有效订单（normal和overdue状态）
        query += " AND state IN ('normal', 'overdue')"

    if "customer" in criteria and criteria["customer"]:
        query += " AND customer = ?"
        params.append(criteria["customer"])

    if "order_id" in criteria and criteria["order_id"]:
        query += " AND order_id = ?"
        params.append(criteria["order_id"])

    if "date_range" in criteria and criteria["date_range"]:
        start_date, end_date = criteria["date_range"]
        query += " AND date >= ? AND date <= ?"
        params.extend([start_date, end_date])

    if "weekday_group" in criteria and criteria["weekday_group"]:
        query += " AND weekday_group = ?"
        params.append(criteria["weekday_group"])

    query += " ORDER BY date DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


@db_query
def search_orders_advanced_all_states(conn, cursor, criteria: Dict) -> List[Dict]:
    """
    高级查找订单（支持混合条件，包含所有状态的订单）
    用于报表查找功能
    """
    query = "SELECT * FROM orders WHERE 1=1"
    params = []

    if "group_id" in criteria and criteria["group_id"]:
        query += " AND group_id = ?"
        params.append(criteria["group_id"])

    if "state" in criteria and criteria["state"]:
        query += " AND state = ?"
        params.append(criteria["state"])

    if "customer" in criteria and criteria["customer"]:
        query += " AND customer = ?"
        params.append(criteria["customer"])

    if "order_id" in criteria and criteria["order_id"]:
        query += " AND order_id = ?"
        params.append(criteria["order_id"])

    if "date_range" in criteria and criteria["date_range"]:
        start_date, end_date = criteria["date_range"]
        query += " AND date >= ? AND date <= ?"
        params.extend([start_date, end_date])

    if "weekday_group" in criteria and criteria["weekday_group"]:
        query += " AND weekday_group = ?"
        params.append(criteria["weekday_group"])

    query += " ORDER BY date DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    return [dict(row) for row in rows]
