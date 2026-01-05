"""Excel导入字段提取模块

包含从Excel行中提取和转换字段的逻辑。
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# 状态映射（从中文状态到英文状态）
STATE_MAP = {
    "正常": "normal",
    "逾期": "overdue",
    "完成": "end",
    "违约完成": "breach_end",
    "正常订单": "normal",
    "逾期订单": "overdue",
    "已完成": "end",
    "违约已完成": "breach_end",
}


def extract_order_id(row_values: List[Any], col_indices: Dict[str, int]) -> str:
    """提取订单号

    Args:
        row_values: 行数据列表
        col_indices: 列索引字典

    Returns:
        str: 订单号，如果未找到返回空字符串
    """
    if "order_id" not in col_indices:
        return ""

    order_id_value = row_values[col_indices["order_id"]]

    if order_id_value is None:
        return ""

    # 如果是数字，转换为字符串，但保留完整格式
    if isinstance(order_id_value, (int, float)):
        # 如果是整数且小于1000000，可能是纯数字订单号
        if isinstance(order_id_value, int) and order_id_value < 1000000:
            return str(int(order_id_value))
        else:
            # 大数字可能是日期格式，转换为字符串并去除小数点
            return (
                str(int(order_id_value))
                if isinstance(order_id_value, float)
                else str(order_id_value)
            )
    else:
        return str(order_id_value).strip()


def extract_date(row_values: List[Any], col_indices: Dict[str, int]) -> str:
    """提取日期

    Args:
        row_values: 行数据列表
        col_indices: 列索引字典

    Returns:
        str: 日期字符串
    """
    if "date" not in col_indices:
        return ""

    date_value = row_values[col_indices["date"]]
    if not date_value:
        return ""

    if isinstance(date_value, datetime):
        return date_value.strftime("%Y-%m-%d %H:%M:%S")
    else:
        return str(date_value).strip()


def extract_customer(row_values: List[Any], col_indices: Dict[str, int]) -> str:
    """提取客户名称

    Args:
        row_values: 行数据列表
        col_indices: 列索引字典

    Returns:
        str: 客户名称
    """
    if "customer" not in col_indices:
        return ""
    return str(row_values[col_indices["customer"]] or "").strip()


def extract_group_id(row_values: List[Any], col_indices: Dict[str, int]) -> str:
    """提取归属ID

    Args:
        row_values: 行数据列表
        col_indices: 列索引字典

    Returns:
        str: 归属ID
    """
    if "group_id" not in col_indices:
        return ""
    return str(row_values[col_indices["group_id"]] or "").strip()


def extract_amount(row_values: List[Any], col_indices: Dict[str, int]) -> float:
    """提取订单金额

    Args:
        row_values: 行数据列表
        col_indices: 列索引字典

    Returns:
        float: 订单金额，如果解析失败返回0.0
    """
    if "amount" not in col_indices:
        return 0.0

    try:
        amount_value = row_values[col_indices["amount"]]
        if amount_value is not None:
            return float(amount_value)
    except (ValueError, TypeError):
        pass
    return 0.0


def extract_state(row_values: List[Any], col_indices: Dict[str, int]) -> str:
    """提取订单状态

    Args:
        row_values: 行数据列表
        col_indices: 列索引字典

    Returns:
        str: 订单状态，默认为"normal"
    """
    if "state" not in col_indices:
        return "normal"

    state_str = str(row_values[col_indices["state"]] or "").strip()
    return STATE_MAP.get(state_str, "normal")


def calculate_weekday_group(date_str: str) -> str:
    """从日期计算星期分组

    Args:
        date_str: 日期字符串

    Returns:
        str: 星期分组（一、二、三、四、五、六、日），默认返回"一"
    """
    if not date_str:
        return "一"

    try:
        if len(date_str) >= 10:
            date_part = date_str[:10]
            dt = datetime.strptime(date_part, "%Y-%m-%d")
            weekday = dt.weekday()  # 0=Monday, 6=Sunday
            weekday_map = {
                0: "一",
                1: "二",
                2: "三",
                3: "四",
                4: "五",
                5: "六",
                6: "日",
            }
            return weekday_map.get(weekday, "一")
    except Exception as e:
        logger.debug(f"解析星期分组失败（使用默认值）: {e}")

    return "一"


def normalize_excel_date(date_str: str) -> str:
    """规范化Excel日期字符串

    Args:
        date_str: 日期字符串

    Returns:
        str: 规范化后的日期字符串（格式：YYYY-MM-DD HH:MM:SS）
    """
    if not date_str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 如果只有日期部分，补充时间（默认12:00:00）
    if len(date_str) == 10:
        return f"{date_str} 12:00:00"
    elif len(date_str) < 19:
        return date_str[:10] + " 12:00:00"

    return date_str
