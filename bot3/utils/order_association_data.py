"""订单关联数据类

使用dataclass封装订单关联相关的参数。
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from telegram import Update
from telegram.ext import ContextTypes


@dataclass
class OrderAssociationParams:
    """订单关联参数

    封装处理订单关联所需的所有参数。
    """

    update: Update
    order_id: str
    existing_chat_id: int
    chat_id: int
    existing_title: Optional[str]
    title: str
    existing_state: str
    manual_trigger: bool
