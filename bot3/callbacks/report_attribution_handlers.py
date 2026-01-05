"""报表回调 - 归属管理处理模块

包含处理归属管理相关回调的逻辑。
"""

from telegram import CallbackQuery, Update
from telegram.ext import ContextTypes

# 这些函数在相应的模块中定义
# 导入将在运行时动态处理


async def handle_attribution_callbacks(
    data: str, query: CallbackQuery, update: Update, context: ContextTypes.DEFAULT_TYPE
) -> bool:
    """处理归属管理相关回调

    Args:
        data: 回调数据
        query: 回调查询对象
        update: Telegram更新对象
        context: 上下文对象

    Returns:
        bool: 是否已处理
    """
    from callbacks.report_callbacks_attribution import (
        handle_broadcast_start, handle_change_attribution,
        handle_change_to_attribution, handle_menu_attribution,
        handle_search_orders)

    if data == "report_menu_attribution":
        await handle_menu_attribution(query)
        return True

    if data == "report_search_orders":
        await handle_search_orders(query, context)
        return True

    if data == "report_change_attribution":
        await handle_change_attribution(query, context)
        return True

    if data == "broadcast_start":
        await handle_broadcast_start(query, context)
        return True

    if data.startswith("report_change_to_"):
        new_group_id = data[17:]  # 提取新的归属ID
        await handle_change_to_attribution(query, update, context, new_group_id)
        return True

    return False
