"""订单分类表初始化 - 客户分类模块

包含创建按客户类型分类表的逻辑。
"""

import sqlite3


def create_customer_tables(cursor: sqlite3.Cursor, schema: str) -> None:
    """创建按客户类型分类表

    Args:
        cursor: 数据库游标
        schema: 表结构SQL
    """
    customer_tables = ["orders_new_customers", "orders_old_customers"]
    for table_name in customer_tables:
        try:
            cursor.execute(schema.format(table_name))
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
