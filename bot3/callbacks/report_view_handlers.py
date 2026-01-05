"""报表回调 - 报表视图处理模块

包含处理报表视图相关回调的逻辑。
"""

from telegram import CallbackQuery
from telegram.ext import ContextTypes

# 这些函数在 report_callbacks_view.py 中定义
# 导入将在运行时动态处理


async def handle_report_view_callbacks(
    data: str,
    query: CallbackQuery,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    user_group_id: str | None,
) -> bool:
    """处理报表视图回调

    Args:
        data: 回调数据
        query: 回调查询对象
        context: 上下文对象
        user_id: 用户ID
        user_group_id: 用户归属ID

    Returns:
        bool: 是否已处理
    """
    from callbacks.report_callbacks_view import (handle_report_view_month,
                                                 handle_report_view_query,
                                                 handle_report_view_today)

    # 新格式: report_view_{type}_{group_id}
    if data.startswith("report_view_"):
        parts = data.split("_")
        if len(parts) < 4:
            return False
        view_type = parts[2]
        group_id = parts[3]
        group_id = None if group_id == "ALL" else group_id

        # 如果用户有权限限制，确保使用用户的归属ID
        if user_group_id:
            group_id = user_group_id

        if view_type == "today":
            await handle_report_view_today(
                query, context, group_id, user_id, user_group_id
            )
            return True
        elif view_type == "month":
            await handle_report_view_month(
                query, context, group_id, user_id, user_group_id
            )
            return True
        elif view_type == "query":
            await handle_report_view_query(query, context, group_id, user_group_id)
            return True

    # 兼容旧格式: report_{group_id}
    if data.startswith("report_") and not data.startswith("report_view_"):
        group_id = data[7:]
        group_id = None if group_id == "ALL" else group_id

        # 如果用户有权限限制，确保使用用户的归属ID
        if user_group_id:
            group_id = user_group_id

        await handle_report_view_today(query, context, group_id, user_id, user_group_id)
        return True

    return False
