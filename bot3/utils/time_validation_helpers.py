"""时间验证辅助函数

包含时间格式验证的辅助函数，提取复杂逻辑。
"""

import re
from typing import Optional, Tuple


def _validate_hour_only_format(value: str) -> Optional[Tuple[bool, str, Optional[str]]]:
    """验证只有小时的格式（HH）

    Args:
        value: 输入字符串

    Returns:
        Tuple[is_valid, parsed_time, error_message] 或 None（如果不匹配格式）
    """
    if not re.match(r"^\d{1,2}$", value):
        return None

    try:
        hour = int(value)
        if 0 <= hour <= 23:
            return True, f"{hour:02d}:00", None
        return False, None, "小时必须在 0-23 之间"
    except ValueError:
        return None


def _validate_hour_minute_format(
    value: str,
) -> Optional[Tuple[bool, str, Optional[str]]]:
    """验证小时:分钟格式（HH:MM）

    Args:
        value: 输入字符串

    Returns:
        Tuple[is_valid, parsed_time, error_message] 或 None（如果不匹配格式）
    """
    if not re.match(r"^\d{1,2}:\d{2}$", value):
        return None

    try:
        parts = value.split(":")
        hour = int(parts[0])
        minute = int(parts[1])
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return True, f"{hour:02d}:{minute:02d}", None
        if hour < 0 or hour > 23:
            return False, None, "小时必须在 0-23 之间"
        if minute < 0 or minute > 59:
            return False, None, "分钟必须在 0-59 之间"
    except (ValueError, IndexError):
        pass

    return None
