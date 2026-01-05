"""收入查询数据类

使用dataclass封装收入查询相关的参数。
"""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class IncomeQueryParams:
    """收入查询参数

    封装查询收入记录所需的所有参数。
    """

    conn: Any
    cursor: Any
    start_date: str
    end_date: Optional[str] = None
    type: Optional[str] = None
    customer: Optional[str] = None
    group_id: Optional[str] = None
    order_id: Optional[str] = None
    include_undone: bool = False
