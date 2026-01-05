"""主入口回调处理器注册模块

包含回调处理器的注册逻辑。
"""

from telegram.ext import Application, CallbackQueryHandler

from callbacks import (button_callback, handle_order_action_callback,
                       handle_schedule_callback)
from callbacks.group_message_callbacks import handle_group_message_callback


def register_callback_handlers(application: Application) -> None:
    """注册回调处理器"""
    application.add_handler(CallbackQueryHandler(handle_order_action_callback))
    application.add_handler(CallbackQueryHandler(handle_schedule_callback))
    application.add_handler(CallbackQueryHandler(handle_group_message_callback))
    application.add_handler(CallbackQueryHandler(button_callback))
