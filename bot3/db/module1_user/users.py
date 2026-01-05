"""
用户权限操作模块

包含授权用户和用户归属映射的管理。
"""

# 标准库
import logging
from datetime import datetime
from typing import Dict, List, Optional

# 本地模块
from db.base import db_query, db_transaction

# 日志
logger = logging.getLogger(__name__)


# ========== 授权用户操作 ==========


@db_transaction
def add_authorized_user(conn, cursor, user_id: int) -> bool:
    """添加授权用户"""
    cursor.execute(
        "INSERT OR IGNORE INTO authorized_users (user_id) VALUES (?)", (user_id,)
    )
    return True


@db_transaction
def remove_authorized_user(conn, cursor, user_id: int) -> bool:
    """移除授权用户"""
    cursor.execute("DELETE FROM authorized_users WHERE user_id = ?", (user_id,))
    return True


@db_query
def get_authorized_users(conn, cursor) -> List[int]:
    """获取所有授权用户ID"""
    cursor.execute("SELECT user_id FROM authorized_users")
    rows = cursor.fetchall()
    return [row[0] for row in rows]


@db_query
def is_user_authorized(conn, cursor, user_id: int) -> bool:
    """检查用户是否授权"""
    cursor.execute("SELECT 1 FROM authorized_users WHERE user_id = ?", (user_id,))
    return cursor.fetchone() is not None


# ========== 用户归属ID映射操作 ==========


@db_query
def get_user_group_id(conn, cursor, user_id: int) -> Optional[str]:
    """获取用户有权限查看的归属ID"""
    cursor.execute(
        "SELECT group_id FROM user_group_mapping WHERE user_id = ?", (user_id,)
    )
    row = cursor.fetchone()
    return row[0] if row else None


@db_transaction
def set_user_group_id(conn, cursor, user_id: int, group_id: str) -> bool:
    """设置用户有权限查看的归属ID"""
    cursor.execute(
        """
    INSERT OR REPLACE INTO user_group_mapping (user_id, group_id, updated_at)
    VALUES (?, ?, CURRENT_TIMESTAMP)
    """,
        (user_id, group_id),
    )
    return True


@db_transaction
def remove_user_group_id(conn, cursor, user_id: int) -> bool:
    """移除用户的归属ID映射"""
    cursor.execute("DELETE FROM user_group_mapping WHERE user_id = ?", (user_id,))
    return cursor.rowcount > 0


@db_query
def get_all_user_group_mappings(conn, cursor) -> List[Dict]:
    """获取所有用户归属ID映射"""
    cursor.execute(
        """
    SELECT user_id, group_id, created_at, updated_at
    FROM user_group_mapping
    ORDER BY user_id
    """
    )
    rows = cursor.fetchall()
    return [dict(row) for row in rows]
