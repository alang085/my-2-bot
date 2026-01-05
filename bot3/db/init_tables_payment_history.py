"""支付表初始化 - 余额历史表模块

包含创建余额历史表和索引的逻辑。
"""

import sqlite3


def create_payment_balance_history_table(cursor: sqlite3.Cursor) -> None:
    """创建支付账号余额历史表

    Args:
        cursor: 数据库游标
    """
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS payment_balance_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id INTEGER,
        account_type TEXT NOT NULL,
        balance REAL NOT NULL,
        date TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (account_id) REFERENCES payment_accounts(id)
    )
    """
    )


def create_payment_balance_history_indexes(cursor: sqlite3.Cursor) -> None:
    """创建余额历史表索引

    Args:
        cursor: 数据库游标
    """
    cursor.execute(
        """
    CREATE INDEX IF NOT EXISTS idx_payment_balance_history_date
    ON payment_balance_history(date)
    """
    )
    cursor.execute(
        """
    CREATE INDEX IF NOT EXISTS idx_payment_balance_history_account_id
    ON payment_balance_history(account_id)
    """
    )
