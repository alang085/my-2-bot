"""财务数据更新 - 初始化模块

包含初始化财务数据的逻辑。
"""

import sqlite3


def init_financial_data_if_needed(cursor: sqlite3.Cursor) -> None:
    """如果需要，初始化财务数据

    Args:
        cursor: 数据库游标
    """
    cursor.execute("SELECT * FROM financial_data ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()

    if not row:
        # 检查表是否有overdue字段（兼容旧数据库）
        cursor.execute("PRAGMA table_info(financial_data)")
        columns = [col[1] for col in cursor.fetchall()]
        has_overdue = "overdue_orders" in columns and "overdue_amount" in columns

        if has_overdue:
            cursor.execute(
                """
            INSERT INTO financial_data (
                valid_orders, valid_amount, liquid_funds,
                new_clients, new_clients_amount,
                old_clients, old_clients_amount,
                interest, completed_orders, completed_amount,
                breach_orders, breach_amount,
                breach_end_orders, breach_end_amount,
                overdue_orders, overdue_amount
            ) VALUES (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            """
            )
        else:
            cursor.execute(
                """
            INSERT INTO financial_data (
                valid_orders, valid_amount, liquid_funds,
                new_clients, new_clients_amount,
                old_clients, old_clients_amount,
                interest, completed_orders, completed_amount,
                breach_orders, breach_amount,
                breach_end_orders, breach_end_amount
            ) VALUES (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            """
            )
