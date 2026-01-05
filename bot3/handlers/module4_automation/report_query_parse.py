"""报表查询 - 解析模块

包含解析查询参数和权限的逻辑。
"""

from datetime import datetime
from typing import Optional, Tuple

import db_operations


async def _resolve_user_group_id(
    user_id: Optional[int], context_group_id: Optional[str]
) -> Optional[str]:
    """解析用户归属ID

    Args:
        user_id: 用户ID
        context_group_id: 上下文中的归属ID

    Returns:
        归属ID
    """
    if user_id:
        user_group_id = await db_operations.get_user_group_id(user_id)
        if user_group_id:
            return user_group_id
    return context_group_id


def _parse_date_strings(
    text: str,
) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
    """解析日期字符串

    Args:
        text: 输入文本

    Returns:
        (是否成功, 错误消息, 开始日期, 结束日期)
    """
    dates = text.split()
    if len(dates) == 1:
        return True, None, dates[0], dates[0]
    elif len(dates) == 2:
        return True, None, dates[0], dates[1]
    else:
        return (
            False,
            "❌ Format Error. Use 'YYYY-MM-DD' or 'YYYY-MM-DD YYYY-MM-DD'",
            None,
            None,
        )


def _validate_date_formats(start_date: str, end_date: str) -> bool:
    """验证日期格式

    Args:
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        是否有效
    """
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
        return True
    except ValueError:
        return False


async def _determine_show_expenses(user_id: Optional[int]) -> bool:
    """确定是否显示开销

    Args:
        user_id: 用户ID

    Returns:
        是否显示开销
    """
    if user_id:
        user_group_id = await db_operations.get_user_group_id(user_id)
        if user_group_id:
            return False
    return True


async def parse_report_query_params(
    update, context, text: str
) -> Tuple[bool, Optional[str], Optional[str], Optional[str], bool]:
    """解析报表查询参数

    Args:
        update: Telegram更新对象
        context: 上下文对象
        text: 输入文本

    Returns:
        Tuple: (是否成功, 错误消息, 开始日期, 结束日期, 是否显示开销)
    """
    user_id = update.effective_user.id if update.effective_user else None
    group_id = context.user_data.get("report_group_id")
    group_id = await _resolve_user_group_id(user_id, group_id)

    is_valid, error_msg, start_date, end_date = _parse_date_strings(text)
    if not is_valid:
        return False, error_msg, None, None, False

    if not _validate_date_formats(start_date, end_date):
        return False, "❌ Invalid Date Format. Use YYYY-MM-DD", None, None, False

    show_expenses = await _determine_show_expenses(user_id)
    return True, None, start_date, end_date, show_expenses
