"""开工收工消息操作模块

包含开工和收工消息的配置功能（按星期轮播）。
"""

from typing import Dict, List, Optional

# 本地模块
from db.base import db_query, db_transaction
from utils.query_builder import QueryBuilder


@db_query
def get_start_work_message_by_weekday(conn, cursor, weekday: int) -> Optional[str]:
    """根据星期几获取开工消息（weekday: 0=周一, 6=周日）"""
    query, params = (
        QueryBuilder("start_work_messages")
        .select("message")
        .where("weekday = ?", weekday)
        .where("is_active = ?", 1)
        .build()
    )
    cursor.execute(query, params)
    row = cursor.fetchone()
    return row[0] if row else None


@db_query
def get_all_start_work_messages(conn, cursor) -> List[Dict]:
    """获取所有开工消息（包括未激活的）"""
    query, params = (
        QueryBuilder("start_work_messages").order_by_field("weekday").build()
    )
    cursor.execute(query, params)
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


@db_query
def get_active_start_work_messages(conn, cursor) -> List[str]:
    """获取所有激活的开工消息（用于随机选择）"""
    query, params = (
        QueryBuilder("start_work_messages")
        .select("message")
        .where("is_active = ?", 1)
        .build()
    )
    cursor.execute(query, params)
    rows = cursor.fetchall()
    return [row[0] for row in rows if row[0] and row[0].strip()]


@db_transaction
def save_start_work_message(conn, cursor, weekday: int, message: str) -> int:
    """保存或更新开工消息，返回消息ID（weekday: 0=周一, 6=周日）"""
    # 检查是否已存在
    query, params = (
        QueryBuilder("start_work_messages")
        .select("id")
        .where("weekday = ?", weekday)
        .build()
    )
    cursor.execute(query, params)
    row = cursor.fetchone()

    if row:
        # 更新现有记录
        cursor.execute(
            """
        UPDATE start_work_messages
        SET message = ?, is_active = 1, updated_at = CURRENT_TIMESTAMP
        WHERE weekday = ?
        """,
            (message, weekday),
        )
        return row[0]
    else:
        # 创建新记录
        cursor.execute(
            """
        INSERT INTO start_work_messages (weekday, message, is_active)
        VALUES (?, ?, 1)
        """,
            (weekday, message),
        )
        return cursor.lastrowid


@db_transaction
def delete_start_work_message(conn, cursor, weekday: int) -> bool:
    """删除指定星期几的开工消息"""
    cursor.execute("DELETE FROM start_work_messages WHERE weekday = ?", (weekday,))
    return cursor.rowcount > 0


@db_transaction
def toggle_start_work_message(conn, cursor, weekday: int) -> bool:
    """切换开工消息的激活状态"""
    cursor.execute(
        """
    UPDATE start_work_messages
    SET is_active = NOT is_active, updated_at = CURRENT_TIMESTAMP
    WHERE weekday = ?
    """,
        (weekday,),
    )
    return cursor.rowcount > 0


@db_query
def get_end_work_message_by_weekday(conn, cursor, weekday: int) -> Optional[str]:
    """根据星期几获取收工消息（weekday: 0=周一, 6=周日）"""
    query, params = (
        QueryBuilder("end_work_messages")
        .select("message")
        .where("weekday = ?", weekday)
        .where("is_active = ?", 1)
        .build()
    )
    cursor.execute(query, params)
    row = cursor.fetchone()
    return row[0] if row else None


@db_query
def get_all_end_work_messages(conn, cursor) -> List[Dict]:
    """获取所有收工消息（包括未激活的）"""
    query, params = QueryBuilder("end_work_messages").order_by_field("weekday").build()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


@db_query
def get_active_end_work_messages(conn, cursor) -> List[str]:
    """获取所有激活的收工消息（用于随机选择）"""
    query, params = (
        QueryBuilder("end_work_messages")
        .select("message")
        .where("is_active = ?", 1)
        .build()
    )
    cursor.execute(query, params)
    rows = cursor.fetchall()
    return [row[0] for row in rows if row[0] and row[0].strip()]


@db_transaction
def save_end_work_message(conn, cursor, weekday: int, message: str) -> int:
    """保存或更新收工消息，返回消息ID（weekday: 0=周一, 6=周日）"""
    # 检查是否已存在
    query, params = (
        QueryBuilder("end_work_messages")
        .select("id")
        .where("weekday = ?", weekday)
        .build()
    )
    cursor.execute(query, params)
    row = cursor.fetchone()

    if row:
        # 更新现有记录
        cursor.execute(
            """
        UPDATE end_work_messages
        SET message = ?, is_active = 1, updated_at = CURRENT_TIMESTAMP
        WHERE weekday = ?
        """,
            (message, weekday),
        )
        return row[0]
    else:
        # 创建新记录
        cursor.execute(
            """
        INSERT INTO end_work_messages (weekday, message, is_active)
        VALUES (?, ?, 1)
        """,
            (weekday, message),
        )
        return cursor.lastrowid


@db_transaction
def delete_end_work_message(conn, cursor, weekday: int) -> bool:
    """删除指定星期几的收工消息"""
    cursor.execute("DELETE FROM end_work_messages WHERE weekday = ?", (weekday,))
    return cursor.rowcount > 0


@db_transaction
def toggle_end_work_message(conn, cursor, weekday: int) -> bool:
    """切换收工消息的激活状态"""
    cursor.execute(
        """
    UPDATE end_work_messages
    SET is_active = NOT is_active, updated_at = CURRENT_TIMESTAMP
    WHERE weekday = ?
    """,
        (weekday,),
    )
    return cursor.rowcount > 0
