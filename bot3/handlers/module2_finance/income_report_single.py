"""收入报表生成 - 单类型模块

包含生成单类型报表的逻辑。
"""

from typing import List, Optional, Tuple

from handlers.module2_finance.income_handlers import (format_income_detail,
                                                      get_income_type_name)


def _prepare_single_type_report_header(
    income_type: str, records: List
) -> Tuple[str, float, int]:
    """准备单类型报表头部

    Args:
        income_type: 收入类型
        records: 记录列表

    Returns:
        (类型名称, 总金额, 记录数)
    """
    type_name = get_income_type_name(income_type)
    records.sort(key=lambda x: x.get("created_at", "") or "")
    type_total = sum(r.get("amount", 0) or 0 for r in records)
    type_count = len(records)
    return type_name, type_total, type_count


def _build_single_type_report_header(
    type_name: str, type_total: float, type_count: int
) -> str:
    """构建单类型报表头部文本

    Args:
        type_name: 类型名称
        type_total: 总金额
        type_count: 记录数

    Returns:
        报表头部文本
    """
    report = f"【{type_name}】总计: {type_total:,.2f} ({type_count}笔)\n"
    report += f"{'─' * 50}\n"
    report += f"{'时间':<8}  {'订单号':<25}  {'金额':>15}\n"
    report += f"{'─' * 50}\n"
    return report


async def _build_single_type_report_details(
    records: List, type_count: int, page: int, items_per_page: int
) -> Tuple[List, bool, int, str]:
    """构建单类型报表明细

    Args:
        records: 记录列表
        type_count: 记录数
        page: 页码
        items_per_page: 每页条数

    Returns:
        (显示记录, 是否有更多页, 总页数, 明细文本)
    """
    has_more_pages = False
    total_pages = 1
    details_text = ""

    if type_count > items_per_page:
        total_pages = (type_count + items_per_page - 1) // items_per_page
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        display_records = records[start_idx:end_idx]
        has_more_pages = end_idx < type_count

        display_range = f"{start_idx + 1}-{min(end_idx, type_count)}"
        details_text = (
            f"📄 第 {page}/{total_pages} 页 "
            f"(显示 {display_range}/{type_count} 条)\n"
        )
    else:
        display_records = records
        has_more_pages = False

    for i, record in enumerate(display_records, 1):
        detail = await format_income_detail(record)
        global_idx = (
            (page - 1) * items_per_page + i if type_count > items_per_page else i
        )
        details_text += f"{global_idx}. {detail}\n"

    return display_records, has_more_pages, total_pages, details_text


async def generate_single_type_report(
    records: List,
    income_type: str,
    start_date: str,
    end_date: str,
    page: int,
    items_per_page: int,
) -> Tuple[str, bool, int, str]:
    """生成单类型报表

    Args:
        records: 记录列表
        income_type: 收入类型
        start_date: 开始日期
        end_date: 结束日期
        page: 页码
        items_per_page: 每页条数

    Returns:
        Tuple: (报表文本, 是否有更多页, 总页数, 当前类型)
    """
    type_name, type_total, type_count = _prepare_single_type_report_header(
        income_type, records
    )
    report = _build_single_type_report_header(type_name, type_total, type_count)

    _, has_more_pages, total_pages, details_text = (
        await _build_single_type_report_details(
            records, type_count, page, items_per_page
        )
    )
    report += details_text + "\n"

    return report, has_more_pages, total_pages, income_type
