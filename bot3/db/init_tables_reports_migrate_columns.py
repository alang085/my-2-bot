"""报表表初始化 - 列迁移模块

包含添加和迁移列的逻辑。
"""

import logging
import sqlite3
from typing import List

logger = logging.getLogger(__name__)


def add_column_if_missing(
    cursor: sqlite3.Cursor,
    conn: sqlite3.Connection,
    columns: List[str],
    column_name: str,
    column_type: str,
) -> None:
    """如果列不存在则添加

    Args:
        cursor: 数据库游标
        conn: 数据库连接
        columns: 现有列列表
        column_name: 列名
        column_type: 列类型（如 'INTEGER DEFAULT 0' 或 'REAL DEFAULT 0'）
    """
    if column_name not in columns:
        try:
            cursor.execute(
                f"ALTER TABLE daily_summary ADD COLUMN {column_name} {column_type}"
            )
            conn.commit()
            logger.info(f"已添加列: {column_name}")
        except sqlite3.OperationalError as e:
            logger.warning(f"添加列 {column_name} 时出错（可能已存在）: {e}")


def migrate_column_rename(
    cursor: sqlite3.Cursor,
    conn: sqlite3.Connection,
    columns: List[str],
    old_column: str,
    new_column: str,
) -> None:
    """迁移列重命名（添加新列并迁移数据）

    Args:
        cursor: 数据库游标
        conn: 数据库连接
        columns: 现有列列表
        old_column: 旧列名
        new_column: 新列名
    """
    if old_column in columns and new_column not in columns:
        try:
            cursor.execute(
                f"ALTER TABLE daily_summary ADD COLUMN {new_column} REAL DEFAULT 0"
            )
            conn.commit()
            # 迁移旧数据
            cursor.execute(
                f"UPDATE daily_summary SET {new_column} = {old_column} WHERE {new_column} = 0"
            )
            conn.commit()
            logger.info(f"已添加列: {new_column} 并迁移数据")
        except sqlite3.OperationalError as e:
            logger.warning(f"添加列 {new_column} 时出错（可能已存在）: {e}")
