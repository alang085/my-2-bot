"""撤销操作数据类

使用dataclass封装撤销操作相关的参数。
"""

from dataclasses import dataclass
from typing import Dict, List

from telegram import Update
from telegram.ext import ContextTypes


@dataclass
class UndoResultParams:
    """撤销结果参数

    封装撤销结果路由所需的所有参数。
    """

    update: Update
    context: ContextTypes.DEFAULT_TYPE
    user_id: int
    is_group: bool
    operation_id: int
    operation_type: str
    operation_data: Dict
    undo_message: str
    undo_message_en: str
    undo_count: int
    last_operation: Dict
    success: bool


@dataclass
class SuccessfulUndoParams:
    """成功撤销参数

    封装成功撤销操作所需的所有参数。
    """

    update: Update
    context: ContextTypes.DEFAULT_TYPE
    user_id: int
    is_group: bool
    operation_id: int
    operation_type: str
    operation_data: Dict
    undo_message: str
    undo_message_en: str
    undo_count: int
    last_operation: Dict


@dataclass
class CompleteUndoSuccessParams:
    """完成撤销成功流程参数

    封装完成撤销成功流程所需的所有参数。
    """

    update: Update
    context: ContextTypes.DEFAULT_TYPE
    user_id: int
    is_group: bool
    operation_type: str
    undo_message: str
    undo_message_en: str
    undo_count: int
    last_operation: Dict
    consistency_errors: List[str]


@dataclass
class ExecuteUndoParams:
    """执行撤销操作参数

    封装执行撤销操作所需的所有参数。
    """

    update: Update
    context: ContextTypes.DEFAULT_TYPE
    user_id: int
    is_group: bool
    chat_id: int
    operation_type: str
    operation_data: Dict
    operation_id: int
    undo_count: int
    last_operation: Dict


@dataclass
class FailedUndoParams:
    """失败撤销参数

    封装失败撤销操作所需的所有参数。
    """

    update: Update
    context: ContextTypes.DEFAULT_TYPE
    user_id: int
    is_group: bool
    operation_id: int
    operation_type: str
    undo_count: int
    last_operation: Dict
