"""财务记录表初始化模块

包含开销记录、收入明细、操作历史等表的创建逻辑。
"""

import logging
import sqlite3

logger = logging.getLogger(__name__)


def _create_expense_records_table(cursor: sqlite3.Cursor) -> None:
    """创建开销记录表

    Args:
        cursor: 数据库游标
    """
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS expense_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        type TEXT NOT NULL,
        amount REAL NOT NULL,
        note TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """
    )


def _create_income_records_table(cursor: sqlite3.Cursor) -> None:
    """创建收入明细表

    Args:
        cursor: 数据库游标
    """
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS income_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        type TEXT NOT NULL,
        amount REAL NOT NULL,
        group_id TEXT,
        order_id TEXT,
        order_date TEXT,
        customer TEXT,
        weekday_group TEXT,
        note TEXT,
        created_by INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        is_undone INTEGER DEFAULT 0
    )
    """
    )


def _create_operation_history_table(cursor: sqlite3.Cursor) -> None:
    """创建操作历史表

    Args:
        cursor: 数据库游标
    """
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS operation_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        operation_type TEXT NOT NULL,
        operation_data TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        is_undone INTEGER DEFAULT 0
    )
    """
    )


def create_record_tables(cursor: sqlite3.Cursor) -> None:
    """创建财务记录相关表"""
    _create_expense_records_table(cursor)
    _create_income_records_table(cursor)
    _migrate_income_records(cursor)

    _create_operation_history_table(cursor)
    _migrate_operation_history(cursor)

    _create_operation_history_indexes(cursor)
    _create_income_records_indexes(cursor)


def _migrate_income_records(cursor: sqlite3.Cursor) -> None:
    """迁移 income_records 表结构（添加 is_undone 字段）"""
    cursor.execute("PRAGMA table_info(income_records)")
    columns = [col[1] for col in cursor.fetchall()]
    if "is_undone" not in columns:
        try:
            logger.info("添加 is_undone 字段到 income_records 表...")
            cursor.execute(
                """
            ALTER TABLE income_records
            ADD COLUMN is_undone INTEGER DEFAULT 0
            """
            )
        except sqlite3.OperationalError as e:
            logger.warning(f"添加 is_undone 字段失败（可能已存在）: {e}")


def _migrate_operation_history(cursor: sqlite3.Cursor) -> None:
    """迁移 operation_history 表结构（添加 chat_id 字段）"""
    cursor.execute("PRAGMA table_info(operation_history)")
    columns = [col[1] for col in cursor.fetchall()]
    if "chat_id" not in columns:
        try:
            logger.info("添加 chat_id 字段到 operation_history 表...")
            cursor.execute(
                """
            ALTER TABLE operation_history
            ADD COLUMN chat_id INTEGER NOT NULL DEFAULT 0
            """
            )
        except sqlite3.OperationalError as e:
            logger.warning(f"添加 chat_id 字段失败（可能已存在）: {e}")


def _create_operation_history_indexes(cursor: sqlite3.Cursor) -> None:
    """为操作历史表创建索引"""
    cursor.execute(
        """
    CREATE INDEX IF NOT EXISTS idx_operation_user_time
    ON operation_history(user_id, created_at DESC)
    """
    )
    cursor.execute(
        """
    CREATE INDEX IF NOT EXISTS idx_operation_undone ON operation_history(is_undone, created_at DESC)
    """
    )
    cursor.execute(
        """
    CREATE INDEX IF NOT EXISTS idx_operation_chat_user
    ON operation_history(chat_id, user_id, created_at DESC)
    """
    )
    # 添加按日期查询的索引
    cursor.execute(
        """
    CREATE INDEX IF NOT EXISTS idx_operation_date ON operation_history(DATE(created_at))
    """
    )


def _create_income_records_indexes(cursor: sqlite3.Cursor) -> None:
    """为收入明细表创建索引"""
    try:
        cursor.execute(
            """
        CREATE INDEX IF NOT EXISTS idx_income_date ON income_records(date)
        """
        )
        cursor.execute(
            """
        CREATE INDEX IF NOT EXISTS idx_income_type ON income_records(type)
        """
        )
        cursor.execute(
            """
        CREATE INDEX IF NOT EXISTS idx_income_customer ON income_records(customer)
        """
        )
        cursor.execute(
            """
        CREATE INDEX IF NOT EXISTS idx_income_group ON income_records(group_id)
        """
        )
        cursor.execute(
            """
        CREATE INDEX IF NOT EXISTS idx_income_order ON income_records(order_id)
        """
        )
        cursor.execute(
            """
        CREATE INDEX IF NOT EXISTS idx_income_date_type ON income_records(date, type)
        """
        )
        cursor.execute(
            """
        CREATE INDEX IF NOT EXISTS idx_income_group_type ON income_records(group_id, type)
        """
        )
    except sqlite3.OperationalError:
        # 索引可能已存在，忽略错误
        pass
