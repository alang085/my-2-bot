"""主入口自动化任务命令处理器注册模块

包含自动化任务相关命令处理器的注册逻辑。
"""

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from decorators import admin_required, error_handler, private_chat_only
from handlers.module4_automation.chat_event_handlers import (
    handle_new_chat_members, handle_new_chat_title)
from handlers.module4_automation.group_message_handlers import (
    get_group_id, list_group_message_configs, send_start_work_messages_command,
    setup_group_auto, test_group_message, test_weekday_message)
from handlers.module4_automation.text_input_handlers import handle_text_input


def register_automation_handlers(application: Application) -> None:
    """注册自动化任务相关命令处理器"""
    # 群组消息管理
    application.add_handler(CommandHandler("groupmsg_getid", get_group_id))
    application.add_handler(CommandHandler("groupmsg_setup", setup_group_auto))
    application.add_handler(CommandHandler("test_group_message", test_group_message))
    application.add_handler(
        CommandHandler("test_weekday_message", test_weekday_message)
    )
    application.add_handler(
        CommandHandler(
            "list_group_message_configs",
            admin_required(error_handler(list_group_message_configs)),
        )
    )
    application.add_handler(
        CommandHandler(
            "send_start_work_messages",
            private_chat_only(
                admin_required(error_handler(send_start_work_messages_command))
            ),
        )
    )

    # 通用文本处理器
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)
    )

    # 群组事件处理器
    application.add_handler(
        MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_new_chat_members)
    )
    application.add_handler(
        MessageHandler(filters.StatusUpdate.NEW_CHAT_TITLE, handle_new_chat_title)
    )
