"""客户订单汇总 - 查询模块

包含查询订单和收入记录的逻辑。
"""

import sqlite3
from typing import Dict, List


def query_customer_orders(
    cursor: sqlite3.Cursor, customer: str, start_date: str = None, end_date: str = None
) -> List[Dict]:
    """查询客户订单

    Args:
        cursor: 数据库游标
        customer: 客户类型
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        List[Dict]: 订单列表
    """
    # 构建查询条件
    conditions = ["customer = ?"]
    params = [customer.upper()]

    if start_date:
        conditions.append("date >= ?")
        params.append(start_date)

    if end_date:
        conditions.append("date <= ?")
        params.append(end_date)

    where_clause = " AND ".join(conditions)

    # 查询所有订单
    cursor.execute(
        f"""
    SELECT * FROM orders
    WHERE {where_clause}
    ORDER BY date DESC
    """,
        params,
    )

    order_rows = cursor.fetchall()
    orders = [dict(row) for row in order_rows]

    return orders


def _initialize_income_map() -> Dict[str, float]:
    """初始化收入映射字典

    Returns:
        初始化的收入映射字典
    """
    return {
        "interest": 0.0,
        "completed": 0.0,
        "breach_end": 0.0,
        "principal_reduction": 0.0,
        "total": 0.0,
    }


def _update_income_map_by_type(
    income_map: Dict[str, Dict], order_id: str, income_type: str, amount: float
) -> None:
    """根据收入类型更新收入映射

    Args:
        income_map: 收入映射字典
        order_id: 订单ID
        income_type: 收入类型
        amount: 金额
    """
    if income_type == "interest":
        income_map[order_id]["interest"] = amount
    elif income_type == "completed":
        income_map[order_id]["completed"] = amount
    elif income_type == "breach_end":
        income_map[order_id]["breach_end"] = amount
    elif income_type == "principal_reduction":
        income_map[order_id]["principal_reduction"] = amount

    income_map[order_id]["total"] += amount


def _build_income_map_from_rows(income_rows: List) -> Dict[str, Dict]:
    """从查询结果构建收入映射

    Args:
        income_rows: 查询结果行列表

    Returns:
        收入映射字典
    """
    income_map = {}
    for row in income_rows:
        order_id = row[0]
        income_type = row[1]
        amount = row[3] or 0.0

        if order_id not in income_map:
            income_map[order_id] = _initialize_income_map()

        _update_income_map_by_type(income_map, order_id, income_type, amount)

    return income_map


def query_order_incomes(
    cursor: sqlite3.Cursor, order_ids: List[str]
) -> Dict[str, Dict]:
    """批量查询订单收入汇总

    Args:
        cursor: 数据库游标
        order_ids: 订单ID列表

    Returns:
        Dict: 订单收入映射表
    """
    if not order_ids:
        return {}

    placeholders = ",".join(["?"] * len(order_ids))

    cursor.execute(
        f"""
        SELECT
            order_id,
            type,
            COUNT(*) as count,
            SUM(amount) as total_amount
        FROM income_records
        WHERE order_id IN ({placeholders})
        GROUP BY order_id, type
        """,
        order_ids,
    )

    income_rows = cursor.fetchall()
    return _build_income_map_from_rows(income_rows)
