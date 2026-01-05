"""公司公告操作模块

包含公司公告和公告发送计划的配置功能。
"""

# 标准库
from datetime import datetime
from typing import Dict, List, Optional

# 第三方库
import pytz

# 本地模块
from db.base import db_query, db_transaction
from utils.query_builder import QueryBuilder


@db_query
def get_company_announcements(conn, cursor) -> List[Dict]:
    """获取所有激活的公司公告（过滤空消息）"""
    query, params = (
        QueryBuilder("company_announcements")
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
def get_all_company_announcements(conn, cursor) -> List[Dict]:
    """获取所有公司公告（包括未激活的）"""
    query, params = QueryBuilder("company_announcements").order_by_field("id").build()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


@db_transaction
def save_company_announcement(conn, cursor, message: str, is_active: int = 1) -> int:
    """保存公司公告，返回公告ID"""
    cursor.execute(
        """
    INSERT INTO company_announcements (message, is_active)
    VALUES (?, ?)
    """,
        (message, is_active),
    )
    return cursor.lastrowid


@db_transaction
def delete_company_announcement(conn, cursor, announcement_id: int) -> bool:
    """删除公司公告"""
    cursor.execute("DELETE FROM company_announcements WHERE id = ?", (announcement_id,))
    return cursor.rowcount > 0


@db_transaction
def toggle_company_announcement(
    conn, cursor, announcement_id: int, is_active: int
) -> bool:
    """切换公司公告的激活状态"""
    cursor.execute(
        """
    UPDATE company_announcements
    SET is_active = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """,
        (is_active, announcement_id),
    )
    return cursor.rowcount > 0


@db_query
def get_announcement_schedule(conn, cursor) -> Optional[Dict]:
    """获取公告发送计划配置"""
    query, params = QueryBuilder("announcement_schedule").where("id = ?", 1).build()
    cursor.execute(query, params)
    row = cursor.fetchone()
    if row:
        return dict(row)
    return None


@db_transaction
def save_announcement_schedule(
    conn, cursor, interval_hours: int = 3, is_active: int = 1
) -> bool:
    """保存公告发送计划配置"""
    query, params = QueryBuilder("announcement_schedule").where("id = ?", 1).build()
    cursor.execute(query, params)
    row = cursor.fetchone()

    if row:
        # 更新
        cursor.execute(
            """
        UPDATE announcement_schedule
        SET interval_hours = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = 1
        """,
            (interval_hours, is_active),
        )
        return cursor.rowcount > 0
    else:
        # 创建
        cursor.execute(
            """
        INSERT INTO announcement_schedule (id, interval_hours, is_active)
        VALUES (1, ?, ?)
        """,
            (interval_hours, is_active),
        )
        return True


@db_transaction
def update_announcement_last_sent(conn, cursor) -> bool:
    """更新公告最后发送时间"""
    tz = pytz.timezone("Asia/Shanghai")
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        """
    UPDATE announcement_schedule
    SET last_sent_at = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = 1
    """,
        (now,),
    )
    return cursor.rowcount > 0
