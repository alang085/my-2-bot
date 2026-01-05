"""收入报表生成 - 全部类型模块

包含生成全部类型报表的逻辑。
"""

from typing import List, Optional, Tuple

from handlers.module2_finance.income_handlers import (format_income_detail,
                                                      get_income_type_name,
                                                      get_income_type_order)


async def generate_all_types_report(
    by_type: dict, type_order: List[str]
) -> Tuple[str, Optional[str]]:
    """生成全部类型报表

    Args:
        by_type: 按类型分组的记录
        type_order: 类型顺序

    Returns:
        Tuple: (报表文本, 当前类型)
    """
    report = ""
    current_type = None

    # 显示所有类型
    for type_key in type_order:
        if type_key not in by_type:
            continue

        type_name = get_income_type_name(type_key)
        type_records = by_type[type_key]

        # 按录入时间正序排序
        type_records.sort(key=lambda x: x.get("created_at", "") or "")

        type_total = sum(r.get("amount", 0) or 0 for r in type_records)
        type_count = len(type_records)

        report += f"【{type_name}】总计: {type_total:,.2f} ({type_count}笔)\n"
        report += f"{'─' * 50}\n"
        report += f"{'时间':<8}  {'订单号':<25}  {'金额':>15}\n"
        report += f"{'─' * 50}\n"

        # 显示所有记录
        for i, record in enumerate(type_records, 1):
            detail = await format_income_detail(record)
            report += f"{i}. {detail}\n"

        report += "\n"

        # 如果当前类型记录最多，设置为当前类型
        if not current_type or type_count > len(by_type.get(current_type, [])):
            current_type = type_key

    return report, current_type
