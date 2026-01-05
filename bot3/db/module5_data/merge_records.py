"""
增量报表合并记录操作模块

包含增量报表合并记录的查询和保存功能。
"""

# 标准库
import logging
import sqlite3
from typing import Dict, List, Optional

# 本地模块
from db.base import db_query, db_transaction

# 日志
logger = logging.getLogger(__name__)


@db_query
def check_merge_record_exists(conn, cursor, merge_date: str) -> bool:
    """检查指定日期的合并记录是否存在"""
    cursor.execute(
        "SELECT COUNT(*) FROM incremental_merge_records WHERE merge_date = ?",
        (merge_date,),
    )
    count = cursor.fetchone()[0]
    return count > 0


@db_query
def get_merge_record(conn, cursor, merge_date: str) -> Optional[Dict]:
    """获取指定日期的合并记录"""
    cursor.execute(
        """
    SELECT * FROM incremental_merge_records
    WHERE merge_date = ?
    """,
        (merge_date,),
    )
    row = cursor.fetchone()
    return dict(row) if row else None


@db_query
def get_all_merge_records(conn, cursor) -> List[Dict]:
    """获取所有合并记录"""
    cursor.execute(
        """
    SELECT * FROM incremental_merge_records
    ORDER BY merged_at DESC
    """
    )
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


@db_transaction
def _insert_merge_record(
    cursor: sqlite3.Cursor,
    merge_date: str,
    baseline_date: str,
    orders_count: int,
    total_amount: float,
    total_interest: float,
    total_expenses: float,
    merged_by: Optional[int],
) -> bool:
    """插入新的合并记录

    Args:
        cursor: 数据库游标
        merge_date: 合并日期
        baseline_date: 基准日期
        orders_count: 订单数
        total_amount: 总金额
        total_interest: 总利息
        total_expenses: 总开销
        merged_by: 合并者ID

    Returns:
        是否成功
    """
    cursor.execute(
        """
    INSERT INTO incremental_merge_records
    (merge_date, baseline_date, orders_count, total_amount,
     total_interest, total_expenses, merged_by)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (
            merge_date,
            baseline_date,
            orders_count,
            total_amount,
            total_interest,
            total_expenses,
            merged_by,
        ),
    )
    return True


def _update_existing_merge_record(
    cursor: sqlite3.Cursor,
    merge_date: str,
    baseline_date: str,
    orders_count: int,
    total_amount: float,
    total_interest: float,
    total_expenses: float,
    merged_by: Optional[int],
) -> bool:
    """更新已存在的合并记录

    Args:
        cursor: 数据库游标
        merge_date: 合并日期
        baseline_date: 基准日期
        orders_count: 订单数
        total_amount: 总金额
        total_interest: 总利息
        total_expenses: 总开销
        merged_by: 合并者ID

    Returns:
        是否成功
    """
    params.cursor.execute(
        """
    UPDATE incremental_merge_records
    SET baseline_date = ?, orders_count = ?, total_amount = ?,
        total_interest = ?, total_expenses = ?, merged_by = ?, merged_at = CURRENT_TIMESTAMP
    WHERE merge_date = ?
    """,
        (
            params.baseline_date,
            params.orders_count,
            params.total_amount,
            params.total_interest,
            params.total_expenses,
            params.merged_by,
            params.merge_date,
        ),
    )
    return True


def save_merge_record(params: "MergeRecordParams") -> bool:
    """保存合并记录

    Args:
        params: 合并记录参数

    Returns:
        是否成功
    """
    from db.module5_data.merge_record_data import MergeRecordParams

    try:
        insert_params = MergeRecordParams(
            conn=params.conn,
            cursor=params.cursor,
            merge_date=params.merge_date,
            baseline_date=params.baseline_date,
            orders_count=params.orders_count,
            total_amount=params.total_amount,
            total_interest=params.total_interest,
            total_expenses=params.total_expenses,
            merged_by=params.merged_by,
        )
        return _insert_merge_record(insert_params)
    except sqlite3.IntegrityError:
        return _update_existing_merge_record(insert_params)
    except Exception as e:
        logger.error(f"保存合并记录失败: {e}", exc_info=True)
        return False
