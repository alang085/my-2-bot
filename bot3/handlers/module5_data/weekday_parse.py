"""星期分组更新 - 日期解析模块

包含解析订单日期的逻辑。
"""

from datetime import date, datetime
from typing import Optional


def parse_order_date(order_date_str: str, order_id: str) -> Optional[date]:
    """解析订单日期

    Args:
        order_date_str: 订单日期字符串
        order_id: 订单ID

    Returns:
        Optional[date]: 解析的日期，如果无法解析则返回None
    """
    from handlers.module5_data.date_parse_helpers import \
        parse_order_date_from_fields

    return parse_order_date_from_fields(order_date_str, order_id)
