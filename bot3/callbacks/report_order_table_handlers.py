"""报表回调 - 订单总表处理模块

包含处理订单总表相关回调的逻辑。
"""

from telegram import CallbackQuery
from telegram.ext import ContextTypes

# 这些函数在 report_callbacks_order_table.py 中定义
# 导入将在运行时动态处理


async def handle_order_table_callbacks(
    data: str, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, user_id: int
) -> bool:
    """处理订单总表回调

    Args:
        data: 回调数据
        query: 回调查询对象
        context: 上下文对象
        user_id: 用户ID

    Returns:
        bool: 是否已处理
    """
    from callbacks.report_callbacks_order_table import (
        handle_order_table_export_excel, handle_order_table_view)

    if data == "order_table_view":
        await handle_order_table_view(query, context, user_id)
        return True

    if data == "order_table_export_excel":
        await handle_order_table_export_excel(query, context, user_id)
        return True

    return False
