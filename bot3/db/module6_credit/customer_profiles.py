"""客户档案数据库操作"""

import logging
from hashlib import md5
from typing import Optional

from db.base import db_query, db_transaction

logger = logging.getLogger(__name__)


def _generate_customer_id(phone: str) -> str:
    """从电话生成客户ID"""
    # 使用MD5哈希电话，取前8位，加上CUST_前缀
    phone_hash = md5(phone.encode()).hexdigest()[:8].upper()
    return f"CUST_{phone_hash}"


@db_transaction
def create_customer_profile(
    conn, cursor, name: str, phone: str, id_card: Optional[str] = None
) -> Optional[str]:
    """创建客户档案"""
    customer_id = _generate_customer_id(phone)

    # 检查是否已存在
    cursor.execute(
        "SELECT customer_id FROM customer_profiles WHERE phone = ?", (phone,)
    )
    existing = cursor.fetchone()
    if existing:
        logger.warning(f"客户档案已存在: phone={phone}")
        return None

    # 创建客户档案
    cursor.execute(
        """
        INSERT INTO customer_profiles (
            customer_id, name, phone, id_card, customer_type, created_at
        ) VALUES (?, ?, ?, ?, 'white', CURRENT_TIMESTAMP)
        """,
        (customer_id, name, phone, id_card),
    )

    logger.info(f"创建客户档案: customer_id={customer_id}, name={name}, phone={phone}")
    return customer_id


@db_query
def get_customer_by_phone(conn, cursor, phone: str) -> Optional[dict]:
    """根据电话获取客户档案"""
    cursor.execute("SELECT * FROM customer_profiles WHERE phone = ? LIMIT 1", (phone,))
    row = cursor.fetchone()
    if row:
        return dict(row)
    return None


@db_query
def get_customer_by_id(conn, cursor, customer_id: str) -> Optional[dict]:
    """根据客户ID获取客户档案"""
    cursor.execute(
        "SELECT * FROM customer_profiles WHERE customer_id = ? LIMIT 1", (customer_id,)
    )
    row = cursor.fetchone()
    if row:
        return dict(row)
    return None


@db_transaction
def update_customer_profile(conn, cursor, phone: str, field: str, value: str) -> bool:
    """更新客户档案字段"""
    valid_fields = ["name", "id_card"]
    if field not in valid_fields:
        logger.error(f"无效的字段名: {field}")
        return False

    cursor.execute(
        f"UPDATE customer_profiles SET {field} = ?, updated_at = CURRENT_TIMESTAMP WHERE phone = ?",
        (value, phone),
    )
    return cursor.rowcount > 0


@db_transaction
def set_customer_type(conn, cursor, phone: str, customer_type: str) -> bool:
    """设置客户类型（white/black）"""
    if customer_type not in ["white", "black"]:
        logger.error(f"无效的客户类型: {customer_type}")
        return False

    cursor.execute(
        """UPDATE customer_profiles
        SET customer_type = ?, updated_at = CURRENT_TIMESTAMP
        WHERE phone = ?""",
        (customer_type, phone),
    )
    return cursor.rowcount > 0


@db_query
def list_customers(conn, cursor, limit: int = 100) -> list:
    """列出所有客户档案"""
    cursor.execute(
        "SELECT * FROM customer_profiles ORDER BY created_at DESC LIMIT ?",
        (limit,),
    )
    rows = cursor.fetchall()
    return [dict(row) for row in rows]
