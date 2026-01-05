"""收入格式化辅助函数

包含格式化收入明细的辅助函数，提取复杂逻辑。
"""

import logging

from utils.date_helpers import datetime_str_to_beijing_str

logger = logging.getLogger(__name__)


def _extract_time_from_record(record: dict) -> str:
    """从记录中提取时间字符串

    Args:
        record: 收入记录字典

    Returns:
        时间字符串（格式：HH:MM:SS），如果无法提取则返回"无时间"
    """
    time_str = "无时间"
    if not record.get("created_at"):
        return time_str

    try:
        beijing_time_str = datetime_str_to_beijing_str(record["created_at"])
        if beijing_time_str and beijing_time_str != record["created_at"]:
            # 提取时间部分（HH:MM:SS）
            if len(beijing_time_str) >= 19:
                time_str = beijing_time_str[11:19]
            else:
                time_str = "无时间"
        elif beijing_time_str:
            # 如果解析失败但返回了原字符串，尝试提取时间部分
            if " " in beijing_time_str and len(beijing_time_str.split(" ")) > 1:
                time_part = beijing_time_str.split(" ")[1]
                if len(time_part) >= 8:
                    time_str = time_part[:8]
    except Exception as e:
        logger.warning(f"解析时间失败: {record.get('created_at')}, 错误: {e}")

    return time_str


def _format_amount_from_record(record: dict) -> str:
    """从记录中格式化金额字符串

    Args:
        record: 收入记录字典

    Returns:
        格式化后的金额字符串
    """
    amount = record.get("amount")
    if amount is None:
        return "NULL"

    try:
        return f"{float(amount):,.2f}"
    except (ValueError, TypeError):
        return "错误"


def format_income_detail_line(time_str: str, order_id: str, amount_str: str) -> str:
    """格式化收入明细行

    Args:
        time_str: 时间字符串
        order_id: 订单号
        amount_str: 金额字符串

    Returns:
        格式化后的明细行
    """
    # 格式：时间  订单号  金额（对齐显示，不使用分隔符）
    # 时间：8字符（HH:MM:SS），订单号：25字符，金额：15字符
    # 使用空格对齐，让竖列对齐
    return f"{time_str:<8}  {order_id:<25}  {amount_str:>15}"
