"""订单状态更新辅助函数 - 日期更新模块

包含订单日期和星期分组更新的逻辑。
"""

import logging
from typing import Any, Dict, Optional

import db_operations
from utils.chat_helpers import get_weekday_group_from_date
from utils.order_parsing import parse_order_from_title

logger = logging.getLogger(__name__)


async def update_order_date_if_needed(
    order: Dict[str, Any], title: str, order_id: str
) -> None:
    """更新订单日期和星期分组（如果需要）

    Args:
        order: 订单字典
        title: 群名
        order_id: 订单ID
    """
    # 解析群名，检查日期和星期分组是否需要更新
    parsed_info = parse_order_from_title(title)
    if not parsed_info:
        return

    new_order_date = parsed_info.get("date")
    if not new_order_date:
        return

    chat_id = order.get("chat_id")
    current_date_str = order.get("date", "")
    current_order_date = _parse_current_order_date(current_date_str)

    # 判断是否需要更新日期
    should_update_date = _should_update_date(
        current_order_date, new_order_date, order_id
    )

    if should_update_date:
        await _update_order_date_and_weekday(order, chat_id, new_order_date, order_id)
    else:
        # 日期没有变化，但检查星期分组是否正确
        await _fix_weekday_group_if_needed(order, new_order_date, chat_id, order_id)


def _parse_current_order_date(current_date_str: str) -> Optional[str]:
    """解析当前订单日期字符串

    Args:
        current_date_str: 日期字符串

    Returns:
        Optional[str]: 解析后的日期，如果无法解析则返回None
    """
    if not current_date_str:
        return None

    # 尝试解析日期字符串（格式：YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS）
    try:
        from datetime import datetime

        # 尝试解析完整格式
        if " " in current_date_str:
            dt = datetime.strptime(current_date_str, "%Y-%m-%d %H:%M:%S")
        else:
            dt = datetime.strptime(current_date_str, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except (ValueError, AttributeError):
        return None


def _should_update_date(
    current_order_date: Optional[str], new_order_date: str, order_id: str
) -> bool:
    """判断是否需要更新日期

    Args:
        current_order_date: 当前订单日期
        new_order_date: 新订单日期
        order_id: 订单ID

    Returns:
        bool: 是否需要更新
    """
    if current_order_date:
        if new_order_date != current_order_date:
            logger.info(
                f"订单 {order_id} 群名日期变化: {current_order_date} -> {new_order_date}"
            )
            return True
        return False
    else:
        # 当前日期无法解析，使用群名中的日期修复
        logger.info(
            f"订单 {order_id} 数据库日期无效，使用群名中的日期: {new_order_date}"
        )
        return True


async def _update_order_date_and_weekday(
    order: Dict[str, Any], chat_id: int, new_order_date: str, order_id: str
) -> None:
    """更新订单日期和星期分组

    Args:
        order: 订单字典
        chat_id: 聊天ID
        new_order_date: 新订单日期（字符串格式：YYYY-MM-DD）
        order_id: 订单ID
    """
    from datetime import datetime

    from utils.order_date import _update_order_date_and_weekday as update_func

    # 将字符串日期转换为 date 对象
    new_date_obj = datetime.strptime(new_order_date, "%Y-%m-%d").date()
    success = await update_func(order, chat_id, new_date_obj, order_id)

    if success:
        # 更新订单字典中的日期和星期分组
        new_date_str = f"{new_order_date} 12:00:00"
        new_weekday_group = get_weekday_group_from_date(new_order_date)
        order["date"] = new_date_str
        order["weekday_group"] = new_weekday_group
        logger.info(
            f"订单 {order_id} 日期和星期分组已更新: "
            f"date={new_date_str}, weekday_group={new_weekday_group}"
        )
    else:
        logger.warning(
            f"订单 {order_id} 日期和星期分组更新失败: chat_id={chat_id}, "
            f"new_order_date={new_order_date}"
        )


async def _fix_weekday_group_if_needed(
    order: Dict[str, Any], new_order_date: str, chat_id: int, order_id: str
) -> None:
    """修复星期分组（如果需要）

    Args:
        order: 订单字典
        new_order_date: 新订单日期
        chat_id: 聊天ID
        order_id: 订单ID
    """
    current_weekday_group = order.get("weekday_group", "")
    correct_weekday_group = get_weekday_group_from_date(new_order_date)

    if current_weekday_group != correct_weekday_group:
        logger.info(
            f"订单 {order_id} 星期分组不正确: "
            f"{current_weekday_group} -> {correct_weekday_group}"
        )
        weekday_update_success = await db_operations.update_order_weekday_group(
            chat_id, correct_weekday_group
        )
        if weekday_update_success:
            order["weekday_group"] = correct_weekday_group
            logger.info(
                f"订单 {order_id} 星期分组已修正: "
                f"{current_weekday_group} -> {correct_weekday_group}"
            )
        else:
            logger.warning(
                f"订单 {order_id} 星期分组更新失败: chat_id={chat_id}, "
                f"correct_weekday_group={correct_weekday_group}"
            )
