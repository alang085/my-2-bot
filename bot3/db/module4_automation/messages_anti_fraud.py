"""防诈骗语录操作模块

包含防诈骗语录的配置功能。
"""

from typing import Dict, List

# 本地模块
from db.base import db_query, db_transaction
from utils.query_builder import QueryBuilder


@db_query
def get_active_anti_fraud_messages(conn, cursor) -> List[str]:
    """获取所有激活的防诈骗语录"""
    query, params = (
        QueryBuilder("anti_fraud_messages")
        .select("message")
        .where("is_active = ?", 1)
        .build()
    )
    cursor.execute(query, params)
    rows = cursor.fetchall()
    return [row[0] for row in rows]


@db_query
def get_all_anti_fraud_messages(conn, cursor) -> List[Dict]:
    """获取所有防诈骗语录（包括未激活的）"""
    query, params = QueryBuilder("anti_fraud_messages").order_by_field("id").build()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


@db_transaction
def save_anti_fraud_message(conn, cursor, message: str) -> int:
    """保存防诈骗语录，返回语录ID"""
    cursor.execute(
        """
    INSERT INTO anti_fraud_messages (message, is_active)
    VALUES (?, 1)
    """,
        (message,),
    )
    return cursor.lastrowid


@db_transaction
def delete_anti_fraud_message(conn, cursor, message_id: int) -> bool:
    """删除防诈骗语录"""
    cursor.execute("DELETE FROM anti_fraud_messages WHERE id = ?", (message_id,))
    return cursor.rowcount > 0


@db_transaction
def toggle_anti_fraud_message(conn, cursor, message_id: int) -> bool:
    """切换防诈骗语录的激活状态"""
    cursor.execute(
        """
    UPDATE anti_fraud_messages
    SET is_active = NOT is_active, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """,
        (message_id,),
    )
    return cursor.rowcount > 0
