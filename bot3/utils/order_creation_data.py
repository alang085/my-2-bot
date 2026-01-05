"""订单创建数据类

使用dataclass封装订单创建相关的参数，减少函数参数数量。
"""

from dataclasses import dataclass
from typing import Any, Dict

from telegram import Update
from telegram.ext import ContextTypes


@dataclass
class OrderCreationParams:
    """订单创建参数

    封装订单创建流程所需的所有参数。
    """

    update: Update
    context: ContextTypes.DEFAULT_TYPE
    parsed_info: Dict[str, Any]
    chat_id: int
    order_id: str
    customer: str
    amount: float
    initial_state: str
    group_id: str
    weekday_group: str
    created_at: str
    is_historical: bool
    order_date: Any


@dataclass
class OrderPostCreationParams:
    """订单创建后处理参数

    封装订单创建后的后续处理步骤所需参数。
    """

    update: Update
    context: ContextTypes.DEFAULT_TYPE
    order_id: str
    customer: str
    amount: float
    initial_state: str
    group_id: str
    weekday_group: str
    created_at: str
    is_historical: bool
    chat_id: int
