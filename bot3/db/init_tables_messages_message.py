"""消息表初始化 - 消息模块

包含创建各种消息表的逻辑。
"""

import sqlite3


def _create_anti_fraud_messages_table(cursor: sqlite3.Cursor) -> None:
    """创建防诈骗语录表

    Args:
        cursor: 数据库游标
    """
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS anti_fraud_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """
    )


def _create_company_promotion_messages_table(cursor: sqlite3.Cursor) -> None:
    """创建公司宣传轮播语录表

    Args:
        cursor: 数据库游标
    """
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS company_promotion_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """
    )


def _create_start_work_messages_table(cursor: sqlite3.Cursor) -> None:
    """创建开工消息表（按星期轮播）

    Args:
        cursor: 数据库游标
    """
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS start_work_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        weekday INTEGER NOT NULL CHECK(weekday >= 0 AND weekday <= 6),
        message TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(weekday)
    )
    """
    )


def _create_end_work_messages_table(cursor: sqlite3.Cursor) -> None:
    """创建收工消息表（按星期轮播）

    Args:
        cursor: 数据库游标
    """
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS end_work_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        weekday INTEGER NOT NULL CHECK(weekday >= 0 AND weekday <= 6),
        message TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(weekday)
    )
    """
    )


def create_message_type_tables(cursor: sqlite3.Cursor) -> None:
    """创建各种消息类型表

    Args:
        cursor: 数据库游标
    """
    _create_anti_fraud_messages_table(cursor)
    _create_company_promotion_messages_table(cursor)
    _create_start_work_messages_table(cursor)
    _create_end_work_messages_table(cursor)
