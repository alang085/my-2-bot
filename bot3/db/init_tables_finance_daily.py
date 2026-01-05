"""财务表初始化 - 日结数据表模块

包含创建日结数据表和索引的逻辑。
"""

import sqlite3


def create_daily_data_table(cursor: sqlite3.Cursor) -> None:
    """创建日结数据表（按日期和归属ID存储）

    Args:
        cursor: 数据库游标
    """
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS daily_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        group_id TEXT,
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
        liquid_flow REAL DEFAULT 0,
        company_expenses REAL DEFAULT 0,
        other_expenses REAL DEFAULT 0,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(date, group_id)
    )
    """
    )


def create_daily_data_indexes(cursor: sqlite3.Cursor) -> None:
    """创建日结数据表索引

    Args:
        cursor: 数据库游标
    """
    try:
        cursor.execute(
            """
        CREATE INDEX IF NOT EXISTS idx_daily_data_date ON daily_data(date)
        """
        )
        cursor.execute(
            """
        CREATE INDEX IF NOT EXISTS idx_daily_data_group ON daily_data(group_id)
        """
        )
    except sqlite3.OperationalError:
        pass
