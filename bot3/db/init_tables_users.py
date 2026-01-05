"""用户和权限相关表初始化模块

包含用户授权和归属映射表的创建逻辑。
"""

import sqlite3


def create_user_tables(cursor: sqlite3.Cursor) -> None:
    """创建用户和权限相关表"""
    # 创建授权用户表（员工）
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS authorized_users (
        user_id INTEGER PRIMARY KEY,
        added_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """
    )

    # 创建用户归属ID映射表（用于限制用户只能查看特定归属ID的报表）
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS user_group_mapping (
        user_id INTEGER PRIMARY KEY,
        group_id TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """
    )
