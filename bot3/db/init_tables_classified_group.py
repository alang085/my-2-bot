"""订单分类表初始化 - 归属分类模块

包含创建按归属ID分类表的逻辑。
"""

import sqlite3


def create_group_tables(cursor: sqlite3.Cursor, schema: str) -> None:
    """创建按归属ID分类表

    Args:
        cursor: 数据库游标
        schema: 表结构SQL
    """
    # 按归属ID分类表（动态创建，先创建常见的）
    # 注意：归属ID分类表会在运行时动态创建，这里只创建已知的
    known_group_ids = ["S01", "S02", "S03", "S04", "S05"]
    for group_id in known_group_ids:
        table_name = f"orders_{group_id}"
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
