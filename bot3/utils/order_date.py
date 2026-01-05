"""订单日期相关工具函数

包含订单日期的解析和更新功能。
"""

# 标准库
import logging
from datetime import date, datetime
from typing import Any, Dict, Optional

# 本地模块
import db_operations
from utils.chat_helpers import get_weekday_group_from_date

logger = logging.getLogger(__name__)


def _parse_current_order_date(date_str: str) -> Optional[date]:
    """解析当前订单日期字符串

    Args:
        date_str: 日期字符串，格式可能是 "YYYY-MM-DD HH:MM:SS" 或 "YYYY-MM-DD"

    Returns:
        解析后的日期对象，如果解析失败返回 None
    """
    if not date_str:
        return None

    try:
        # 提取日期部分（去掉时间部分）
        date_part = date_str.split()[0] if " " in date_str else date_str
        return datetime.strptime(date_part, "%Y-%m-%d").date()
    except ValueError:
        try:
            # 尝试其他日期格式
            return datetime.strptime(date_part, "%Y/%m/%d").date()
        except ValueError:
            logger.debug(f"无法解析订单日期: {date_str}")
            return None


def _format_order_date_string(new_order_date: date) -> str:
    """格式化订单日期字符串

    Args:
        new_order_date: 新的订单日期

    Returns:
        格式化的日期字符串
    """
    return f"{new_order_date.strftime('%Y-%m-%d')} 12:00:00"


async def _update_order_date_field(
    chat_id: int, new_date_str: str, order_id: str
) -> bool:
    """更新订单日期字段

    Args:
        chat_id: 聊天ID
        new_date_str: 新的日期字符串
        order_id: 订单ID（用于日志）

    Returns:
        是否成功更新
    """
    date_update_success = await db_operations.update_order_date(chat_id, new_date_str)
    if not date_update_success:
        logger.warning(f"更新订单日期失败: chat_id={chat_id}, new_date={new_date_str}")
        return False
    return True


async def _update_weekday_group_if_needed(
    chat_id: int, current_weekday_group: str, new_weekday_group: str, order_id: str
) -> bool:
    """如果需要，更新星期分组

    Args:
        chat_id: 聊天ID
        current_weekday_group: 当前星期分组
        new_weekday_group: 新的星期分组
        order_id: 订单ID（用于日志）

    Returns:
        是否成功更新
    """
    if current_weekday_group != new_weekday_group:
        logger.info(
            f"订单 {order_id} 星期分组需要更新: {current_weekday_group} -> {new_weekday_group}"
        )
        weekday_update_success = await db_operations.update_order_weekday_group(
            chat_id, new_weekday_group
        )
        if not weekday_update_success:
            logger.warning(
                f"更新订单星期分组失败: chat_id={chat_id}, "
                f"new_weekday_group={new_weekday_group}"
            )
            return False
    else:
        logger.debug(
            f"订单 {order_id} 星期分组已正确 ({current_weekday_group})，无需更新"
        )
    return True


async def _update_order_date_and_weekday(
    order: Dict[str, Any],
    chat_id: int,
    new_order_date: date,
    order_id: str,
) -> bool:
    """更新订单日期和星期分组

    Args:
        order: 订单字典
        chat_id: 聊天ID
        new_order_date: 新的订单日期
        order_id: 订单ID（用于日志）

    Returns:
        是否成功更新
    """
    try:
        new_weekday_group = get_weekday_group_from_date(new_order_date)
        current_weekday_group = order.get("weekday_group", "")

        logger.info(
            f"订单 {order_id} 群名更新: 新日期={new_order_date}, "
            f"当前星期分组={current_weekday_group}, 新星期分组={new_weekday_group}"
        )

        new_date_str = _format_order_date_string(new_order_date)

        if not await _update_order_date_field(chat_id, new_date_str, order_id):
            return False

        return await _update_weekday_group_if_needed(
            chat_id, current_weekday_group, new_weekday_group, order_id
        )

    except Exception as e:
        logger.error(f"更新订单日期和星期分组失败: {e}", exc_info=True)
        return False
