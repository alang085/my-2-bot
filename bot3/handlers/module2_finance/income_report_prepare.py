"""收入报表生成 - 准备模块

包含准备报表数据的逻辑。
"""

from typing import List, Optional


def prepare_income_records(
    records: List, income_type: Optional[str]
) -> tuple[List, dict, float]:
    """准备收入记录数据

    Args:
        records: 原始记录列表
        income_type: 收入类型

    Returns:
        Tuple: (过滤后的记录, 按类型分组的记录, 总金额)
    """
    from handlers.module2_finance.income_handlers import \
        group_income_records_by_type

    if not records:
        return [], {}, 0.0

    # 如果指定了类型，只显示该类型的记录
    if income_type:
        records = [r for r in records if r["type"] == income_type]

    # 按类型分组
    by_type = group_income_records_by_type(records)

    # 计算总计
    total_amount = sum(r.get("amount", 0) or 0 for r in records)

    return records, by_type, total_amount
