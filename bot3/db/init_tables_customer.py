"""客户信用系统表初始化模块

包含客户档案、信用、信用历史、客户价值等表的创建逻辑。
"""

import sqlite3


def _create_customer_profiles_table(cursor: sqlite3.Cursor) -> None:
    """创建客户档案表"""
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS customer_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            id_card TEXT,
            customer_type TEXT DEFAULT 'white',
            first_contact_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def _create_customer_credit_table(cursor: sqlite3.Cursor) -> None:
    """创建客户信用表"""
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS customer_credit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT UNIQUE NOT NULL,
            credit_score INTEGER DEFAULT 500,
            credit_level TEXT DEFAULT 'C',
            consecutive_payments INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def _create_credit_history_table(cursor: sqlite3.Cursor) -> None:
    """创建信用变更历史表"""
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS credit_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT NOT NULL,
            change_type TEXT NOT NULL,
            score_change INTEGER NOT NULL,
            score_before INTEGER NOT NULL,
            score_after INTEGER NOT NULL,
            order_id TEXT,
            reason TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def _create_customer_value_table(cursor: sqlite3.Cursor) -> None:
    """创建客户价值表"""
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS customer_value (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT UNIQUE NOT NULL,
            total_borrowed REAL DEFAULT 0,
            total_interest_paid REAL DEFAULT 0,
            total_profit REAL DEFAULT 0,
            order_count INTEGER DEFAULT 0,
            completed_order_count INTEGER DEFAULT 0,
            average_order_amount REAL DEFAULT 0,
            last_calculated TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def _create_customer_indexes(cursor: sqlite3.Cursor) -> None:
    """创建客户相关表的索引"""
    try:
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_customer_profiles_phone ON customer_profiles(phone)"
        )
        cursor.execute(
            (
                "CREATE INDEX IF NOT EXISTS idx_customer_credit_customer_id "
                "ON customer_credit(customer_id)"
            )
        )
        cursor.execute(
            (
                "CREATE INDEX IF NOT EXISTS idx_credit_history_customer_id "
                "ON credit_history(customer_id)"
            )
        )
        cursor.execute(
            (
                "CREATE INDEX IF NOT EXISTS idx_customer_value_customer_id "
                "ON customer_value(customer_id)"
            )
        )
    except sqlite3.OperationalError:
        pass


def create_customer_tables(cursor: sqlite3.Cursor) -> None:
    """创建客户信用系统相关表"""
    _create_customer_profiles_table(cursor)
    _create_customer_credit_table(cursor)
    _create_credit_history_table(cursor)
    _create_customer_value_table(cursor)
    _create_customer_indexes(cursor)
