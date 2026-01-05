"""订单通知数据类

使用dataclass封装订单通知相关的参数。
"""

from dataclasses import dataclass

from telegram import Update
from telegram.ext import ContextTypes


@dataclass
class OrderNotificationParams:
    """订单通知参数

    封装订单创建通知所需的所有参数。
    """

    update: Update
    context: ContextTypes.DEFAULT_TYPE
    order_id: str
    group_id: str
    created_at: str
    weekday_group: str
    customer: str
    amount: float
    initial_state: str
    is_historical: bool
    chat_id: int


@dataclass
class OrderRecordParams:
    """订单记录参数

    封装订单操作记录所需的所有参数。
    """

    update: Update
    context: ContextTypes.DEFAULT_TYPE
    user_id: int
    order_id: str
    chat_id: int
    group_id: str
    amount: float
    customer: str
    initial_state: str
    is_historical: bool
    created_at: str
