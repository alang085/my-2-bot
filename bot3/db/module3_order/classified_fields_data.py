"""分类表字段更新数据类

使用dataclass封装分类表字段更新相关的参数。
"""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ClassifiedFieldsUpdateParams:
    """分类表字段更新参数

    封装更新所有分类表字段所需的所有参数。
    """

    cursor: Any
    order_data: Dict
    new_order_id: str
    new_date_str: str
    new_weekday_group: str
    new_customer: str
    new_amount: float
    new_state: str
    updated_at: str
