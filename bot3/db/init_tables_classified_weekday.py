"""订单分类表初始化 - 星期分类模块

包含创建按星期分组分类表的逻辑。
"""

import sqlite3


def create_weekday_tables(cursor: sqlite3.Cursor, schema: str) -> None:
    """创建按星期分组分类表

    Args:
        cursor: 数据库游标
        schema: 表结构SQL
    """
    weekday_tables = [
        "orders_monday",
        "orders_tuesday",
        "orders_wednesday",
        "orders_thursday",
        "orders_friday",
        "orders_saturday",
        "orders_sunday",
    ]
    for table_name in weekday_tables:
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
            cursor.execute(
                f"""
            CREATE INDEX IF NOT EXISTS idx_{table_name}_date ON {table_name}(date)
            """
            )
        except sqlite3.OperationalError:
            pass
