"""日期解析辅助函数

包含解析订单日期的辅助函数，提取复杂逻辑。
"""

from datetime import date, datetime
from typing import Optional


def _parse_date_from_string(date_str: str) -> Optional[date]:
    """从日期字符串解析日期

    Args:
        date_str: 日期字符串（可能包含时间部分）

    Returns:
        解析的日期，如果无法解析则返回None
    """
    if not date_str:
        return None

    try:
        # 如果包含空格，只取日期部分
        clean_date_str = date_str.split()[0] if " " in date_str else date_str
        return datetime.strptime(clean_date_str, "%Y-%m-%d").date()
    except Exception:
        return None


def _parse_date_from_order_id(order_id: str) -> Optional[date]:
    """从订单ID解析日期

    Args:
        order_id: 订单ID

    Returns:
        解析的日期，如果无法解析则返回None
    """
    if not order_id:
        return None

    try:
        if order_id.startswith("A"):
            # A类型订单：A + 6位日期（YYMMDD）
            if len(order_id) >= 7 and order_id[1:7].isdigit():
                date_part = order_id[1:7]
                full_date_str = f"20{date_part}"
                return datetime.strptime(full_date_str, "%Y%m%d").date()
        else:
            # 其他类型订单：6位日期（YYMMDD）
            if len(order_id) >= 6 and order_id[:6].isdigit():
                date_part = order_id[:6]
                full_date_str = f"20{date_part}"
                return datetime.strptime(full_date_str, "%Y%m%d").date()
    except Exception:
        pass

    return None


def parse_order_date_from_fields(order_date_str: str, order_id: str) -> Optional[date]:
    """从订单日期字符串或订单ID解析日期

    Args:
        order_date_str: 订单日期字符串
        order_id: 订单ID

    Returns:
        解析的日期，如果无法解析则返回None
    """
    # 优先使用数据库中的date字段
    date_from_db = _parse_date_from_string(order_date_str)
    if date_from_db:
        return date_from_db

    # 如果date字段无效，尝试从订单ID解析
    return _parse_date_from_order_id(order_id)
