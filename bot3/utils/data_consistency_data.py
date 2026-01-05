"""数据一致性检查数据类

使用dataclass封装数据一致性检查相关的参数。
"""

from dataclasses import dataclass
from typing import List


@dataclass
class DataConsistencyParams:
    """数据一致性参数

    封装检查数据一致性所需的所有参数。
    """

    field_name: str
    stats_value: float
    income_value: float
    mismatches: List[str]
    output_lines: List[str]
    tolerance: float = 0.01
    stats_label: str = "统计表"
    income_label: str = "明细表"
