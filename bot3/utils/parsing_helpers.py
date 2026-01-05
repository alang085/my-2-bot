"""参数解析辅助模块

包含从context.args中解析参数的辅助函数。
"""

# 标准库
from datetime import datetime
from typing import Optional, Tuple, Union

from telegram.ext import ContextTypes

from constants import DATE_EXAMPLE, DATE_FORMAT, ERROR_MESSAGES

logger = __import__("logging").getLogger(__name__)


def parse_user_id_from_args(
    context: ContextTypes.DEFAULT_TYPE, arg_index: int = 0
) -> Tuple[Optional[int], Optional[str]]:
    """从context.args中解析用户ID

    Args:
        context: ContextTypes.DEFAULT_TYPE 对象
        arg_index: 参数索引，默认为0

    Returns:
        Tuple[user_id, error_message]:
            - user_id: 解析后的用户ID，如果解析失败则为None
            - error_message: 错误消息，如果没有错误则为None
    """
    if not context.args or len(context.args) <= arg_index:
        return None, "❌ 用法错误：缺少用户ID参数"

    try:
        user_id = int(context.args[arg_index])
        return user_id, None
    except ValueError:
        return None, "❌ 用户ID必须是数字"


def parse_date_from_args(
    context: ContextTypes.DEFAULT_TYPE, arg_index: int = 0, allow_range: bool = False
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """从context.args中解析日期

    Args:
        context: ContextTypes.DEFAULT_TYPE 对象
        arg_index: 参数索引，默认为0
        allow_range: 是否允许日期范围（两个日期）

    Returns:
        Tuple[start_date, end_date, error_message]:
            - start_date: 开始日期，如果解析失败则为None
            - end_date: 结束日期，如果allow_range=False则等于start_date，如果解析失败则为None
            - error_message: 错误消息，如果没有错误则为None
    """
    if not context.args or len(context.args) <= arg_index:
        return None, None, "❌ 用法错误：缺少日期参数"

    try:
        date_str = context.args[arg_index]
        datetime.strptime(date_str, "%Y-%m-%d")
        start_date = date_str

        if allow_range and len(context.args) > arg_index + 1:
            end_date_str = context.args[arg_index + 1]
            datetime.strptime(end_date_str, "%Y-%m-%d")
            end_date = end_date_str
        else:
            end_date = start_date

        return start_date, end_date, None
    except ValueError:
        return (
            None,
            None,
            f"{ERROR_MESSAGES['DATE_FORMAT_ERROR']}，请使用 {DATE_FORMAT} 格式\n例如: {DATE_EXAMPLE}",
        )


def validate_args_count(
    context: ContextTypes.DEFAULT_TYPE, min_count: int, usage_message: str
) -> Tuple[bool, Optional[str]]:
    """验证参数数量

    Args:
        context: ContextTypes.DEFAULT_TYPE 对象
        min_count: 最小参数数量
        usage_message: 用法说明消息

    Returns:
        Tuple[is_valid, error_message]:
            - is_valid: 参数数量是否有效
            - error_message: 错误消息，如果有效则为None
    """
    if not context.args or len(context.args) < min_count:
        return False, usage_message
    return True, None


def parse_date_string(
    date_str: str,
) -> Tuple[Union[str, Tuple[str, str]], Optional[str]]:
    """解析日期字符串（支持单个日期或日期范围）

    Args:
        date_str: 日期字符串，格式为 "YYYY-MM-DD" 或 "YYYY-MM-DD YYYY-MM-DD"

    Returns:
        Tuple[date_or_range, error_message]:
            - date_or_range: 单个日期字符串或日期范围元组
            - error_message: 错误消息，如果没有错误则为None
    """
    try:
        parts = date_str.strip().split()
        if len(parts) == 1:
            # 单个日期
            datetime.strptime(parts[0], "%Y-%m-%d")
            return parts[0], None
        elif len(parts) == 2:
            # 日期范围
            datetime.strptime(parts[0], "%Y-%m-%d")
            datetime.strptime(parts[1], "%Y-%m-%d")
            return (parts[0], parts[1]), None
        else:
            return (
                None,
                "❌ 日期格式错误，请使用 'YYYY-MM-DD' 或 'YYYY-MM-DD YYYY-MM-DD'",
            )
    except ValueError:
        return None, "❌ 日期格式错误，请使用 YYYY-MM-DD 格式"
