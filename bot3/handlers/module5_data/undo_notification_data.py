"""撤销操作通知数据类

使用dataclass封装撤销操作通知相关的参数。
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class AdminNotificationParams:
    """管理员通知参数

    封装成功撤销操作的管理员通知所需的所有参数（用于构建消息）。
    """

    user_full_name: str
    username: str
    user_id: int
    chat_info: str
    operation_type: str
    undo_message: str
    undo_message_en: str
    is_group: bool
    undo_count: int
    created_at: str
    consistency_status: str


@dataclass
class SendUndoAdminNotificationParams:
    """发送撤销管理员通知参数

    封装发送撤销管理员通知所需的所有输入参数。
    """

    update: "Update"
    context: "ContextTypes.DEFAULT_TYPE"
    user_id: int
    is_group: bool
    operation_type: str
    undo_message: str
    undo_message_en: str
    undo_count: int
    last_operation: dict
    consistency_errors: list


@dataclass
class FailureAdminNotificationParams:
    """失败撤销管理员通知参数

    封装失败撤销操作的管理员通知所需的所有参数。
    """

    user_full_name: str
    username: str
    user_id: int
    chat_info: str
    operation_type: str
    operation_id: int
    created_at: str
    undo_count: int


@dataclass
class ExceptionAdminNotificationParams:
    """异常撤销管理员通知参数

    封装异常撤销操作的管理员通知所需的所有参数。
    """

    user_full_name: str
    username: str
    user_id_str: str
    chat_info: str
    error: Exception
