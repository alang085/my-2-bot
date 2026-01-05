"""撤销操作历史数据类

使用dataclass封装撤销操作历史相关的参数。
"""

from dataclasses import dataclass
from typing import Dict, List

from telegram import Update
from telegram.ext import ContextTypes


@dataclass
class UndoHistoryParams:
    """撤销操作历史参数

    封装记录撤销操作历史所需的所有参数。
    """

    update: Update
    user_id: int
    operation_id: int
    operation_type: str
    operation_data: Dict
    undo_message: str
    undo_message_en: str
    is_group: bool
    consistency_errors: List[str]
