"""报表回调 - 开销处理模块

包含处理开销相关回调的逻辑。
"""

from telegram import CallbackQuery
from telegram.ext import ContextTypes

# 这些函数在 report_callbacks_expense.py 中定义
# 导入将在运行时动态处理


async def handle_expense_callbacks(
    data: str, query: CallbackQuery, user_id: int, context: ContextTypes.DEFAULT_TYPE
) -> bool:
    """处理开销相关回调

    Args:
        data: 回调数据
        query: 回调查询对象
        user_id: 用户ID
        context: 上下文对象

    Returns:
        bool: 是否已处理
    """
    from callbacks.report_callbacks_expense import (
        handle_expense_company_add, handle_expense_company_month,
        handle_expense_company_query, handle_expense_company_today,
        handle_expense_other_add, handle_expense_other_month,
        handle_expense_other_query, handle_expense_other_today)

    # 公司开销
    if data == "report_record_company":
        await handle_expense_company_today(query, user_id, context)
        return True

    if data == "report_expense_month_company":
        await handle_expense_company_month(query, context)
        return True

    if data == "report_expense_query_company":
        await handle_expense_company_query(query, context)
        return True

    if data == "report_add_expense_company":
        await handle_expense_company_add(query, user_id, context)
        return True

    # 其他开销
    if data == "report_record_other":
        await handle_expense_other_today(query, user_id, context)
        return True

    if data == "report_expense_month_other":
        await handle_expense_other_month(query, context)
        return True

    if data == "report_expense_query_other":
        await handle_expense_other_query(query, context)
        return True

    if data == "report_add_expense_other":
        await handle_expense_other_add(query, user_id, context)
        return True

    return False
