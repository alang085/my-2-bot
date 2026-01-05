"""客户订单汇总 - 组装模块

包含组装订单汇总结果的逻辑。
"""

from typing import Dict, List


def assemble_order_summary(
    orders: List[Dict], income_map: Dict[str, Dict]
) -> List[Dict]:
    """组装订单汇总结果

    Args:
        orders: 订单列表
        income_map: 订单收入映射表

    Returns:
        List[Dict]: 汇总结果列表
    """
    result = []
    for order in orders:
        order_id = order["order_id"]
        income_data = income_map.get(
            order_id,
            {
                "interest": 0.0,
                "completed": 0.0,
                "breach_end": 0.0,
                "principal_reduction": 0.0,
                "total": 0.0,
            },
        )

        result.append(
            {
                "order": order,
                "interest": income_data["interest"],
                "completed": income_data["completed"],
                "breach_end": income_data["breach_end"],
                "principal_reduction": income_data["principal_reduction"],
                "total_contribution": income_data["total"],
            }
        )

    return result
