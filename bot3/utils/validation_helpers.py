"""输入验证工具函数

提供统一的输入验证工具，确保所有用户输入都经过严格验证
"""

import re
from datetime import datetime
from typing import Optional, Tuple

from constants import (AMOUNT_TOLERANCE, DATE_FORMAT, MAX_ACCOUNT_NAME_LENGTH,
                       MAX_NOTE_LENGTH, ORDER_STATES)


def validate_integer(
    value: str, min_value: Optional[int] = None, max_value: Optional[int] = None
) -> Tuple[bool, Optional[int], Optional[str]]:
    """验证整数输入

    Args:
        value: 输入字符串
        min_value: 最小值（可选）
        max_value: 最大值（可选）

    Returns:
        Tuple[is_valid, parsed_value, error_message]:
            - is_valid: 是否有效
            - parsed_value: 解析后的整数值，如果无效则为None
            - error_message: 错误消息，如果有效则为None
    """
    try:
        int_value = int(value.strip())
        if min_value is not None and int_value < min_value:
            return False, None, f"数值必须大于等于 {min_value}"
        if max_value is not None and int_value > max_value:
            return False, None, f"数值必须小于等于 {max_value}"
        return True, int_value, None
    except ValueError:
        return False, None, "请输入有效的整数"


def validate_float(
    value: str, min_value: Optional[float] = None, max_value: Optional[float] = None
) -> Tuple[bool, Optional[float], Optional[str]]:
    """验证浮点数输入

    Args:
        value: 输入字符串
        min_value: 最小值（可选）
        max_value: 最大值（可选）

    Returns:
        Tuple[is_valid, parsed_value, error_message]:
            - is_valid: 是否有效
            - parsed_value: 解析后的浮点数值，如果无效则为None
            - error_message: 错误消息，如果有效则为None
    """
    try:
        float_value = float(value.strip())
        if min_value is not None and float_value < min_value:
            return False, None, f"数值必须大于等于 {min_value}"
        if max_value is not None and float_value > max_value:
            return False, None, f"数值必须小于等于 {max_value}"
        return True, float_value, None
    except ValueError:
        return False, None, "请输入有效的数字"


def validate_amount(
    value: str, min_amount: float = 0.01, max_amount: float = 999999999.99
) -> Tuple[bool, Optional[float], Optional[str]]:
    """验证金额输入

    Args:
        value: 输入字符串
        min_amount: 最小金额（默认0.01）
        max_amount: 最大金额（默认999999999.99）

    Returns:
        Tuple[is_valid, parsed_value, error_message]:
            - is_valid: 是否有效
            - parsed_value: 解析后的金额值，如果无效则为None
            - error_message: 错误消息，如果有效则为None
    """
    is_valid, amount, error = validate_float(value, min_amount, max_amount)
    if not is_valid:
        if error and "必须大于等于" in error:
            return False, None, f"金额必须大于等于 {min_amount}"
        if error and "必须小于等于" in error:
            return False, None, f"金额不能超过 {max_amount:,.2f}"
        return False, None, "请输入有效的金额"
    return True, amount, None


def validate_date(
    value: str, date_format: str = DATE_FORMAT
) -> Tuple[bool, Optional[str], Optional[str]]:
    """验证日期格式

    Args:
        value: 输入字符串
        date_format: 日期格式（默认 DATE_FORMAT）

    Returns:
        Tuple[is_valid, parsed_date, error_message]:
            - is_valid: 是否有效
            - parsed_date: 格式化后的日期字符串，如果无效则为None
            - error_message: 错误消息，如果有效则为None
    """
    try:
        date_obj = datetime.strptime(value.strip(), date_format)
        return True, date_obj.strftime(date_format), None
    except ValueError:
        return (
            False,
            None,
            f"日期格式错误，请使用格式：{date_format}（例如：{datetime.now().strftime(date_format)}）",
        )


def validate_order_id(value: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """验证订单ID格式

    订单ID格式：4位数字，如 "0001", "0123"

    Args:
        value: 输入字符串

    Returns:
        Tuple[is_valid, parsed_order_id, error_message]:
            - is_valid: 是否有效
            - parsed_order_id: 格式化后的订单ID，如果无效则为None
            - error_message: 错误消息，如果有效则为None
    """
    value = value.strip()
    if not value:
        return False, None, "订单ID不能为空"

    # 检查是否为4位数字
    if not re.match(r"^\d{4}$", value):
        return False, None, "订单ID必须是4位数字（例如：0001, 0123）"

    return True, value, None


def validate_group_id(value: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """验证归属ID格式

    归属ID格式：1个字母 + 2位数字，如 "S01", "A12"

    Args:
        value: 输入字符串

    Returns:
        Tuple[is_valid, parsed_group_id, error_message]:
            - is_valid: 是否有效
            - parsed_group_id: 格式化后的归属ID（大写），如果无效则为None
            - error_message: 错误消息，如果有效则为None
    """
    value = value.strip().upper()
    if not value:
        return False, None, "归属ID不能为空"

    # 检查格式：1个字母 + 2位数字
    if not re.match(r"^[A-Z]\d{2}$", value):
        return False, None, "归属ID格式错误，应为1个字母+2位数字（例如：S01, A12）"

    return True, value, None


def validate_customer_type(value: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """验证客户类型

    客户类型：A（新客户）或 B（老客户）

    Args:
        value: 输入字符串

    Returns:
        Tuple[is_valid, parsed_customer_type, error_message]:
            - is_valid: 是否有效
            - parsed_customer_type: 格式化后的客户类型（大写），如果无效则为None
            - error_message: 错误消息，如果有效则为None
    """
    value = value.strip().upper()
    if value in ["A", "B"]:
        return True, value, None
    return False, None, "客户类型必须是 A（新客户）或 B（老客户）"


def validate_order_state(value: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """验证订单状态

    Args:
        value: 输入字符串

    Returns:
        Tuple[is_valid, parsed_state, error_message]:
            - is_valid: 是否有效
            - parsed_state: 解析后的状态值，如果无效则为None
            - error_message: 错误消息，如果有效则为None
    """
    value = value.strip().lower()
    if value in ORDER_STATES:
        return True, value, None

    valid_states = ", ".join(ORDER_STATES.keys())
    return False, None, f"订单状态无效，有效状态：{valid_states}"


def validate_text_length(
    value: str, max_length: int, field_name: str = "文本"
) -> Tuple[bool, Optional[str], Optional[str]]:
    """验证文本长度

    Args:
        value: 输入字符串
        max_length: 最大长度
        field_name: 字段名称（用于错误消息）

    Returns:
        Tuple[is_valid, parsed_text, error_message]:
            - is_valid: 是否有效
            - parsed_text: 修剪后的文本，如果无效则为None
            - error_message: 错误消息，如果有效则为None
    """
    value = value.strip()
    if len(value) > max_length:
        return False, None, f"{field_name}长度不能超过 {max_length} 个字符"
    return True, value, None


def validate_time_format(value: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """验证时间格式

    支持格式：HH 或 HH:MM（24小时制）

    Args:
        value: 输入字符串

    Returns:
        Tuple[is_valid, parsed_time, error_message]:
            - is_valid: 是否有效
            - parsed_time: 格式化后的时间字符串（HH:MM），如果无效则为None
            - error_message: 错误消息，如果有效则为None
    """
    from utils.time_validation_helpers import (_validate_hour_minute_format,
                                               _validate_hour_only_format)

    value = value.strip()

    # 格式1：只有小时（HH）
    result = _validate_hour_only_format(value)
    if result is not None:
        return result

    # 格式2：小时:分钟（HH:MM）
    result = _validate_hour_minute_format(value)
    if result is not None:
        return result

    return False, None, "时间格式错误，请输入小时（0-23）或小时:分钟（如 22:30）"


def validate_chat_id(value: str) -> Tuple[bool, Optional[int], Optional[str]]:
    """验证聊天ID（Telegram群组/频道ID）

    Args:
        value: 输入字符串

    Returns:
        Tuple[is_valid, parsed_chat_id, error_message]:
            - is_valid: 是否有效
            - parsed_chat_id: 解析后的聊天ID，如果无效则为None
            - error_message: 错误消息，如果有效则为None
    """
    is_valid, chat_id, error = validate_integer(value)
    if not is_valid:
        return False, None, "聊天ID必须是有效的数字"

    # Telegram 群组ID通常是负数，频道ID可能是负数或正数
    # 这里只检查是否为有效整数，不做正负限制
    return True, chat_id, None


def validate_account_name(value: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """验证账户名称

    Args:
        value: 输入字符串

    Returns:
        Tuple[is_valid, parsed_name, error_message]:
            - is_valid: 是否有效
            - parsed_name: 修剪后的账户名称，如果无效则为None
            - error_message: 错误消息，如果有效则为None
    """
    value = value.strip()
    if not value:
        return False, None, "账户名称不能为空"

    return validate_text_length(value, MAX_ACCOUNT_NAME_LENGTH, "账户名称")


def validate_note(value: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """验证备注

    Args:
        value: 输入字符串

    Returns:
        Tuple[is_valid, parsed_note, error_message]:
            - is_valid: 是否有效
            - parsed_note: 修剪后的备注，如果无效则为None
            - error_message: 错误消息，如果有效则为None
    """
    return validate_text_length(value, MAX_NOTE_LENGTH, "备注")
