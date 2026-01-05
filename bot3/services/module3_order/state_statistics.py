"""订单状态变更 - 统计更新模块

包含更新统计数据的逻辑。
"""

import logging
from typing import Optional, Tuple

from services.module3_order.order_service import update_all_stats

logger = logging.getLogger(__name__)


async def update_statistics_for_state_change(
    new_state: str, amount: float, group_id: Optional[str]
) -> Tuple[bool, Optional[str]]:
    """更新状态变更的统计数据

    Args:
        new_state: 新状态
        amount: 金额
        group_id: 归属ID

    Returns:
        Tuple: (是否成功, 错误消息)
    """
    try:
        if new_state == "normal":
            # 从overdue转为normal：从overdue移回valid
            await update_all_stats("overdue", -amount, -1, group_id)
            await update_all_stats("valid", amount, 1, group_id)
        elif new_state == "overdue":
            # 从normal转为overdue：从valid移到overdue
            await update_all_stats("valid", -amount, -1, group_id)
            await update_all_stats("overdue", amount, 1, group_id)
        elif new_state == "breach":
            # 从normal/overdue转为breach：从valid移到breach
            await update_all_stats("valid", -amount, -1, group_id)
            await update_all_stats("breach", amount, 1, group_id)
    except Exception as e:
        logger.error(f"更新订单状态转换统计数据失败: {e}", exc_info=True)
        return False, str(e)

    return True, None
