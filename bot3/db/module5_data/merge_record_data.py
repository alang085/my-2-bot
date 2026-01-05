"""合并记录数据类

使用dataclass封装合并记录相关的参数。
"""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class MergeRecordParams:
    """合并记录参数

    封装保存合并记录所需的所有参数。
    """

    conn: Any
    cursor: Any
    merge_date: str
    baseline_date: str
    orders_count: int
    total_amount: float
    total_interest: float
    total_expenses: float
    merged_by: Optional[int] = None
