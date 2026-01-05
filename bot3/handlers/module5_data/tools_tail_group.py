"""查找尾数订单 - 分组分析模块

包含按归属ID分组分析的逻辑。
"""

from typing import Any, Dict, List

import db_operations


async def analyze_by_group_id(
    all_valid_orders: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """按归属ID分组分析

    Args:
        all_valid_orders: 所有有效订单列表

    Returns:
        Dict: 分组分析结果字典
    """
    group_analysis = {}
    all_group_ids = list(
        set(
            order.get("group_id") for order in all_valid_orders if order.get("group_id")
        )
    )

    for group_id in sorted(all_group_ids):
        group_orders = [o for o in all_valid_orders if o.get("group_id") == group_id]
        group_amount = sum(o.get("amount", 0) for o in group_orders)
        group_tail = int(group_amount % 1000)
        group_non_thousand = [o for o in group_orders if o.get("amount", 0) % 1000 != 0]

        grouped_data = await db_operations.get_grouped_data(group_id)
        stats_group_amount = grouped_data.get("valid_amount", 0)
        stats_group_tail = int(stats_group_amount % 1000)

        group_analysis[group_id] = {
            "orders": group_orders,
            "actual_amount": group_amount,
            "actual_tail": group_tail,
            "stats_amount": stats_group_amount,
            "stats_tail": stats_group_tail,
            "non_thousand": group_non_thousand,
        }

    return group_analysis
