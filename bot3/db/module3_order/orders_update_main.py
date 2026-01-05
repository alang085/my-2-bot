"""订单更新 - 主表更新模块

包含更新主表的逻辑。
"""

from typing import Any, Dict


def update_main_table(cursor, chat_id: int, new_order_data: Dict[str, Any]) -> bool:
    """更新主表

    Args:
        cursor: 数据库游标
        chat_id: 聊天ID
        new_order_data: 新订单数据

    Returns:
        bool: 是否成功更新
    """
    cursor.execute(
        """
        UPDATE orders
        SET order_id = ?, date = ?, weekday_group = ?,
            customer = ?, amount = ?, state = ?, updated_at = ?
        WHERE chat_id = ? AND state NOT IN (?, ?)
        """,
        (
            new_order_data["order_id"],
            new_order_data["date"],
            new_order_data["weekday_group"],
            new_order_data["customer"],
            new_order_data["amount"],
            new_order_data["state"],
            new_order_data["updated_at"],
            chat_id,
            "end",
            "breach_end",
        ),
    )

    return cursor.rowcount > 0
