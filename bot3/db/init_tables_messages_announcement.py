"""消息表初始化 - 公告模块

包含创建公告相关表的逻辑。
"""

import sqlite3


def create_announcement_tables(cursor: sqlite3.Cursor) -> None:
    """创建公司公告表和公告发送计划表

    Args:
        cursor: 数据库游标
    """
    # 创建公司公告表
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS company_announcements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """
    )

    # 创建公告发送计划表（全局配置，只有一条记录）
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS announcement_schedule (
        id INTEGER PRIMARY KEY DEFAULT 1 CHECK(id = 1),
        interval_hours INTEGER DEFAULT 3,
        is_active INTEGER DEFAULT 1,
        last_sent_at TEXT,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """
    )

    # 初始化公告发送计划表（如果不存在记录）
    cursor.execute("SELECT COUNT(*) FROM announcement_schedule")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            """
        INSERT INTO announcement_schedule (id, interval_hours, is_active)
        VALUES (1, 3, 1)
        """
        )
