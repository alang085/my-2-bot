"""定时播报操作模块

包含定时播报的配置功能。
"""

from typing import Any, Dict, List, Optional

# 本地模块
from db.base import db_query, db_transaction
from db.module4_automation.schedule_broadcast_data import \
    ScheduledBroadcastParams
from utils.query_builder import QueryBuilder


@db_query
def get_scheduled_broadcast(conn, cursor, slot: int) -> Optional[Dict]:
    """获取指定槽位的定时播报"""
    cursor.execute("SELECT * FROM scheduled_broadcasts WHERE slot = ?", (slot,))
    row = cursor.fetchone()
    return dict(row) if row else None


@db_query
def get_all_scheduled_broadcasts(conn, cursor) -> List[Dict]:
    """获取所有定时播报"""
    query, params = QueryBuilder("scheduled_broadcasts").order_by_field("slot").build()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


@db_query
def get_active_scheduled_broadcasts(conn, cursor) -> List[Dict]:
    """获取所有激活的定时播报"""
    query, params = (
        QueryBuilder("scheduled_broadcasts")
        .where("is_active = ?", 1)
        .order_by_field("slot")
        .build()
    )
    cursor.execute(query, params)
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def _create_or_update_scheduled_broadcast_impl(
    params: ScheduledBroadcastParams,
) -> bool:
    """创建或更新定时播报（内部实现）

    Args:
        params: 定时播报参数

    Returns:
        是否成功
    """
    query, query_params = (
        QueryBuilder("scheduled_broadcasts").where("slot = ?", params.slot).build()
    )
    params.cursor.execute(query, query_params)
    row = params.cursor.fetchone()

    if row:
        # 更新现有记录
        params.cursor.execute(
            """
        UPDATE scheduled_broadcasts
        SET time = ?, chat_id = ?, chat_title = ?, message = ?,
            is_active = ?, updated_at = CURRENT_TIMESTAMP
        WHERE slot = ?
        """,
            (
                params.time,
                params.chat_id,
                params.chat_title,
                params.message,
                params.is_active,
                params.slot,
            ),
        )
    else:
        # 创建新记录
        params.cursor.execute(
            """
        INSERT INTO scheduled_broadcasts (slot, time, chat_id, chat_title, message, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                params.slot,
                params.time,
                params.chat_id,
                params.chat_title,
                params.message,
                params.is_active,
            ),
        )

    return True


@db_transaction
def create_or_update_scheduled_broadcast(
    conn,
    cursor,
    slot: int,
    time: str,
    chat_id: Optional[int] = None,
    chat_title: Optional[str] = None,
    message: str = "",
    is_active: int = 1,
) -> bool:
    """创建或更新定时播报（向后兼容包装）

    Args:
        conn: 数据库连接（由装饰器注入）
        cursor: 数据库游标（由装饰器注入）
        slot: 播报槽位
        time: 播报时间
        chat_id: 聊天ID
        chat_title: 聊天标题
        message: 播报消息
        is_active: 是否激活

    Returns:
        是否成功
    """
    params = ScheduledBroadcastParams(
        conn=conn,
        cursor=cursor,
        slot=slot,
        time=time,
        chat_id=chat_id,
        chat_title=chat_title,
        message=message,
        is_active=is_active,
    )
    return _create_or_update_scheduled_broadcast_impl(params)


@db_transaction
def delete_scheduled_broadcast(conn, cursor, slot: int) -> bool:
    """删除定时播报"""
    cursor.execute("DELETE FROM scheduled_broadcasts WHERE slot = ?", (slot,))
    return cursor.rowcount > 0


@db_transaction
def toggle_scheduled_broadcast(conn, cursor, slot: int, is_active: int) -> bool:
    """切换定时播报的激活状态"""
    cursor.execute(
        """
    UPDATE scheduled_broadcasts
    SET is_active = ?, updated_at = CURRENT_TIMESTAMP
    WHERE slot = ?
    """,
        (is_active, slot),
    )
    return cursor.rowcount > 0
