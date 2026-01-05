"""客户价值服务"""

import logging
from typing import Optional

from db.module6_credit.customer_value import create_value_record
from db.module6_credit.customer_value import \
    get_top_customers as db_get_top_customers
from db.module6_credit.customer_value import get_value_by_customer_id
from db.module6_credit.customer_value import \
    update_value_on_order as db_update_value_on_order

logger = logging.getLogger(__name__)


async def initialize_value(customer_id: str) -> bool:
    """初始化客户价值记录"""
    return await get_value_by_customer_id(customer_id) or await create_value_record(
        customer_id
    )


async def get_value_info(customer_id: str) -> Optional[dict]:
    """获取客户价值信息"""
    return await get_value_by_customer_id(customer_id)


async def update_value_on_order(
    customer_id: str, order_amount: float, is_completed: bool = False
) -> tuple[bool, Optional[str]]:
    """订单时更新价值"""
    success = await db_update_value_on_order(customer_id, order_amount, is_completed)
    if success:
        return True, None
    return False, "❌ 更新价值失败"


async def update_value_on_payment(
    customer_id: str, interest_amount: float
) -> tuple[bool, Optional[str]]:
    """付息时更新价值"""
    from db.module6_credit.customer_value import \
        update_value_on_payment as db_update_value_on_payment

    success = await db_update_value_on_payment(customer_id, interest_amount)
    if success:
        return True, None
    return False, "❌ 更新价值失败"


async def get_top_customers(
    min_score: Optional[int] = None,
    min_profit: Optional[float] = None,
    min_orders: Optional[int] = None,
    limit: int = 20,
) -> list[dict]:
    """获取优质客户列表"""
    return await db_get_top_customers(min_score, min_profit, min_orders, limit)
