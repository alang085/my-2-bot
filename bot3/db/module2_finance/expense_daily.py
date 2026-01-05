"""开销记录 - 日结数据更新模块

包含更新日结数据的逻辑。
"""

import sqlite3
from typing import Tuple


def _calculate_expense_amounts(field: str, amount: float) -> Tuple[float, float]:
    """计算开销金额

    Args:
        field: 开销字段名
        amount: 开销金额

    Returns:
        (公司开销金额, 其他开销金额)
    """
    company_amount = amount if field == "company_expenses" else 0
    other_amount = amount if field == "other_expenses" else 0
    return company_amount, other_amount


def _insert_new_daily_expense_record(
    cursor: sqlite3.Cursor,
    date: str,
    amount: float,
    company_amount: float,
    other_amount: float,
) -> None:
    """插入新的日结开销记录

    Args:
        cursor: 数据库游标
        date: 日期
        amount: 开销金额
        company_amount: 公司开销金额
        other_amount: 其他开销金额
    """
    cursor.execute(
        """
    INSERT INTO daily_data (
        date, group_id, new_clients, new_clients_amount,
        old_clients, old_clients_amount,
        interest, completed_orders, completed_amount,
        breach_orders, breach_amount,
        breach_end_orders, breach_end_amount,
        liquid_flow, company_expenses, other_expenses
    ) VALUES (?, NULL, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ?, ?, ?)
    """,
        (date, -amount, company_amount, other_amount),
    )


def _update_existing_daily_expense(
    cursor: sqlite3.Cursor, date: str, field: str, amount: float
) -> None:
    """更新现有日结开销记录

    Args:
        cursor: 数据库游标
        date: 日期
        field: 开销字段名
        amount: 开销金额
    """
    if field == "company_expenses":
        cursor.execute(
            """
        UPDATE daily_data
        SET company_expenses = company_expenses + ?,
            liquid_flow = liquid_flow - ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE date = ? AND group_id IS NULL
        """,
            (amount, amount, date),
        )
    else:  # other_expenses
        cursor.execute(
            """
        UPDATE daily_data
        SET other_expenses = other_expenses + ?,
            liquid_flow = liquid_flow - ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE date = ? AND group_id IS NULL
        """,
            (amount, amount, date),
        )


def update_daily_data_for_expense(
    cursor: sqlite3.Cursor, date: str, field: str, amount: float
) -> None:
    """更新日结数据（开销）

    Args:
        cursor: 数据库游标
        date: 日期
        field: 开销字段名
        amount: 开销金额
    """
    cursor.execute(
        "SELECT * FROM daily_data WHERE date = ? AND group_id IS NULL", (date,)
    )
    daily_row = cursor.fetchone()

    company_amount, other_amount = _calculate_expense_amounts(field, amount)

    if not daily_row:
        _insert_new_daily_expense_record(
            cursor, date, amount, company_amount, other_amount
        )
    else:
        _update_existing_daily_expense(cursor, date, field, amount)
