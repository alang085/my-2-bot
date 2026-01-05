"""财务表初始化 - 分组数据表模块

包含创建分组数据表的逻辑。
"""

import sqlite3


def create_grouped_data_table(cursor: sqlite3.Cursor) -> None:
    """创建分组数据表（按归属ID分组）

    Args:
        cursor: 数据库游标
    """
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS grouped_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id TEXT UNIQUE NOT NULL,
        valid_orders INTEGER DEFAULT 0,
        valid_amount REAL DEFAULT 0,
        liquid_funds REAL DEFAULT 0,
        new_clients INTEGER DEFAULT 0,
        new_clients_amount REAL DEFAULT 0,
        old_clients INTEGER DEFAULT 0,
        old_clients_amount REAL DEFAULT 0,
        interest REAL DEFAULT 0,
        completed_orders INTEGER DEFAULT 0,
        completed_amount REAL DEFAULT 0,
        breach_orders INTEGER DEFAULT 0,
        breach_amount REAL DEFAULT 0,
        breach_end_orders INTEGER DEFAULT 0,
        breach_end_amount REAL DEFAULT 0,
        overdue_orders INTEGER DEFAULT 0,
        overdue_amount REAL DEFAULT 0,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """
    )
