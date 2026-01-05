"""订单归属变更 - 更新模块

包含更新订单归属的逻辑。
"""

import logging
from typing import Dict, List, Tuple

from db.module3_order.orders import update_order_group_id

logger = logging.getLogger(__name__)


async def _update_completed_order_attribution(
    chat_id: int, new_group_id: str, success_count: int, fail_count: int
) -> Tuple[int, int]:
    """更新已完成订单的归属ID（不迁移统计数据）

    Args:
        chat_id: 群组ID
        new_group_id: 新归属ID
        success_count: 成功计数
        fail_count: 失败计数

    Returns:
        (成功计数, 失败计数)
    """
    try:
        if await update_order_group_id(chat_id, new_group_id):
            return success_count + 1, fail_count
        return success_count, fail_count + 1
    except Exception as e:
        logger.error(f"更新订单归属出错: {e}", exc_info=True)
        return success_count, fail_count + 1


async def _update_active_order_attribution(
    order: Dict, new_group_id: str, success_count: int, fail_count: int
) -> Tuple[bool, int, int]:
    """更新活跃订单的归属ID

    Args:
        order: 订单字典
        new_group_id: 新归属ID
        success_count: 成功计数
        fail_count: 失败计数

    Returns:
        (是否成功, 成功计数, 失败计数)
    """
    chat_id = order["chat_id"]
    try:
        if await update_order_group_id(chat_id, new_group_id):
            return True, success_count + 1, fail_count
        logger.warning(
            f"更新订单归属失败: chat_id={chat_id}, new_group_id={new_group_id}"
        )
        return False, success_count, fail_count + 1
    except Exception as e:
        logger.error(f"更新订单归属出错: {e}", exc_info=True)
        return False, success_count, fail_count + 1


def _update_old_group_stats(
    old_group_stats: Dict, old_group_id: str, state: str, amount: float
) -> None:
    """更新旧归属统计数据

    Args:
        old_group_stats: 旧归属统计字典（会被修改）
        old_group_id: 旧归属ID
        state: 订单状态
        amount: 订单金额
    """
    if old_group_id not in old_group_stats:
        old_group_stats[old_group_id] = {
            "valid": {"count": 0, "amount": 0},
            "breach": {"count": 0, "amount": 0},
        }

    if state in ["normal", "overdue"]:
        old_group_stats[old_group_id]["valid"]["count"] += 1
        old_group_stats[old_group_id]["valid"]["amount"] += amount
    elif state == "breach":
        old_group_stats[old_group_id]["breach"]["count"] += 1
        old_group_stats[old_group_id]["breach"]["amount"] += amount


async def _process_single_order_attribution(
    order: Dict, new_group_id: str, counters: Dict, old_group_stats: Dict
) -> None:
    """处理单个订单的归属更新

    Args:
        order: 订单字典
        new_group_id: 新归属ID
        counters: 计数器字典（会被修改）
        old_group_stats: 旧归属统计字典（会被修改）
    """
    chat_id = order["chat_id"]
    old_group_id = order["group_id"]
    amount = order.get("amount", 0)
    state = order.get("state", "normal")

    if state in ["end", "breach_end"]:
        counters["success_count"], counters["fail_count"] = (
            await _update_completed_order_attribution(
                chat_id, new_group_id, counters["success_count"], counters["fail_count"]
            )
        )
        return

    update_success, counters["success_count"], counters["fail_count"] = (
        await _update_active_order_attribution(
            order, new_group_id, counters["success_count"], counters["fail_count"]
        )
    )

    if update_success:
        _update_old_group_stats(old_group_stats, old_group_id, state, amount)


async def update_order_attribution(
    orders: List[Dict], new_group_id: str
) -> Tuple[int, int, Dict]:
    """更新订单归属并统计迁移数据

    Args:
        orders: 订单列表
        new_group_id: 新的归属ID

    Returns:
        Tuple: (成功数量, 失败数量, 旧归属统计)
    """
    counters = {"success_count": 0, "fail_count": 0}
    old_group_stats = {}

    for order in orders:
        await _process_single_order_attribution(
            order, new_group_id, counters, old_group_stats
        )

    return counters["success_count"], counters["fail_count"], old_group_stats
