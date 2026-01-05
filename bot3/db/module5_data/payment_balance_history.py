"""
支付账号余额历史操作模块

包含支付账号余额历史的记录和查询功能。
"""

# 标准库
import logging
from typing import Dict, List

# 本地模块
from db.base import db_query, db_transaction

# 日志
logger = logging.getLogger(__name__)


@db_transaction
def record_payment_balance_history(
    conn, cursor, account_id: int, account_type: str, balance: float, date: str
) -> int:
    """记录支付账号余额历史

    Args:
        account_id: 账号ID
        account_type: 账号类型（gcash/paymaya）
        balance: 余额
        date: 日期字符串，格式 'YYYY-MM-DD'

    Returns:
        记录ID
    """
    # 检查当天是否已有记录，如果有则更新，否则插入
    cursor.execute(
        """
    SELECT id FROM payment_balance_history
    WHERE account_id = ? AND date = ?
    """,
        (account_id, date),
    )
    existing = cursor.fetchone()

    if existing:
        # 更新现有记录
        cursor.execute(
            """
        UPDATE payment_balance_history
        SET balance = ?, created_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
            (balance, existing[0]),
        )
        return existing[0]
    else:
        # 插入新记录
        cursor.execute(
            """
        INSERT INTO payment_balance_history (account_id, account_type, balance, date)
        VALUES (?, ?, ?, ?)
        """,
            (account_id, account_type, balance, date),
        )
        return cursor.lastrowid


@db_query
def get_balance_history_by_date(conn, cursor, date: str) -> List[Dict]:
    """获取指定日期的所有账号余额历史

    Args:
        date: 日期字符串，格式 'YYYY-MM-DD'

    Returns:
        余额历史记录列表
    """
    cursor.execute(
        """
    SELECT * FROM payment_balance_history
    WHERE date = ?
    ORDER BY account_type, account_id
    """,
        (date,),
    )
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


@db_query
def _initialize_balance_result(date: str) -> Dict:
    """初始化余额结果字典

    Args:
        date: 日期字符串

    Returns:
        初始化的结果字典
    """
    return {
        "date": date,
        "gcash_total": 0.0,
        "paymaya_total": 0.0,
        "total": 0.0,
        "accounts": [],
    }


def _process_balance_summary_rows(rows: List, result: Dict) -> None:
    """处理余额汇总行

    Args:
        rows: 查询结果行
        result: 结果字典（会被修改）
    """
    for row in rows:
        account_type = row[0]
        total_balance = row[1] or 0.0
        account_count = row[2] or 0

        if account_type == "gcash":
            result["gcash_total"] = total_balance
        elif account_type == "paymaya":
            result["paymaya_total"] = total_balance

        result["accounts"].append(
            {
                "account_type": account_type,
                "total_balance": total_balance,
                "account_count": account_count,
            }
        )

    result["total"] = result["gcash_total"] + result["paymaya_total"]


def _get_account_details(cursor, date: str) -> List[Dict]:
    """获取每个账户的详细余额历史

    Args:
        cursor: 数据库游标
        date: 日期字符串

    Returns:
        账户详情列表
    """
    cursor.execute(
        """
    SELECT pb.*, pa.account_number, pa.account_name
    FROM payment_balance_history pb
    LEFT JOIN payment_accounts pa ON pb.account_id = pa.id
    WHERE pb.date = ?
    ORDER BY pb.account_type, pb.account_id
    """,
        (date,),
    )
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


@db_query
def get_balance_summary_by_date(conn, cursor, date: str) -> Dict:
    """获取指定日期的余额汇总统计"""
    cursor.execute(
        """
    SELECT account_type, SUM(balance) as total_balance, COUNT(*) as account_count
    FROM payment_balance_history
    WHERE date = ?
    GROUP BY account_type
    """,
        (date,),
    )
    rows = cursor.fetchall()
    result = _initialize_balance_result(date)
    _process_balance_summary_rows(rows, result)
    result["account_details"] = _get_account_details(cursor, date)
    return result
