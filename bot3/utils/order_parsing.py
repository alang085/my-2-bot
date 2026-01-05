"""订单解析工具函数

包含从群名解析订单信息的函数。
"""

# 标准库
import re
from datetime import date, datetime
from typing import Dict, Optional, Union


def get_state_from_title(title: str) -> str:
    """从群名识别订单状态"""
    # 注意：需要先检查组合符号，再检查单个符号
    if "❌⭕️" in title:
        return "breach_end"
    elif "⭕️" in title:
        return "end"
    elif "❌" in title:
        return "breach"
    elif "❗️" in title:
        return "overdue"
    else:
        return "normal"


def _match_a_prefix_format(title: str) -> Optional[Dict[str, str]]:
    """匹配A前缀格式（A + 10或11位数字）

    Args:
        title: 群名

    Returns:
        如果匹配成功，返回包含 raw_digits, order_id, customer, is_11_digits 的字典
        否则返回 None
    """
    # 优先匹配11位数字
    match_11 = re.match(r"^A(\d{11})", title)
    if match_11:
        # 确保不是12位数字的前11位
        if len(title) > 12 and title[12].isdigit():
            match_11 = None
        else:
            raw_digits = match_11.group(1)
            return {
                "raw_digits": raw_digits,
                "order_id": "A" + raw_digits,
                "customer": "A",
                "is_11_digits": True,
            }

    # 匹配10位数字
    if not match_11:
        match_10 = re.match(r"^A(\d{10})", title)
        if match_10:
            # 确保不是11位数字的前10位
            if len(title) > 11 and title[11].isdigit():
                match_10 = None
            else:
                raw_digits = match_10.group(1)
                return {
                    "raw_digits": raw_digits,
                    "order_id": "A" + raw_digits,
                    "customer": "A",
                    "is_11_digits": False,
                }

    return None


def _match_traditional_format(title: str) -> Optional[Dict[str, str]]:
    """匹配传统格式（10或11位数字开头，可选A后缀）

    Args:
        title: 群名

    Returns:
        如果匹配成功，返回包含 raw_digits, order_id, customer, is_11_digits 的字典
        否则返回 None
    """
    # 优先匹配11位数字
    match_11 = re.match(r"^(\d{11})(A)?", title)
    if match_11:
        # 确保不是12位数字的前11位
        if len(title) > 11 and title[11].isdigit():
            match_11 = None
        else:
            raw_digits = match_11.group(1)
            has_a_suffix = match_11.group(2) == "A"
            return {
                "raw_digits": raw_digits,
                "order_id": raw_digits + "A" if has_a_suffix else raw_digits,
                "customer": "A" if has_a_suffix else "B",
                "is_11_digits": True,
            }

    # 匹配10位数字
    if not match_11:
        match_10 = re.match(r"^(\d{10})(A)?", title)
        if match_10:
            # 确保不是11位数字的前10位
            if len(title) > 10 and title[10].isdigit():
                match_10 = None
            else:
                raw_digits = match_10.group(1)
                has_a_suffix = match_10.group(2) == "A"
                return {
                    "raw_digits": raw_digits,
                    "order_id": raw_digits + "A" if has_a_suffix else raw_digits,
                    "customer": "A" if has_a_suffix else "B",
                    "is_11_digits": False,
                }

    return None


def _parse_date_from_digits(raw_digits: str) -> Optional[date]:
    """从数字字符串解析日期（前6位: YYMMDD）

    Args:
        raw_digits: 数字字符串（10或11位）

    Returns:
        解析后的日期对象，如果解析失败返回 None
    """
    date_part = raw_digits[:6]
    try:
        # 假设 20YY
        full_date_str = f"20{date_part}"
        return datetime.strptime(full_date_str, "%Y%m%d").date()
    except ValueError:
        return None


def _parse_amount_from_digits(raw_digits: str, is_11_digits: bool) -> float:
    """从数字字符串解析金额

    Args:
        raw_digits: 数字字符串（10或11位）
        is_11_digits: 是否为11位数字

    Returns:
        解析后的金额
    """
    if is_11_digits:
        # 11位数字: YYMMDDNNKKH
        # KK = 第9-10位 (千位)
        # H = 第11位 (百位)
        amount_thousands = int(raw_digits[8:10])
        amount_hundreds = int(raw_digits[10])
        return amount_thousands * 1000 + amount_hundreds * 100
    else:
        # 10位数字: YYMMDDNNKK
        # KK = 第9-10位 (千位)
        amount_part = raw_digits[8:10]
        return int(amount_part) * 1000


def parse_order_from_title(title: str) -> Optional[Dict[str, Union[str, date, float]]]:
    """从群名解析订单信息

    规则:
    1. 群名必须以10个或11个连续数字开始，或者以A开头后跟10或11个数字
    2. 10个数字格式: YYMMDDNNKK (YYMMDD=日期, NN=序号, KK=金额千位)
    3. 11个数字格式: YYMMDDNNKKH (YYMMDD=日期, NN=序号, KK=金额千位, H=金额百位)
    4. 最后带A表示新客户，否则为老客户
    5. 支持A开头的格式: A2310220105 (保持A前缀格式，order_id为A2310220105)
    6. 也支持A后缀格式: 2310220105A (保持A后缀格式，order_id为2310220105A)

    Args:
        title: 群名

    Returns:
        包含 date, amount, order_id, customer, full_date_str 的字典，如果解析失败返回 None
    """
    # 首先尝试匹配A前缀格式
    match_result = _match_a_prefix_format(title)
    if not match_result:
        # 尝试匹配传统格式
        match_result = _match_traditional_format(title)

    if not match_result:
        return None

    raw_digits = match_result["raw_digits"]
    order_id = match_result["order_id"]
    customer = match_result["customer"]
    is_11_digits = match_result["is_11_digits"]

    # 解析日期
    order_date_obj = _parse_date_from_digits(raw_digits)
    if not order_date_obj:
        return None

    # 解析金额
    amount = _parse_amount_from_digits(raw_digits, is_11_digits)

    # 构建完整日期字符串
    full_date_str = f"20{raw_digits[:6]}"

    return {
        "date": order_date_obj,
        "amount": amount,
        "order_id": order_id,
        "customer": customer,
        "full_date_str": full_date_str,
    }
