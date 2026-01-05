"""财务表初始化辅助函数

包含财务表初始化的辅助函数，提取重复代码。
"""

import sqlite3


def _add_column_if_not_exists_with_commit(
    cursor: sqlite3.Cursor,
    conn: sqlite3.Connection,
    table_name: str,
    column_name: str,
    column_type: str = "REAL",
    default_value: str = "0",
) -> bool:
    """添加列（如果不存在）并提交

    Args:
        cursor: 数据库游标
        conn: 数据库连接
        table_name: 表名
        column_name: 列名
        column_type: 列类型，默认为REAL
        default_value: 默认值，默认为"0"

    Returns:
        是否成功添加列
    """
    try:
        cursor.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} DEFAULT {default_value}"
        )
        conn.commit()
        print(f"已添加列: {column_name}")
        return True
    except sqlite3.OperationalError as e:
        print(f"添加列 {column_name} 时出错（可能已存在）: {e}")
        return False


def migrate_daily_data_columns(
    cursor: sqlite3.Cursor, conn: sqlite3.Connection
) -> None:
    """迁移daily_data表结构（添加缺失的列）

    Args:
        cursor: 数据库游标
        conn: 数据库连接
    """
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='daily_data'"
    )
    table_exists = cursor.fetchone()

    if not table_exists:
        return

    cursor.execute("PRAGMA table_info(daily_data)")
    columns = [row[1] for row in cursor.fetchall()]

    # 需要添加的列列表
    columns_to_add = [
        ("liquid_flow", "REAL", "0"),
        ("company_expenses", "REAL", "0"),
        ("other_expenses", "REAL", "0"),
    ]

    for column_name, column_type, default_value in columns_to_add:
        if column_name not in columns:
            _add_column_if_not_exists_with_commit(
                cursor, conn, "daily_data", column_name, column_type, default_value
            )
