"""信用变更历史数据类

使用dataclass封装信用变更历史相关的参数。
"""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class CreditChangeParams:
    """信用变更参数

    封装记录信用变更历史所需的所有参数。
    """

    conn: Any
    cursor: Any
    customer_id: str
    change_type: str
    score_change: int
    score_before: int
    score_after: int
    order_id: Optional[str] = None
    reason: Optional[str] = None
