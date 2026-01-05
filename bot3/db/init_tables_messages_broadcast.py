"""消息表初始化 - 播报模块

包含创建定时播报相关表的逻辑。
"""

import sqlite3


def create_broadcast_tables(cursor: sqlite3.Cursor) -> None:
    """创建定时播报表

    Args:
        cursor: 数据库游标
    """
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS scheduled_broadcasts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slot INTEGER NOT NULL CHECK(slot >= 1 AND slot <= 3),
        time TEXT NOT NULL,
        chat_id INTEGER,
        chat_title TEXT,
        message TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(slot)
    )
    """
    )
