"""群组消息配置数据类

使用dataclass封装群组消息配置相关的参数。
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class GroupMessageConfigParams:
    """群组消息配置参数

    封装保存群组消息配置所需的所有参数。
    """

    conn: Any
    cursor: Any
    chat_id: int
    chat_title: Optional[str] = None
    start_work_message: Optional[str] = None
    end_work_message: Optional[str] = None
    welcome_message: Optional[str] = None
    bot_links: Optional[str] = None
    worker_links: Optional[str] = None
    is_active: int = 1
    extra_fields: Optional[Dict[str, Any]] = None
