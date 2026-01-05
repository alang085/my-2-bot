"""星期分组更新 - 更新模块

包含更新订单星期分组的逻辑。
"""

import logging
from typing import Dict, Tuple

import db_operations
from utils.weekday_helpers import get_weekday_group_from_date

logger = logging.getLogger(__name__)


async def update_order_weekday_group_if_needed(
    order: Dict, order_date, correct_weekday_group: str
) -> Tuple[bool, bool, bool]:
    """更新订单星期分组（如果需要）

    Args:
        order: 订单字典
        order_date: 订单日期
        correct_weekday_group: 正确的星期分组

    Returns:
        Tuple: (是否更新成功, 是否验证失败, 是否更新失败)
    """
    order_id = order["order_id"]
    chat_id = order["chat_id"]
    current_weekday_group = order.get("weekday_group", "")

    # 比较当前值和计算值，只在值不同时才更新
    if current_weekday_group == correct_weekday_group:
        return False, False, False  # 无需更新

    # 更新
    success = await db_operations.update_order_weekday_group(
        chat_id, correct_weekday_group
    )

    if success:
        # 验证更新是否成功
        updated_order = await db_operations.get_order_by_chat_id(chat_id)
        if (
            updated_order
            and updated_order.get("weekday_group") == correct_weekday_group
        ):
            logger.debug(
                f"订单 {order_id} 星期分组已更新: "
                f"{current_weekday_group} -> {correct_weekday_group}"
            )
            return True, False, False  # 更新成功
        else:
            logger.warning(
                f"订单 {order_id} 更新后验证失败: 期望 {correct_weekday_group}, "
                f"实际 {updated_order.get('weekday_group') if updated_order else 'None'}"
            )
            return False, True, False  # 验证失败
    else:
        logger.warning(f"订单 {order_id} 更新失败: chat_id={chat_id}")
        return False, False, True  # 更新失败
