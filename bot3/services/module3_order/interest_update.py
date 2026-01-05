"""利息处理 - 更新模块

包含更新统计数据的逻辑。
"""

import logging
from typing import Any, Dict, Optional, Tuple

from utils.stats_helpers import update_all_stats, update_liquid_capital

logger = logging.getLogger(__name__)


async def update_interest_statistics(
    amount_validated: float, group_id: str, order_model: Any
) -> Tuple[bool, Optional[str]]:
    """更新利息收入统计数据

    Args:
        amount_validated: 验证后的金额
        group_id: 归属ID
        order_model: 订单模型

    Returns:
        Tuple: (是否成功, 错误消息)
    """
    try:
        # 利息收入统计
        await update_all_stats("interest", amount_validated, 0, group_id)
        # 流动资金增加
        await update_liquid_capital(amount_validated)
        return True, None
    except Exception as e:
        logger.error(f"更新利息收入统计数据失败: {e}", exc_info=True)
        # 统计数据更新失败，但收入明细已记录
        # 记录错误信息，提示用户使用修复命令
        error_info = {
            "operation": "interest",
            "order_id": order_model.order_id,
            "amount": amount_validated,
            "error": str(e),
        }
        logger.error(f"数据不一致风险: {error_info}")

        return (
            False,
            (
                f"❌ Statistics update failed, but income record saved. "
                f"Use /fix_statistics to repair. Error: {str(e)}"
            ),
        )
