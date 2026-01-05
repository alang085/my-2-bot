"""收入记录数据类

使用dataclass封装收入记录相关的参数。
"""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class IncomeRecordParams:
    """收入记录参数

    封装收入记录所需的所有参数。
    """

    date: str
    type: str
    amount: float
    group_id: str
    order_id: Optional[str]
    order_date: Optional[str]
    customer: Optional[str]
    weekday_group: Optional[str]
    notes: Optional[str] = None


@dataclass
class IncomeInsertParams:
    """收入插入参数

    封装收入插入操作所需的所有参数（包含数据库连接）。
    """

    cursor: Any
    date: str
    type: str
    amount: float
    group_id: str
    order_id: Optional[str]
    order_date: Optional[str]
    customer: Optional[str]
    weekday_group: Optional[str]
    notes: Optional[str] = None


@dataclass
class IncomeRecordFullParams:
    """收入记录完整参数

    封装记录收入所需的所有参数（包含数据库连接和创建者）。
    """

    conn: Any
    cursor: Any
    date: str
    type: str
    amount: float
    group_id: Optional[str] = None
    order_id: Optional[str] = None
    order_date: Optional[str] = None
    customer: Optional[str] = None
    weekday_group: Optional[str] = None
    note: Optional[str] = None
    created_by: Optional[int] = None
