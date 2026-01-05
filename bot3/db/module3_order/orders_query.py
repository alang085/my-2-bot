"""订单查询操作模块

包含订单的查询功能。
"""

from typing import Dict, Optional

# 本地模块
from db.base import db_query
from utils.query_builder import QueryBuilder


@db_query
def get_order_by_chat_id(conn, cursor, chat_id: int) -> Optional[Dict]:
    """根据chat_id获取订单（排除end和breach_end状态）"""
    query, params = (
        QueryBuilder("orders")
        .where("chat_id = ?", chat_id)
        .where_not_in("state", ["end", "breach_end"])
        .build()
    )
    cursor.execute(query, params)
    row = cursor.fetchone()
    return dict(row) if row else None


@db_query
def get_order_by_chat_id_including_archived(
    conn, cursor, chat_id: int
) -> Optional[Dict]:
    """根据chat_id获取订单（包括end和breach_end状态）"""
    query, params = QueryBuilder("orders").where("chat_id = ?", chat_id).build()
    cursor.execute(query, params)
    row = cursor.fetchone()
    return dict(row) if row else None


@db_query
def get_order_by_order_id(conn, cursor, order_id: str) -> Optional[Dict]:
    """根据order_id获取订单"""
    query, params = QueryBuilder("orders").where("order_id = ?", order_id).build()
    cursor.execute(query, params)
    row = cursor.fetchone()
    return dict(row) if row else None
