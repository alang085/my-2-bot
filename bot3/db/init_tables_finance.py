"""财务数据表初始化模块

包含财务统计相关表的创建逻辑。
"""

import logging
import sqlite3

logger = logging.getLogger(__name__)


def create_finance_tables(cursor: sqlite3.Cursor, conn: sqlite3.Connection) -> None:
    """创建财务数据表（全局统计、分组统计、日结数据）"""
    from db.init_tables_finance_daily import (create_daily_data_indexes,
                                              create_daily_data_table)
    from db.init_tables_finance_financial import create_financial_data_table
    from db.init_tables_finance_grouped import create_grouped_data_table

    # 创建财务数据表（全局统计）
    create_financial_data_table(cursor)

    # 创建分组数据表（按归属ID分组）
    create_grouped_data_table(cursor)

    # 创建日结数据表（按日期和归属ID存储）
    create_daily_data_table(cursor)

    # 为日结数据表创建索引
    create_daily_data_indexes(cursor)

    # 检查表是否存在，如果存在需要检查列是否存在并添加缺失的列
    _migrate_daily_data_table(cursor, conn)
    _migrate_financial_data_table(cursor, conn)
    _migrate_grouped_data_table(cursor, conn)
    _initialize_financial_data(cursor)


def _migrate_daily_data_table(cursor: sqlite3.Cursor, conn: sqlite3.Connection) -> None:
    """迁移 daily_data 表结构（添加缺失的列）

    Args:
        cursor: 数据库游标
        conn: 数据库连接
    """
    from db.init_tables_finance_helpers import migrate_daily_data_columns

    migrate_daily_data_columns(cursor, conn)


def _migrate_financial_data_table(
    cursor: sqlite3.Cursor, conn: sqlite3.Connection
) -> None:
    """迁移 financial_data 表结构（添加 overdue 字段）"""
    try:
        cursor.execute("PRAGMA table_info(financial_data)")
        columns = [row[1] for row in cursor.fetchall()]

        if "overdue_orders" not in columns:
            try:
                cursor.execute(
                    "ALTER TABLE financial_data ADD COLUMN overdue_orders INTEGER DEFAULT 0"
                )
                conn.commit()
                logger.info("已添加列: financial_data.overdue_orders")
            except sqlite3.OperationalError:
                pass

        if "overdue_amount" not in columns:
            try:
                cursor.execute(
                    "ALTER TABLE financial_data ADD COLUMN overdue_amount REAL DEFAULT 0"
                )
                conn.commit()
                logger.info("已添加列: financial_data.overdue_amount")
            except sqlite3.OperationalError:
                pass
    except Exception as e:
        logger.warning(f"检查 financial_data 表结构时出错: {e}")


def _migrate_grouped_data_table(
    cursor: sqlite3.Cursor, conn: sqlite3.Connection
) -> None:
    """迁移 grouped_data 表结构（添加 overdue 字段）"""
    try:
        cursor.execute("PRAGMA table_info(grouped_data)")
        columns = [row[1] for row in cursor.fetchall()]

        if "overdue_orders" not in columns:
            try:
                cursor.execute(
                    "ALTER TABLE grouped_data ADD COLUMN overdue_orders INTEGER DEFAULT 0"
                )
                conn.commit()
                logger.info("已添加列: grouped_data.overdue_orders")
            except sqlite3.OperationalError:
                pass

        if "overdue_amount" not in columns:
            try:
                cursor.execute(
                    "ALTER TABLE grouped_data ADD COLUMN overdue_amount REAL DEFAULT 0"
                )
                conn.commit()
                logger.info("已添加列: grouped_data.overdue_amount")
            except sqlite3.OperationalError:
                pass
    except Exception as e:
        logger.warning(f"检查 grouped_data 表结构时出错: {e}")


def _initialize_financial_data(cursor: sqlite3.Cursor) -> None:
    """初始化财务数据（如果不存在）"""
    cursor.execute("SELECT COUNT(*) FROM financial_data")
    if cursor.fetchone()[0] == 0:
        cursor.execute("PRAGMA table_info(financial_data)")
        columns = [row[1] for row in cursor.fetchall()]
        has_overdue = "overdue_orders" in columns and "overdue_amount" in columns

        if has_overdue:
            cursor.execute(
                """
            INSERT INTO financial_data (
                valid_orders, valid_amount, liquid_funds,
                new_clients, new_clients_amount,
                old_clients, old_clients_amount,
                interest, completed_orders, completed_amount,
                breach_orders, breach_amount,
                breach_end_orders, breach_end_amount,
                overdue_orders, overdue_amount
            ) VALUES (0, 0, 100000, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            """
            )
        else:
            cursor.execute(
                """
            INSERT INTO financial_data (
                valid_orders, valid_amount, liquid_funds,
                new_clients, new_clients_amount,
                old_clients, old_clients_amount,
                interest, completed_orders, completed_amount,
                breach_orders, breach_amount,
                breach_end_orders, breach_end_amount
            ) VALUES (0, 0, 100000, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            """
            )
