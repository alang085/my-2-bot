"""日结数据更新 - 初始化模块

包含初始化日结数据的逻辑。
"""

import sqlite3
from typing import Optional


def init_daily_data_if_needed(
    cursor: sqlite3.Cursor, date: str, group_id: Optional[str]
) -> None:
    """如果需要，初始化日结数据

    Args:
        cursor: 数据库游标
        date: 日期
        group_id: 归属ID
    """
    if group_id:
        cursor.execute(
            "SELECT * FROM daily_data WHERE date = ? AND group_id = ?", (date, group_id)
        )
    else:
        cursor.execute(
            "SELECT * FROM daily_data WHERE date = ? AND group_id IS NULL", (date,)
        )

    row = cursor.fetchone()

    if not row:
        cursor.execute(
            """
        INSERT INTO daily_data (
            date, group_id, new_clients, new_clients_amount,
            old_clients, old_clients_amount,
            interest, completed_orders, completed_amount,
            breach_orders, breach_amount,
            breach_end_orders, breach_end_amount,
            liquid_flow, company_expenses, other_expenses
        ) VALUES (?, ?, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        """,
            (date, group_id),
        )
