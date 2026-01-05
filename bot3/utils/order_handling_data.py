"""订单处理数据类

使用dataclass封装订单处理相关的参数。
"""

from dataclasses import dataclass
from typing import Any, Dict

from telegram import Update
from telegram.ext import ContextTypes


@dataclass
class ExistingOrderLogicParams:
    """已存在订单逻辑参数

    封装处理已存在订单逻辑所需的所有参数。
    """

    update: Update
    context: ContextTypes.DEFAULT_TYPE
    existing_order: Dict[str, Any]
    parsed_info: Dict[str, Any]
    title: str
    order_id: str
    chat_id: int
    manual_trigger: bool


@dataclass
class ExistingOrderFlowParams:
    """已存在订单流程参数

    封装处理已存在订单流程所需的所有参数。
    """

    update: Update
    context: ContextTypes.DEFAULT_TYPE
    existing_order: Dict[str, Any]
    parsed_info: Dict[str, Any]
    title: str
    order_id: str
    chat_id: int
    manual_trigger: bool


@dataclass
class NewOrderCreationParams:
    """新订单创建参数

    封装处理新订单创建所需的所有参数。
    """

    update: Update
    context: ContextTypes.DEFAULT_TYPE
    chat_id: int
    parsed_info: Dict[str, Any]
    title: str
    order_id: str
    allow_create_new: bool
    manual_trigger: bool
