"""播报相关工具函数"""

from datetime import date, datetime, timedelta
from typing import Optional, Tuple

import pytz


def _parse_order_date(order_date: Optional[date], today: date) -> Tuple[date, int]:
    """解析订单日期并获取目标星期几

    Args:
        order_date: 订单日期（可选）
        today: 当前日期

    Returns:
        (订单日期, 目标星期几)
    """
    if order_date:
        if isinstance(order_date, str):
            try:
                if " " in order_date:
                    order_date = datetime.strptime(
                        order_date.split()[0], "%Y-%m-%d"
                    ).date()
                else:
                    order_date = datetime.strptime(order_date, "%Y-%m-%d").date()
            except ValueError:
                order_date = today
        target_weekday = order_date.weekday()
    else:
        target_weekday = today.weekday()
        order_date = today

    return order_date, target_weekday


def _calculate_days_until_target(today: date, target_weekday: int) -> int:
    """计算从今天到下个目标星期几的天数

    Args:
        today: 当前日期
        target_weekday: 目标星期几（0=Monday, 1=Tuesday, ..., 6=Sunday）

    Returns:
        天数
    """
    days_until_target = (target_weekday - today.weekday()) % 7
    if days_until_target == 0:
        days_until_target = 7
    return days_until_target


def _format_payment_date(next_payment_date: date) -> Tuple[datetime, str, str]:
    """格式化付款日期

    Args:
        next_payment_date: 下个付款日期

    Returns:
        (datetime对象, 日期字符串, 星期字符串)
    """
    next_payment_datetime = datetime.combine(next_payment_date, datetime.min.time())
    date_str = next_payment_date.strftime("%B %d,%Y")
    weekday_str = next_payment_date.strftime("%A")
    return next_payment_datetime, date_str, weekday_str


def calculate_next_payment_date(
    order_date: Optional[date] = None,
) -> Tuple[datetime, str, str]:
    """
    计算下一个付款日期（从当前日期找到下一个与订单日期相同星期几的日期）

    Args:
        order_date: 订单日期（可选，如果为None则使用当前日期）

    返回: (日期对象, 日期字符串, 星期字符串)

    逻辑：
    - 订单的付款日期是固定的星期几（由订单日期决定）
    - 从当前日期开始，找到下一个与订单日期相同星期几的日期
    - 如果当前日期就是订单的付款星期几，那么下个付款日期是7天后

    示例：
    - 订单日期：2025-07-22 (周二)
    - 当前日期：2025-11-29 (周五)
    - 下个付款日期：2025-12-03 (下一个周二)

    - 订单日期：2025-11-25 (周二)
    - 当前日期：2025-11-29 (周五)
    - 下个付款日期：2025-12-02 (下一个周二)
    """
    tz = pytz.timezone("Asia/Shanghai")
    today = datetime.now(tz).date()

    _, target_weekday = _parse_order_date(order_date, today)
    days_until_target = _calculate_days_until_target(today, target_weekday)
    next_payment_date = today + timedelta(days=days_until_target)

    return _format_payment_date(next_payment_date)


def format_broadcast_message(
    principal: float,
    principal_12: float,
    outstanding_interest: float = 0,
    date_str: Optional[str] = None,
    weekday_str: Optional[str] = None,
) -> str:
    """
    生成播报消息模板

    Args:
        principal: 本金金额
        principal_12: 本金12%金额
        outstanding_interest: 未付利息（默认0）
        date_str: 日期字符串（如果为None，自动计算）
        weekday_str: 星期字符串（如果为None，自动计算）

    Returns:
        格式化后的播报消息
    """
    # 如果没有提供日期，自动计算
    if date_str is None or weekday_str is None:
        _, date_str, weekday_str = calculate_next_payment_date()

    # 格式化金额（添加千位分隔符）
    principal_formatted = f"{principal:,.0f}"
    principal_12_formatted = f"{principal_12:,.0f}"

    # 构建播报消息
    message = (
        f"Your next payment is due on {date_str} ({weekday_str}) "
        f"for {principal_formatted} or {principal_12_formatted} "
        f"to defer the principal payment for one week.\n\n"
        f"Your outstanding interest is {outstanding_interest}"
    )

    return message
