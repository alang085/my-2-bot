"""撤销验证数据类

使用dataclass封装撤销验证相关的参数。
"""

from dataclasses import dataclass
from typing import Dict

from telegram import Update


@dataclass
class UndoVerificationParams:
    """撤销验证参数

    封装撤销验证和记录历史所需的所有参数。
    """

    update: Update
    user_id: int
    operation_id: int
    operation_type: str
    operation_data: Dict
    undo_message: str
    undo_message_en: str
    is_group: bool
