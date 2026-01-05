"""格式化辅助模块

包含消息格式化相关的辅助函数。
"""

# 标准库
from typing import Any, Dict, Optional

from utils.message_builders import MessageBuilder


def format_error(
    error: str,
    details: Optional[Dict[str, Any]] = None,
    is_group: bool = False,
) -> str:
    """统一格式化错误消息

    Args:
        error: 错误描述
        details: 详细信息字典
        is_group: 是否为群聊（群聊使用简短消息）

    Returns:
        格式化后的错误消息
    """
    return MessageBuilder.build_error_message(error, details, is_group)
