"""开销记录 - 财务数据更新模块

包含更新财务数据的逻辑。
"""

import sqlite3


def update_financial_data_for_expense(cursor: sqlite3.Cursor, amount: float) -> float:
    """更新财务数据（开销）

    Args:
        cursor: 数据库游标
        amount: 开销金额

    Returns:
        float: 新的流动资金
    """
    cursor.execute("SELECT * FROM financial_data ORDER BY id DESC LIMIT 1")
    financial_row = cursor.fetchone()

    if not financial_row:
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
        current_liquid_funds = 0
    else:
        current_liquid_funds = dict(financial_row).get("liquid_funds", 0)

    new_liquid_funds = current_liquid_funds - amount

    cursor.execute(
        """
    UPDATE financial_data
    SET "liquid_funds" = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = (SELECT id FROM financial_data ORDER BY id DESC LIMIT 1)
    """,
        (new_liquid_funds,),
    )

    return new_liquid_funds
