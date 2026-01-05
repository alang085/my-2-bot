"""违约订单完成 - 统计更新模块

包含更新统计数据的逻辑。
"""

import logging
from typing import Optional, Tuple

from services.module3_order.order_service import (update_all_stats,
                                                  update_liquid_capital)

logger = logging.getLogger(__name__)


async def update_breach_end_statistics(
    amount: float, group_id: Optional[str]
) -> Tuple[bool, Optional[str]]:
    """更新违约完成统计数据

    Args:
        amount: 金额
        group_id: 归属ID

    Returns:
        Tuple: (是否成功, 错误消息)
    """
    try:
        await update_all_stats("breach_end", amount, 1, group_id)
        await update_liquid_capital(amount)
        return True, None
    except Exception as e:
        logger.error(f"更新违约完成统计数据失败: {e}", exc_info=True)
        return False, str(e)
