"""报表回调 - 收入明细处理模块

包含处理收入明细查询相关回调的逻辑。
"""

from telegram import CallbackQuery
from telegram.ext import ContextTypes

# 这些函数在 report_callbacks_income.py 中定义
# 导入将在运行时动态处理


async def handle_income_callbacks(
    data: str, query: CallbackQuery, user_id: int, context: ContextTypes.DEFAULT_TYPE
) -> bool:
    """处理收入明细查询回调

    Args:
        data: 回调数据
        query: 回调查询对象
        user_id: 用户ID
        context: 上下文对象

    Returns:
        bool: 是否已处理
    """
    from callbacks.report_callbacks_income import (
        handle_income_adv_page, handle_income_advanced_query,
        handle_income_page, handle_income_query_group,
        handle_income_query_step_date, handle_income_query_step_type,
        handle_income_query_type, handle_income_type,
        handle_income_view_by_type, handle_income_view_month,
        handle_income_view_query, handle_income_view_today)

    if data == "income_view_today":
        await handle_income_view_today(query, user_id, context)
        return True

    if data == "income_view_month":
        await handle_income_view_month(query, user_id, context)
        return True

    if data == "income_view_query":
        await handle_income_view_query(query, user_id, context)
        return True

    if data == "income_view_by_type":
        await handle_income_view_by_type(query, user_id, context)
        return True

    if data == "income_advanced_query":
        await handle_income_advanced_query(query, user_id, context)
        return True

    if data == "income_query_step_date":
        await handle_income_query_step_date(query, user_id, context)
        return True

    if data.startswith("income_query_step_type_"):
        await handle_income_query_step_type(query, user_id, context, data)
        return True

    if data.startswith("income_query_type_"):
        await handle_income_query_type(query, user_id, context, data)
        return True

    if data.startswith("income_query_group_"):
        await handle_income_query_group(query, user_id, context, data)
        return True

    if data.startswith("income_adv_page_"):
        await handle_income_adv_page(query, user_id, context, data)
        return True

    if data.startswith("income_type_"):
        await handle_income_type(query, user_id, context, data)
        return True

    if data.startswith("income_page_"):
        await handle_income_page(query, user_id, context, data)
        return True

    return False
