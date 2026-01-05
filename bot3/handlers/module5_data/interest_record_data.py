"""利息记录处理数据类

使用dataclass封装利息记录处理相关的参数。
"""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class InterestRecordParams:
    """利息记录参数

    封装处理利息收入记录所需的所有参数。
    """

    record: Dict[str, Any]
    amount: float
    date: str
    group_id: str
    income_summary: Dict[str, Any]
    daily_income: Dict[str, Dict[str, Dict[str, Any]]]
    global_income: Dict[str, Any]
