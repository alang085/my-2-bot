"""收入明细分页 - 准备模块

包含准备查询参数和标题的逻辑。
"""

from db.module2_finance.income import get_income_records_for_callback
from handlers.income_handlers import INCOME_TYPES


async def prepare_query_params(
    income_type: str, start_date: str, end_date: str
) -> tuple[list, str, str]:
    """准备查询参数

    Args:
        income_type: 收入类型
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        tuple: (记录列表, 类型名称, 标题)
    """
    # 处理 income_type
    query_type = (
        None
        if (income_type == "None" or income_type == "" or income_type is None)
        else income_type
    )

    # 获取记录
    records = await get_income_records_for_callback(
        start_date, end_date, income_type=query_type
    )

    type_name = INCOME_TYPES.get(query_type, query_type) if query_type else "全部"

    # 生成标题
    if start_date == end_date:
        title = f"今日{type_name}收入 ({start_date})"
    else:
        title = f"{type_name}收入 ({start_date} 至 {end_date})"

    return records, type_name, title
