"""收入高级查询分页 - 查询模块

包含查询收入记录的逻辑。
"""

from typing import List

from callbacks.report_callbacks_income import get_income_records_for_callback


async def query_income_records(
    start_date: str, end_date: str, final_type: str | None, final_group: str | None
) -> List[dict]:
    """查询收入记录

    Args:
        start_date: 开始日期
        end_date: 结束日期
        final_type: 类型
        final_group: 归属ID

    Returns:
        List[dict]: 收入记录列表
    """
    if final_group == "NULL_SPECIAL":
        all_records = await get_income_records_for_callback(
            start_date, end_date, income_type=final_type
        )
        records = [r for r in all_records if r.get("group_id") is None]
    else:
        records = await get_income_records_for_callback(
            start_date, end_date, income_type=final_type
        )

    return records


def build_income_title(
    start_date: str, end_date: str, final_type: str | None, final_group: str | None
) -> str:
    """构建标题

    Args:
        start_date: 开始日期
        end_date: 结束日期
        final_type: 类型
        final_group: 归属ID

    Returns:
        str: 标题
    """
    from constants import INCOME_TYPES

    type_name = INCOME_TYPES.get(final_type, "全部类型") if final_type else "全部类型"
    if final_group == "NULL_SPECIAL":
        group_name = "全局"
    elif final_group:
        group_name = final_group
    else:
        group_name = "全部"

    title = "收入明细查询"
    if start_date == end_date:
        title += f" ({start_date})"
    else:
        title += f" ({start_date} 至 {end_date})"
    title += f"\n类型: {type_name} | 归属ID: {group_name}"

    return title
