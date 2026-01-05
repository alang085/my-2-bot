"""信用评分服务"""

import logging
from typing import Optional

from db.module6_credit.credit_history import record_credit_change
from db.module6_credit.customer_credit import (create_credit_record,
                                               get_credit_benefits,
                                               get_credit_by_customer_id)
from db.module6_credit.customer_credit import \
    update_credit_on_breach as db_update_credit_on_breach
from db.module6_credit.customer_credit import \
    update_credit_on_payment as db_update_credit_on_payment

# 注意：update_credit_on_payment 和 update_credit_on_breach 是同步函数
# 需要通过 db.base 的装饰器转换为异步

logger = logging.getLogger(__name__)


async def initialize_credit(customer_id: str) -> bool:
    """初始化客户信用记录"""
    return await get_credit_by_customer_id(customer_id) or await create_credit_record(
        customer_id
    )


async def get_credit_info(customer_id: str) -> Optional[dict]:
    """获取客户信用信息"""
    return await get_credit_by_customer_id(customer_id)


async def update_credit_on_payment(
    customer_id: str, order_id: Optional[str] = None
) -> tuple[bool, Optional[str], Optional[dict]]:
    """付息时更新信用"""
    success, change_data = await db_update_credit_on_payment(customer_id, order_id)
    if not success:
        return False, "❌ 更新信用失败", None

    # 记录信用变更历史
    await record_credit_change(
        customer_id=customer_id,
        change_type="payment_on_time",
        score_change=change_data["score_change"],
        score_before=change_data["score_before"],
        score_after=change_data["score_after"],
        order_id=order_id,
        reason="准时付息",
    )

    # 检查是否触发连续奖励
    if change_data.get("consecutive") == 0:
        # 触发连续奖励，记录额外加分
        await record_credit_change(
            customer_id=customer_id,
            change_type="consecutive_bonus",
            score_change=10,
            score_before=change_data["score_after"] - 10,
            score_after=change_data["score_after"],
            order_id=order_id,
            reason="连续三次准时付息奖励",
        )

    return True, None, change_data


async def update_credit_on_breach(
    customer_id: str, order_id: Optional[str] = None
) -> tuple[bool, Optional[str]]:
    """违约时清零信用"""
    credit = await get_credit_by_customer_id(customer_id)
    if not credit:
        return False, "❌ 信用记录不存在"

    score_before = credit["credit_score"]
    success = await db_update_credit_on_breach(customer_id, order_id)

    if success:
        # 记录信用变更历史
        await record_credit_change(
            customer_id=customer_id,
            change_type="breach",
            score_change=-score_before,  # 清零
            score_before=score_before,
            score_after=0,
            order_id=order_id,
            reason="违约清零",
        )
        return True, None
    return False, "❌ 更新信用失败"


async def get_credit_benefits(customer_id: str) -> Optional[dict]:
    """获取信用权益"""
    from db.module6_credit.customer_credit import \
        get_credit_benefits as db_get_credit_benefits

    return await db_get_credit_benefits(customer_id)
