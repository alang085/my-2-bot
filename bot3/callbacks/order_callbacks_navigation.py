"""订单操作回调处理器 - 导航模块

包含返回等导航相关的回调处理逻辑。
"""

from telegram import Update
from telegram.ext import ContextTypes

from handlers.module3_order.basic_handlers import show_current_order
from utils.chat_helpers import is_group_chat


async def handle_order_action_back(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """处理返回按钮"""
    is_group = is_group_chat(update)
    # 在群聊中，返回时不刷新显示，只关闭当前选择界面
    if is_group:
        await query.delete_message()
    else:
        await show_current_order(update, context)
    await query.answer()
