"""订单完成数据类

使用dataclass封装订单完成相关的参数。
"""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class CompletionHistoryParams:
    """订单完成历史参数

    封装记录订单完成操作历史所需的所有参数。
    """

    user_id: Optional[int]
    chat_id: int
    order_model: Any
    group_id: str
    amount: float
    old_state: str
    date_str: str
    income_record_id: Optional[int]
