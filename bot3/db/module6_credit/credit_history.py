"""信用变更历史数据库操作"""

import logging
from typing import Optional

from db.base import db_transaction
from db.module6_credit.credit_history_data import CreditChangeParams

logger = logging.getLogger(__name__)


@db_transaction
def record_credit_change(
    conn=None,
    cursor=None,
    customer_id: Optional[str] = None,
    change_type: Optional[str] = None,
    score_change: Optional[int] = None,
    score_before: Optional[int] = None,
    score_after: Optional[int] = None,
    order_id: Optional[str] = None,
    reason: Optional[str] = None,
    params: Optional[CreditChangeParams] = None,
) -> bool:
    """记录信用变更历史

    支持两种调用方式：
    1. 旧方式（向后兼容）：直接传递参数
    2. 新方式：传递CreditChangeParams对象

    Args:
        conn: 数据库连接（旧方式，由装饰器提供）
        cursor: 数据库游标（旧方式，由装饰器提供）
        customer_id: 客户ID（旧方式）
        change_type: 变更类型（旧方式）
        score_change: 分数变化（旧方式）
        score_before: 变更前分数（旧方式）
        score_after: 变更后分数（旧方式）
        order_id: 订单ID（旧方式）
        reason: 原因（旧方式）
        params: 信用变更参数（新方式）

    Returns:
        是否成功
    """
    # 向后兼容：如果使用旧方式调用，创建params对象
    if params is None:
        if customer_id is None:
            raise ValueError("必须提供customer_id或params参数")
        params = CreditChangeParams(
            conn=conn,
            cursor=cursor,
            customer_id=customer_id,
            change_type=change_type,
            score_change=score_change,
            score_before=score_before,
            score_after=score_after,
            order_id=order_id,
            reason=reason,
        )

    params.cursor.execute(
        """
        INSERT INTO credit_history (
            customer_id, change_type, score_change, score_before, score_after,
            order_id, reason, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (
            params.customer_id,
            params.change_type,
            params.score_change,
            params.score_before,
            params.score_after,
            params.order_id,
            params.reason,
        ),
    )
    logger.info(
        f"记录信用变更: customer_id={params.customer_id}, change_type={params.change_type}, "
        f"score_change={params.score_change}"
    )
    return True
