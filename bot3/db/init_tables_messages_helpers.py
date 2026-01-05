"""消息表初始化辅助函数

包含消息表初始化的辅助函数，提取重复代码。
"""

import sqlite3


def _add_column_if_not_exists(
    cursor: sqlite3.Cursor, table_name: str, column_name: str, column_type: str = "TEXT"
) -> None:
    """添加列（如果不存在）

    Args:
        cursor: 数据库游标
        table_name: 表名
        column_name: 列名
        column_type: 列类型，默认为TEXT
    """
    try:
        cursor.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        )
    except sqlite3.OperationalError:
        pass  # 字段已存在


def _add_weekday_message_columns(cursor: sqlite3.Cursor, prefix: str) -> None:
    """添加按星期轮换的消息字段（7个字段，1=周一，7=周日）

    Args:
        cursor: 数据库游标
        prefix: 字段前缀（如 start_work_message, end_work_message）
    """
    for i in range(1, 8):
        column_name = f"{prefix}_{i}"
        _add_column_if_not_exists(cursor, "group_message_config", column_name)


def migrate_group_message_config_fields(cursor: sqlite3.Cursor) -> None:
    """迁移group_message_config表结构（添加新字段）

    Args:
        cursor: 数据库游标
    """
    # 添加bot_links和worker_links字段
    _add_column_if_not_exists(cursor, "group_message_config", "bot_links")
    _add_column_if_not_exists(cursor, "group_message_config", "worker_links")

    # 添加按星期轮换的消息字段
    _add_weekday_message_columns(cursor, "start_work_message")
    _add_weekday_message_columns(cursor, "end_work_message")
    _add_weekday_message_columns(cursor, "welcome_message")
    _add_weekday_message_columns(cursor, "anti_fraud_message")
