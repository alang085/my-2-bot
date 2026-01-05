"""Excel导出数据类

使用dataclass封装Excel导出相关的参数。
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ExcelFileParams:
    """Excel文件参数

    封装创建Excel文件所需的所有参数。
    """

    file_path: str
    orders: List[Dict]
    completed_orders: Optional[List[Dict]] = None
    breach_orders: Optional[List[Dict]] = None
    breach_end_orders: Optional[List[Dict]] = None
    daily_interest: float = 0
    daily_summary: Optional[Dict] = None
    all_orders_for_chat_id: Optional[List[Dict]] = None


@dataclass
class DailyChangesExcelParams:
    """每日变化Excel文件参数

    封装创建每日变化Excel文件所需的所有参数。
    """

    file_path: str
    date: str
    new_orders: List[Dict]
    completed_orders: List[Dict]
    breach_end_orders: List[Dict]
    income_records: List[Dict]
    expense_records: List[Dict]
    daily_summary: Dict
    monthly_data: Optional[Dict] = None
