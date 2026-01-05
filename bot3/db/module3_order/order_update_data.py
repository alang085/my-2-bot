"""订单更新数据类

使用dataclass封装订单更新相关的参数。
"""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ClassifiedTableUpdateParams:
    """分类表更新参数

    封装分类表更新所需的所有参数。

    参数分组：
    - 状态变更：old_state, new_state
    - 星期分组变更：old_weekday_group, new_weekday_group
    - 客户类型变更：old_customer, new_customer
    - 订单信息：order_id, order_data, old_created_at, updated_at
    - 数据库操作：cursor
    """

    # 数据库操作
    cursor: Any

    # 状态变更
    old_state: str
    new_state: str

    # 星期分组变更
    old_weekday_group: str
    new_weekday_group: str

    # 客户类型变更
    old_customer: str
    new_customer: str

    # 订单信息
    order_id: str
    order_data: Dict[str, Any]
    old_created_at: str
    updated_at: str
