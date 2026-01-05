"""客户档案服务"""

import logging
from typing import Optional, Tuple

from db.module6_credit.customer_profiles import (create_customer_profile,
                                                 get_customer_by_id,
                                                 get_customer_by_phone,
                                                 list_customers,
                                                 set_customer_type,
                                                 update_customer_profile)

logger = logging.getLogger(__name__)


async def create_customer(
    name: str, phone: str, id_card: Optional[str] = None
) -> Tuple[bool, Optional[str], Optional[dict]]:
    """创建客户档案"""
    customer_id = await create_customer_profile(name, phone, id_card)
    if customer_id:
        customer = await get_customer_by_phone(phone)
        return True, None, customer
    return False, "客户档案已存在或创建失败", None


async def get_customer(phone: str) -> Optional[dict]:
    """获取客户档案"""
    return await get_customer_by_phone(phone)


async def list_customers_func(limit: int = 100) -> list:
    """列出所有客户档案"""
    return await list_customers(limit)


async def update_customer(
    phone: str, field: str, value: str
) -> Tuple[bool, Optional[str]]:
    """更新客户档案"""
    success = await update_customer_profile(phone, field, value)
    if success:
        return True, None
    return False, "更新失败或客户不存在"


async def set_customer_type_func(
    phone: str, customer_type: str
) -> Tuple[bool, Optional[str]]:
    """设置客户类型"""
    success = await set_customer_type(phone, customer_type)
    if success:
        return True, None
    return False, "设置失败或客户不存在"
