"""收入统计 - 组装模块

包含组装统计结果的逻辑。
"""

from typing import Callable, Dict, List


def assemble_customer_contribution(
    income_rows: List, order_row, calculate_income_statistics: Callable
) -> Dict:
    """组装客户贡献统计结果

    Args:
        income_rows: 收入行数据
        order_row: 订单统计行数据
        calculate_income_statistics: 计算收入统计的函数

    Returns:
        Dict: 统计结果
    """
    # 初始化结果
    result = {
        "total_interest": 0.0,
        "total_completed": 0.0,
        "total_breach_end": 0.0,
        "total_principal_reduction": 0.0,
        "total_amount": 0.0,
        "interest_count": 0,
        "order_count": 0,
        "first_order_date": None,
        "last_order_date": None,
    }

    # 处理收入数据（使用统一函数）
    income_records = [
        {"type": row[0], "count": row[1], "amount": row[2] or 0.0}
        for row in income_rows
    ]
    income_stats = calculate_income_statistics(income_records)
    result.update(income_stats)

    # 处理订单统计
    if order_row:
        result["order_count"] = order_row[0] or 0
        result["first_order_date"] = order_row[1]
        result["last_order_date"] = order_row[2]

    return result
