"""收入查询操作模块

包含收入相关的查询功能。
"""

# 标准库
from datetime import datetime
from typing import Dict, List, Optional

# 本地模块
from db.base import db_query, db_transaction
from utils.date_helpers import get_date_range_for_query


@db_query
def get_all_valid_orders(conn, cursor) -> List[Dict]:
    """获取所有有效订单（normal和overdue状态）"""
    cursor.execute(
        """
    SELECT * FROM orders
    WHERE state IN ('normal', 'overdue')
    ORDER BY date DESC, order_id DESC
    """
    )
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


@db_query
def get_completed_orders_by_date(conn, cursor, date: str) -> List[Dict]:
    """获取指定日期完成的订单（通过updated_at判断，使用北京时间范围）"""
    start_time, end_time = get_date_range_for_query(date)
    cursor.execute(
        """
    SELECT * FROM orders
    WHERE state = 'end'
    AND updated_at >= ? AND updated_at <= ?
    ORDER BY updated_at DESC
    """,
        (start_time, end_time),
    )
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


@db_query
def get_breach_orders_by_date(conn, cursor, date: str) -> List[Dict]:
    """获取指定日期状态变为违约的订单（通过updated_at判断，使用北京时间范围）"""
    start_time, end_time = get_date_range_for_query(date)
    cursor.execute(
        """
    SELECT * FROM orders
    WHERE state = 'breach'
    AND updated_at >= ? AND updated_at <= ?
    ORDER BY updated_at DESC
    """,
        (start_time, end_time),
    )
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


@db_query
def get_breach_end_orders_by_date(conn, cursor, date: str) -> List[Dict]:
    """获取指定日期违约完成且有变动的订单（通过updated_at判断，使用北京时间范围）"""
    start_time, end_time = get_date_range_for_query(date)
    cursor.execute(
        """
    SELECT * FROM orders
    WHERE state = 'breach_end'
    AND updated_at >= ? AND updated_at <= ?
    ORDER BY updated_at DESC
    """,
        (start_time, end_time),
    )
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


@db_query
def get_new_orders_by_date(conn, cursor, date: str) -> List[Dict]:
    """获取指定日期新增的订单（通过created_at判断，使用北京时间范围）"""
    start_time, end_time = get_date_range_for_query(date)
    cursor.execute(
        """
    SELECT * FROM orders
    WHERE created_at >= ? AND created_at <= ?
    ORDER BY created_at DESC
    """,
        (start_time, end_time),
    )
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


@db_query
def get_daily_interest_total(conn, cursor, date: str) -> float:
    """获取指定日期的利息收入总额（排除已撤销的记录）"""
    cursor.execute(
        """
    SELECT COALESCE(SUM(amount), 0) as total
    FROM income_records
    WHERE date = ? AND type = 'interest' AND (is_undone IS NULL OR is_undone = 0)
    """,
        (date,),
    )
    row = cursor.fetchone()
    return float(row[0]) if row and row[0] else 0.0


@db_query
def get_daily_expenses(conn, cursor, date: str) -> Dict:
    """获取指定日期的开销（公司开销+其他开销）"""
    cursor.execute(
        """
    SELECT
        type,
        COALESCE(SUM(amount), 0) as total
    FROM expense_records
    WHERE date = ?
    GROUP BY type
    """,
        (date,),
    )
    rows = cursor.fetchall()

    result = {"company_expenses": 0.0, "other_expenses": 0.0, "total": 0.0}

    for row in rows:
        expense_type = row[0]
        amount = float(row[1]) if row[1] else 0.0
        if expense_type == "company":
            result["company_expenses"] = amount
        elif expense_type == "other":
            result["other_expenses"] = amount
        result["total"] += amount

    return result


@db_query
def get_daily_summary(conn, cursor, date: str) -> Optional[Dict]:
    """获取指定日期的日切数据"""
    cursor.execute(
        """
    SELECT * FROM daily_summary
    WHERE date = ?
    """,
        (date,),
    )
    row = cursor.fetchone()
    if row:
        return dict(row)
    return None


@db_transaction
def save_daily_summary(conn, cursor, date: str, data: Dict) -> bool:
    """保存日切数据"""
    try:
        cursor.execute(
            """
        INSERT OR REPLACE INTO daily_summary (
            date, new_clients_count, new_clients_amount,
            old_clients_count, old_clients_amount,
            completed_orders_count, completed_amount,
            breach_orders_count, breach_amount,
            breach_end_orders_count, breach_end_amount,
            daily_interest, company_expenses, other_expenses,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                date,
                data.get("new_clients_count", 0),
                data.get("new_clients_amount", 0.0),
                data.get("old_clients_count", 0),
                data.get("old_clients_amount", 0.0),
                data.get("completed_orders_count", 0),
                data.get("completed_amount", 0.0),
                data.get("breach_orders_count", 0),
                data.get("breach_amount", 0.0),
                data.get("breach_end_orders_count", 0),
                data.get("breach_end_amount", 0.0),
                data.get("daily_interest", 0.0),
                data.get("company_expenses", 0.0),
                data.get("other_expenses", 0.0),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
