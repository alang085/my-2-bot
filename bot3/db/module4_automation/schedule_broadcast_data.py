"""定时播报数据类

使用dataclass封装定时播报相关的参数。
"""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ScheduledBroadcastParams:
    """定时播报参数

    封装创建或更新定时播报所需的所有参数。
    """

    conn: Any
    cursor: Any
    slot: int
    time: str
    chat_id: Optional[int]
    chat_title: Optional[str]
    message: str
    is_active: int = 1
