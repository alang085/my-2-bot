"""客户信用数据库操作"""

import logging
from typing import Dict, Optional

from db.base import db_query, db_transaction

logger = logging.getLogger(__name__)


@db_transaction
def create_credit_record(conn, cursor, customer_id: str) -> bool:
    """创建客户信用记录（默认分数500）"""
    # 检查是否已存在
    cursor.execute(
        "SELECT customer_id FROM customer_credit WHERE customer_id = ?", (customer_id,)
    )
    if cursor.fetchone():
        logger.warning(f"信用记录已存在: customer_id={customer_id}")
        return False

    cursor.execute(
        """
        INSERT INTO customer_credit (
            customer_id, credit_score, credit_level, consecutive_payments,
            created_at, updated_at
        ) VALUES (?, 500, 'C', 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        (customer_id,),
    )
    logger.info(f"创建信用记录: customer_id={customer_id}")
    return True


@db_query
def get_credit_by_customer_id(conn, cursor, customer_id: str) -> Optional[dict]:
    """根据客户ID获取信用记录"""
    cursor.execute(
        "SELECT * FROM customer_credit WHERE customer_id = ? LIMIT 1", (customer_id,)
    )
    row = cursor.fetchone()
    if row:
        return dict(row)
    return None


@db_transaction
def _fetch_customer_credit(cursor, customer_id: str) -> Optional[Dict]:
    """获取客户信用信息

    Args:
        cursor: 数据库游标
        customer_id: 客户ID

    Returns:
        信用信息字典或None
    """
    cursor.execute(
        "SELECT * FROM customer_credit WHERE customer_id = ? LIMIT 1", (customer_id,)
    )
    row = cursor.fetchone()
    if not row:
        return None
    return dict(row)


def _calculate_credit_score_change(consecutive: int) -> int:
    """计算信用分数变化

    Args:
        consecutive: 连续付息次数

    Returns:
        分数变化值
    """
    score_change = 10
    if consecutive % 3 == 0:
        score_change += 10
    return score_change


def _determine_credit_level(score: int) -> str:
    """确定信用等级

    Args:
        score: 信用分数

    Returns:
        信用等级
    """
    if score >= 800:
        return "A"
    elif score >= 600:
        return "B"
    elif score >= 400:
        return "C"
    else:
        return "D"


def _update_credit_in_database(
    cursor, customer_id: str, score_after: int, credit_level: str, consecutive: int
) -> None:
    """更新数据库中的信用信息

    Args:
        cursor: 数据库游标
        customer_id: 客户ID
        score_after: 更新后的分数
        credit_level: 信用等级
        consecutive: 连续付息次数
    """
    cursor.execute(
        """
        UPDATE customer_credit 
        SET credit_score = ?, credit_level = ?, consecutive_payments = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE customer_id = ?
        """,
        (score_after, credit_level, consecutive, customer_id),
    )


def update_credit_on_payment(
    conn, cursor, customer_id: str, order_id: Optional[str] = None
) -> tuple[bool, Optional[dict]]:
    """付息时更新信用（+10分，连续付息+10分）"""
    credit = _fetch_customer_credit(cursor, customer_id)
    if not credit:
        return False, None

    score_before = credit["credit_score"]
    consecutive = credit.get("consecutive_payments", 0) + 1

    score_change = _calculate_credit_score_change(consecutive)
    score_after = min(1000, score_before + score_change)
    credit_level = _determine_credit_level(score_after)

    _update_credit_in_database(
        cursor, customer_id, score_after, credit_level, consecutive
    )

    change_data = {
        "score_before": score_before,
        "score_after": score_after,
        "score_change": score_change,
        "consecutive": consecutive,
    }

    return True, change_data


@db_transaction
def update_credit_on_breach(
    conn, cursor, customer_id: str, order_id: Optional[str] = None
) -> bool:
    """违约时清零信用"""
    cursor.execute(
        """
        UPDATE customer_credit 
        SET credit_score = 0, credit_level = 'D', consecutive_payments = 0,
            updated_at = CURRENT_TIMESTAMP
        WHERE customer_id = ?
        """,
        (customer_id,),
    )
    return cursor.rowcount > 0


@db_query
def get_credit_benefits(conn, cursor, customer_id: str) -> Optional[dict]:
    """获取信用权益"""
    credit = get_credit_by_customer_id(conn, cursor, customer_id)
    if not credit:
        return None

    score = credit["credit_score"]
    level = credit["credit_level"]

    # 根据信用等级计算权益
    benefits = {
        "credit_score": score,
        "credit_level": level,
        "max_loan_amount": 0,
        "interest_rate_discount": 0,
    }

    if level == "A":
        benefits["max_loan_amount"] = 50000
        benefits["interest_rate_discount"] = 0.1
    elif level == "B":
        benefits["max_loan_amount"] = 30000
        benefits["interest_rate_discount"] = 0.05
    elif level == "C":
        benefits["max_loan_amount"] = 20000
        benefits["interest_rate_discount"] = 0
    else:
        benefits["max_loan_amount"] = 10000
        benefits["interest_rate_discount"] = 0

    return benefits
