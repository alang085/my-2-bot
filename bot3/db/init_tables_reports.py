"""报表相关表初始化模块

包含日切数据汇总、基准报表、增量报表合并记录等表的创建逻辑。
"""

import logging
import sqlite3

logger = logging.getLogger(__name__)


def _create_daily_summary_table(cursor: sqlite3.Cursor) -> None:
    """创建日切数据汇总表

    Args:
        cursor: 数据库游标
    """
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS daily_summary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL UNIQUE,
        new_clients_count INTEGER DEFAULT 0,
        new_clients_amount REAL DEFAULT 0,
        old_clients_count INTEGER DEFAULT 0,
        old_clients_amount REAL DEFAULT 0,
        completed_orders_count INTEGER DEFAULT 0,
        completed_amount REAL DEFAULT 0,
        breach_orders_count INTEGER DEFAULT 0,
        breach_amount REAL DEFAULT 0,
        breach_end_orders_count INTEGER DEFAULT 0,
        breach_end_amount REAL DEFAULT 0,
        daily_interest REAL DEFAULT 0,
        company_expenses REAL DEFAULT 0,
        other_expenses REAL DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """
    )


def _create_baseline_report_table(cursor: sqlite3.Cursor) -> None:
    """创建基准报表表

    Args:
        cursor: 数据库游标
    """
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS baseline_report (
        id INTEGER PRIMARY KEY DEFAULT 1 CHECK(id = 1),
        baseline_date TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """
    )


def _create_incremental_merge_records_table(cursor: sqlite3.Cursor) -> None:
    """创建增量报表合并记录表

    Args:
        cursor: 数据库游标
    """
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS incremental_merge_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        merge_date TEXT NOT NULL UNIQUE,
        baseline_date TEXT NOT NULL,
        orders_count INTEGER DEFAULT 0,
        total_amount REAL DEFAULT 0,
        total_interest REAL DEFAULT 0,
        total_expenses REAL DEFAULT 0,
        merged_by INTEGER,
        merged_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """
    )


def create_report_tables(cursor: sqlite3.Cursor, conn: sqlite3.Connection) -> None:
    """创建报表相关表"""
    _create_daily_summary_table(cursor)
    _migrate_daily_summary(cursor, conn)
    _create_baseline_report_table(cursor)
    _create_incremental_merge_records_table(cursor)


def _migrate_daily_summary(cursor: sqlite3.Cursor, conn: sqlite3.Connection) -> None:
    """迁移 daily_summary 表结构（添加缺失的列）"""
    from db.init_tables_reports_migrate_columns import (add_column_if_missing,
                                                        migrate_column_rename)

    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='daily_summary'"
    )
    daily_summary_exists = cursor.fetchone()
    if daily_summary_exists:
        cursor.execute("PRAGMA table_info(daily_summary)")
        columns = [row[1] for row in cursor.fetchall()]

        # 添加新客户字段
        add_column_if_missing(
            cursor, conn, columns, "new_clients_count", "INTEGER DEFAULT 0"
        )
        add_column_if_missing(
            cursor, conn, columns, "new_clients_amount", "REAL DEFAULT 0"
        )

        # 添加老客户字段
        add_column_if_missing(
            cursor, conn, columns, "old_clients_count", "INTEGER DEFAULT 0"
        )
        add_column_if_missing(
            cursor, conn, columns, "old_clients_amount", "REAL DEFAULT 0"
        )

        # 添加违约订单字段
        add_column_if_missing(
            cursor, conn, columns, "breach_orders_count", "INTEGER DEFAULT 0"
        )
        add_column_if_missing(cursor, conn, columns, "breach_amount", "REAL DEFAULT 0")

        # 重命名 completed_orders_amount 为 completed_amount
        migrate_column_rename(
            cursor, conn, columns, "completed_orders_amount", "completed_amount"
        )

        # 重命名 breach_end_orders_amount 为 breach_end_amount
        migrate_column_rename(
            cursor, conn, columns, "breach_end_orders_amount", "breach_end_amount"
        )
