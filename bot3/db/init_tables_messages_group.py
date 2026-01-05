"""消息表初始化 - 群组模块

包含创建群组消息配置相关表的逻辑。
"""

import sqlite3


def create_group_tables(cursor: sqlite3.Cursor) -> None:
    """创建群组消息配置表

    Args:
        cursor: 数据库游标
    """
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS group_message_config (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER NOT NULL UNIQUE,
        chat_title TEXT,
        start_work_message TEXT,
        end_work_message TEXT,
        welcome_message TEXT,
        bot_links TEXT,
        worker_links TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """
    )

    # 添加新字段（如果表已存在）
    from db.init_tables_messages import _migrate_group_message_config

    _migrate_group_message_config(cursor)
