"""订单分类表初始化 - 状态分类模块

包含创建按状态分类表的逻辑。
"""

import sqlite3


def create_state_tables(cursor: sqlite3.Cursor, schema: str) -> None:
    """创建按状态分类表

    Args:
        cursor: 数据库游标
        schema: 表结构SQL
    """
    state_tables = [
        "orders_normal",
        "orders_overdue",
        "orders_breach",
        "orders_end",
        "orders_breach_end",
    ]
    for table_name in state_tables:
        try:
            cursor.execute(schema.format(table_name))
            # 创建索引
            cursor.execute(
                f"""
            CREATE INDEX IF NOT EXISTS idx_{table_name}_order_id ON {table_name}(order_id)
            """
            )
            cursor.execute(
                f"""
            CREATE INDEX IF NOT EXISTS idx_{table_name}_chat_id ON {table_name}(chat_id)
            """
            )
        except sqlite3.OperationalError:
            pass
