"""订单相关表初始化模块

包含订单表和分类表的创建逻辑。
"""

import logging
import sqlite3

logger = logging.getLogger(__name__)


def _create_orders_main_table(cursor: sqlite3.Cursor) -> None:
    """创建订单主表

    Args:
        cursor: 数据库游标
    """
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT UNIQUE NOT NULL,
        group_id TEXT NOT NULL,
        chat_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        weekday_group TEXT NOT NULL,
        customer TEXT NOT NULL,
        amount REAL NOT NULL,
        state TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """
    )


def _create_orders_indexes(cursor: sqlite3.Cursor) -> None:
    """创建订单表索引

    Args:
        cursor: 数据库游标
    """
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_orders_chat_id ON orders(chat_id)",
        "CREATE INDEX IF NOT EXISTS idx_orders_state ON orders(state)",
        "CREATE INDEX IF NOT EXISTS idx_orders_group_id ON orders(group_id)",
        "CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(date)",
        "CREATE INDEX IF NOT EXISTS idx_orders_weekday_group ON orders(weekday_group)",
        "CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_orders_updated_at ON orders(updated_at)",
        "CREATE INDEX IF NOT EXISTS idx_orders_state_chat ON orders(state, chat_id)",
    ]

    try:
        for index_sql in indexes:
            cursor.execute(index_sql)
    except sqlite3.OperationalError:
        pass


def create_orders_tables(cursor: sqlite3.Cursor) -> None:
    """创建订单表和索引"""
    _create_orders_main_table(cursor)
    _create_orders_indexes(cursor)


def create_classified_tables(cursor: sqlite3.Cursor) -> None:
    """创建订单分类表（按状态、客户类型、星期分组、归属ID分类）"""
    from db.init_tables_classified_customer import create_customer_tables
    from db.init_tables_classified_group import create_group_tables
    from db.init_tables_classified_state import create_state_tables
    from db.init_tables_classified_weekday import create_weekday_tables

    # 分类表的表结构（与orders表一致）
    classified_table_schema = """
    CREATE TABLE IF NOT EXISTS {} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT UNIQUE NOT NULL,
        group_id TEXT NOT NULL,
        chat_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        weekday_group TEXT NOT NULL,
        customer TEXT NOT NULL,
        amount REAL NOT NULL,
        state TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """

    # 1. 按状态分类表
    create_state_tables(cursor, classified_table_schema)

    # 2. 按客户类型分类表
    create_customer_tables(cursor, classified_table_schema)

    # 3. 按星期分组分类表
    create_weekday_tables(cursor, classified_table_schema)

    # 4. 按归属ID分类表
    create_group_tables(cursor, classified_table_schema)
