"""支付相关表初始化模块

包含支付账号和余额历史表的创建逻辑。
"""

import sqlite3


def create_payment_tables(cursor: sqlite3.Cursor, conn: sqlite3.Connection) -> None:
    """创建支付账号表和余额历史表"""
    from db.init_tables_payment_accounts import (create_payment_accounts_table,
                                                 init_payment_accounts)
    from db.init_tables_payment_history import (
        create_payment_balance_history_indexes,
        create_payment_balance_history_table)

    # 创建支付账号表
    create_payment_accounts_table(cursor)

    # 初始化支付账号（如果不存在）
    init_payment_accounts(cursor)

    # 创建支付账号余额历史表
    create_payment_balance_history_table(cursor)

    # 创建索引以提高查询性能
    create_payment_balance_history_indexes(cursor)
