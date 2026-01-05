"""文本输入处理 - 路由模块

包含路由不同状态文本输入的逻辑。
"""

from telegram import Update
from telegram.ext import ContextTypes


async def route_text_input_by_state(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_state: str, text: str
) -> bool:
    """根据状态路由文本输入

    Args:
        update: Telegram更新对象
        context: 上下文对象
        user_state: 用户状态
        text: 输入文本

    Returns:
        bool: 是否已处理
    """
    # 按功能分组路由
    from handlers.module4_automation.text_input_routers import (
        route_config_states, route_finance_states, route_group_message_states,
        route_payment_states, route_schedule_states, route_search_states)

    if await route_group_message_states(update, context, user_state, text):
        return True

    if await route_finance_states(update, context, user_state, text):
        return True

    if await route_search_states(update, context, user_state, text):
        return True

    if await route_payment_states(update, context, user_state, text):
        return True

    if await route_schedule_states(update, context, user_state):
        return True

    if await route_config_states(update, context, user_state, text):
        return True

    return False
