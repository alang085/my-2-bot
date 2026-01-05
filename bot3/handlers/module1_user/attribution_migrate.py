"""订单归属变更 - 数据迁移模块

包含迁移统计数据的逻辑。
"""

import logging
from typing import Dict

from services.module3_order.order_service import update_all_stats

logger = logging.getLogger(__name__)


async def migrate_statistics(old_group_stats: Dict, new_group_id: str) -> Dict:
    """迁移统计数据

    Args:
        old_group_stats: 旧归属统计
        new_group_id: 新的归属ID

    Returns:
        Dict: 汇总统计
    """
    # 从旧归属减少
    for old_group_id, stats in old_group_stats.items():
        # 减少有效订单
        if stats["valid"]["count"] > 0:
            await update_all_stats(
                "valid",
                -stats["valid"]["amount"],
                -stats["valid"]["count"],
                old_group_id,
            )

        # 减少违约订单
        if stats["breach"]["count"] > 0:
            await update_all_stats(
                "breach",
                -stats["breach"]["amount"],
                -stats["breach"]["count"],
                old_group_id,
            )

    # 汇总所有需要迁移的数据
    total_valid_count = sum(s["valid"]["count"] for s in old_group_stats.values())
    total_valid_amount = sum(s["valid"]["amount"] for s in old_group_stats.values())
    total_breach_count = sum(s["breach"]["count"] for s in old_group_stats.values())
    total_breach_amount = sum(s["breach"]["amount"] for s in old_group_stats.values())

    # 到新归属增加
    if total_valid_count > 0:
        await update_all_stats(
            "valid", total_valid_amount, total_valid_count, new_group_id
        )

    if total_breach_count > 0:
        await update_all_stats(
            "breach", total_breach_amount, total_breach_count, new_group_id
        )

    return {
        "valid_count": total_valid_count,
        "valid_amount": total_valid_amount,
        "breach_count": total_breach_count,
        "breach_amount": total_breach_amount,
    }
