"""公司宣传轮播语录操作模块

包含公司宣传轮播语录的配置功能。
"""

from typing import Dict, List, Optional

# 本地模块
from db.base import db_query, db_transaction
from utils.query_builder import QueryBuilder


@db_query
def get_active_promotion_messages(conn, cursor) -> List[Dict]:
    """获取所有激活的公司宣传轮播语录（过滤空消息）"""
    query, params = (
        QueryBuilder("company_promotion_messages")
        .where("is_active = ?", 1)
        .order_by_field("id")
        .build()
    )
    cursor.execute(query, params)
    rows = cursor.fetchall()
    # 过滤掉空消息或只有空白字符的消息
    result = []
    for row in rows:
        message = row["message"]
        if message and message.strip():  # 确保消息不为空且不只是空白字符
            result.append(dict(row))
    return result


@db_query
def get_all_promotion_messages(conn, cursor) -> List[Dict]:
    """获取所有公司宣传轮播语录（包括未激活的）"""
    query, params = (
        QueryBuilder("company_promotion_messages").order_by_field("id").build()
    )
    cursor.execute(query, params)
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


@db_transaction
def save_promotion_message(conn, cursor, message: str) -> int:
    """保存公司宣传轮播语录，返回语录ID"""
    cursor.execute(
        """
    INSERT INTO company_promotion_messages (message, is_active)
    VALUES (?, 1)
    """,
        (message,),
    )
    return cursor.lastrowid


@db_transaction
def delete_promotion_message(conn, cursor, message_id: int) -> bool:
    """删除公司宣传轮播语录"""
    cursor.execute("DELETE FROM company_promotion_messages WHERE id = ?", (message_id,))
    return cursor.rowcount > 0


@db_transaction
def toggle_promotion_message(conn, cursor, message_id: int) -> bool:
    """切换公司宣传轮播语录的激活状态"""
    cursor.execute(
        """
    UPDATE company_promotion_messages
    SET is_active = NOT is_active, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """,
        (message_id,),
    )
    return cursor.rowcount > 0


@db_query
def get_promotion_schedule(conn, cursor) -> Optional[Dict]:
    """获取公司宣传轮播发送计划（复用公告计划表结构）"""
    # 使用公告计划表存储，但可以扩展为独立表
    query, params = QueryBuilder("announcement_schedule").where("id = ?", 1).build()
    cursor.execute(query, params)
    row = cursor.fetchone()
    return dict(row) if row else None
