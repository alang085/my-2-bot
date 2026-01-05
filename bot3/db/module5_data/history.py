"""
操作历史模块

包含用户操作历史的记录和查询。
"""

# 标准库
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

# 第三方库
import pytz

# 本地模块
from db.base import db_query, db_transaction

# 日志
logger = logging.getLogger(__name__)


# ========== 操作历史（撤销功能） ==========


@db_transaction
def record_operation(
    conn, cursor, user_id: int, operation_type: str, operation_data: Dict, chat_id: int
) -> int:
    """记录操作历史，返回操作ID（使用北京时间）"""
    # 使用北京时间作为 created_at
    import pytz

    tz_beijing = pytz.timezone("Asia/Shanghai")
    created_at = datetime.now(tz_beijing).strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        """
    INSERT INTO operation_history
    (user_id, chat_id, operation_type, operation_data, is_undone, created_at)
    VALUES (?, ?, ?, ?, 0, ?)
    """,
        (
            user_id,
            chat_id,
            operation_type,
            json.dumps(operation_data, ensure_ascii=False),
            created_at,
        ),
    )
    return cursor.lastrowid


@db_query
def get_last_operation(
    conn, cursor, user_id: int, chat_id: int, date: Optional[str] = None
) -> Optional[Dict]:
    """获取用户在指定聊天环境中的最后一个未撤销的操作

    规则：撤回命令不撤回撤回命令本身，排除 operation_type 为 'operation_undo' 的操作

    Args:
        user_id: 用户ID
        chat_id: 聊天环境ID
        date: 日期字符串（YYYY-MM-DD），如果提供则只返回该日期的操作，如果为None则返回当天的操作
    """

    # 如果没有提供日期，使用当天日期
    if date is None:
        from utils.date_helpers import get_daily_period_date

        date = get_daily_period_date()

    cursor.execute(
        """
    SELECT * FROM operation_history
    WHERE user_id = ? AND chat_id = ? AND is_undone = 0 
        AND DATE(created_at) = ? AND operation_type != 'operation_undo'
    ORDER BY created_at DESC, id DESC
    LIMIT 1
    """,
        (user_id, chat_id, date),
    )
    row = cursor.fetchone()
    if row:
        result = dict(row)
        result["operation_data"] = json.loads(result["operation_data"])
        return result
    return None


@db_transaction
def mark_operation_undone(conn, cursor, operation_id: int) -> bool:
    """标记操作为已撤销"""
    cursor.execute(
        """
    UPDATE operation_history
    SET is_undone = 1
    WHERE id = ?
    """,
        (operation_id,),
    )
    return cursor.rowcount > 0


@db_transaction
def mark_operation_as_undone(conn, cursor, operation_id: int) -> bool:
    """标记操作为已撤销（别名函数，用于向后兼容）"""
    return mark_operation_undone(conn, cursor, operation_id)


@db_transaction
def delete_operation(conn, cursor, operation_id: int) -> bool:
    """强制删除操作记录（不可恢复）"""
    cursor.execute("DELETE FROM operation_history WHERE id = ?", (operation_id,))
    return cursor.rowcount > 0


@db_query
def get_operation_by_id(conn, cursor, operation_id: int) -> Optional[Dict]:
    """根据ID获取操作记录"""
    cursor.execute("SELECT * FROM operation_history WHERE id = ?", (operation_id,))
    row = cursor.fetchone()
    if row:
        result = dict(row)
        result["operation_data"] = json.loads(result["operation_data"])
        return result
    return None


@db_query
def get_recent_operations(conn, cursor, user_id: int, limit: int = 10) -> List[Dict]:
    """获取用户最近的操作历史"""
    cursor.execute(
        """
    SELECT * FROM operation_history
    WHERE user_id = ?
    ORDER BY created_at DESC, id DESC
    LIMIT ?
    """,
        (user_id, limit),
    )
    rows = cursor.fetchall()
    result = []
    for row in rows:
        op = dict(row)
        op["operation_data"] = json.loads(op["operation_data"])
        result.append(op)
    return result


@db_query
def get_operations_by_date(
    conn, cursor, date: str, user_id: Optional[int] = None
) -> List[Dict]:
    """获取指定日期的操作历史

    Args:
        date: 日期字符串，格式 'YYYY-MM-DD'
        user_id: 可选的用户ID，如果提供则只返回该用户的操作

    Returns:
        操作历史列表，每个操作包含完整信息
    """
    if user_id:
        cursor.execute(
            """
        SELECT * FROM operation_history
        WHERE DATE(created_at) = ? AND user_id = ?
        ORDER BY created_at ASC, id ASC
        """,
            (date, user_id),
        )
    else:
        cursor.execute(
            """
        SELECT * FROM operation_history
        WHERE DATE(created_at) = ?
        ORDER BY created_at ASC, id ASC
        """,
            (date,),
        )

    rows = cursor.fetchall()
    result = []
    for row in rows:
        op = dict(row)
        try:
            op["operation_data"] = json.loads(op["operation_data"])
        except (json.JSONDecodeError, TypeError):
            op["operation_data"] = {}
        result.append(op)
    return result


@db_query
def _get_total_operations_count(cursor, date: str) -> int:
    """获取总操作数

    Args:
        cursor: 数据库游标
        date: 日期字符串

    Returns:
        总操作数
    """
    cursor.execute(
        """
    SELECT COUNT(*) FROM operation_history
    WHERE DATE(created_at) = ?
    """,
        (date,),
    )
    return cursor.fetchone()[0] or 0


def _get_operations_by_type(cursor, date: str) -> Dict:
    """获取按操作类型统计的数据

    Args:
        cursor: 数据库游标
        date: 日期字符串

    Returns:
        按类型统计的字典
    """
    cursor.execute(
        """
    SELECT operation_type, COUNT(*) as count
    FROM operation_history
    WHERE DATE(created_at) = ?
    GROUP BY operation_type
    ORDER BY count DESC
    """,
        (date,),
    )
    return {row[0]: row[1] for row in cursor.fetchall()}


def _get_operations_by_user(cursor, date: str) -> Dict:
    """获取按用户统计的数据

    Args:
        cursor: 数据库游标
        date: 日期字符串

    Returns:
        按用户统计的字典
    """
    cursor.execute(
        """
    SELECT user_id, COUNT(*) as count
    FROM operation_history
    WHERE DATE(created_at) = ?
    GROUP BY user_id
    ORDER BY count DESC
    """,
        (date,),
    )
    return {row[0]: row[1] for row in cursor.fetchall()}


def _get_undone_operations_count(cursor, date: str) -> int:
    """获取已撤销的操作数

    Args:
        cursor: 数据库游标
        date: 日期字符串

    Returns:
        已撤销的操作数
    """
    cursor.execute(
        """
    SELECT COUNT(*) FROM operation_history
    WHERE DATE(created_at) = ? AND is_undone = 1
    """,
        (date,),
    )
    return cursor.fetchone()[0] or 0


def get_daily_operations_summary(conn, cursor, date: str) -> Dict:
    """获取指定日期的操作汇总统计

    Args:
        date: 日期字符串，格式 'YYYY-MM-DD'

    Returns:
        包含统计信息的字典：
        - total_count: 总操作数
        - by_type: 按操作类型统计
        - by_user: 按用户统计
        - undone_count: 已撤销的操作数
    """
    total_count = _get_total_operations_count(cursor, date)
    by_type = _get_operations_by_type(cursor, date)
    by_user = _get_operations_by_user(cursor, date)
    undone_count = _get_undone_operations_count(cursor, date)

    return {
        "date": date,
        "total_count": total_count,
        "by_type": by_type,
        "by_user": by_user,
        "undone_count": undone_count,
    }
