"""支付表初始化 - 支付账号表模块

包含创建支付账号表的逻辑。
"""

import sqlite3


def _check_table_exists(cursor: sqlite3.Cursor) -> bool:
    """检查表是否存在

    Args:
        cursor: 数据库游标

    Returns:
        是否存在
    """
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='payment_accounts'"
    )
    return cursor.fetchone() is not None


def _check_has_unique_constraint(cursor: sqlite3.Cursor) -> bool:
    """检查表是否有UNIQUE约束

    Args:
        cursor: 数据库游标

    Returns:
        是否有UNIQUE约束
    """
    cursor.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='payment_accounts'"
    )
    table_sql = cursor.fetchone()
    return table_sql is not None and "UNIQUE" in table_sql[0]


def _migrate_payment_accounts_table(cursor: sqlite3.Cursor) -> None:
    """迁移支付账号表（移除UNIQUE约束）

    Args:
        cursor: 数据库游标
    """
    cursor.execute("SELECT * FROM payment_accounts")
    old_data = cursor.fetchall()
    cursor.execute("DROP TABLE payment_accounts")

    cursor.execute(
        """
    CREATE TABLE payment_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_type TEXT NOT NULL,
        account_number TEXT NOT NULL,
        account_name TEXT,
        balance REAL DEFAULT 0,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """
    )

    if old_data:
        cursor.executemany(
            """
            INSERT INTO payment_accounts (
                id, account_type, account_number,
                account_name, balance, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            old_data,
        )


def _create_payment_accounts_table_if_not_exists(cursor: sqlite3.Cursor) -> None:
    """创建支付账号表（如果不存在）

    Args:
        cursor: 数据库游标
    """
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS payment_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_type TEXT NOT NULL,
        account_number TEXT NOT NULL,
        account_name TEXT,
        balance REAL DEFAULT 0,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """
    )


def create_payment_accounts_table(cursor: sqlite3.Cursor) -> None:
    """创建支付账号表（如果需要迁移则迁移）

    Args:
        cursor: 数据库游标
    """
    if _check_table_exists(cursor) and _check_has_unique_constraint(cursor):
        _migrate_payment_accounts_table(cursor)
    else:
        _create_payment_accounts_table_if_not_exists(cursor)


def init_payment_accounts(cursor: sqlite3.Cursor) -> None:
    """初始化支付账号（如果不存在）

    Args:
        cursor: 数据库游标
    """
    cursor.execute("SELECT COUNT(*) FROM payment_accounts")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            """
        INSERT INTO payment_accounts (account_type, account_number, account_name, balance)
        VALUES ('gcash', '', '', 0)
        """
        )
        cursor.execute(
            """
        INSERT INTO payment_accounts (account_type, account_number, account_name, balance)
        VALUES ('paymaya', '', '', 0)
        """
        )
