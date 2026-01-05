"""订单消息数据类

使用dataclass封装订单消息相关的参数。
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class OrderCreationMessageParams:
    """订单创建消息参数

    封装构建订单创建消息所需的所有参数。
    """

    order_id: str
    group_id: str
    created_at: str
    weekday_group: Optional[str]
    customer: str
    amount: float
    initial_state: str
    is_historical: bool = False
