"""查找尾数订单 - 数据获取模块

包含获取订单和统计数据的逻辑。
"""

from typing import Any, Dict, List, Tuple

import db_operations


async def fetch_orders_and_stats() -> Tuple[List[Dict[str, Any]], float, float]:
    """获取所有有效订单和统计数据

    Returns:
        Tuple[List[Dict], float, float]: (订单列表, 实际有效金额, 统计有效金额)
    """
    # 获取所有有效订单（包含所有状态，用于完整分析）
    all_valid_orders = await db_operations.search_orders_advanced_all_states({})

    # 计算实际有效金额（从订单表）
    actual_valid_amount = sum(order.get("amount", 0) for order in all_valid_orders)

    # 获取统计表中的有效金额
    financial_data = await db_operations.get_financial_data()
    stats_valid_amount = financial_data["valid_amount"]

    return all_valid_orders, actual_valid_amount, stats_valid_amount
