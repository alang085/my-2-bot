"""主入口基础命令处理器注册模块

包含基础命令处理器的注册逻辑。
"""

from telegram.ext import Application, CommandHandler

from decorators import authorized_required, error_handler, private_chat_only
from handlers.module2_finance.payment_handlers import (show_all_accounts,
                                                       show_gcash,
                                                       show_paymaya)
from handlers.module4_automation.schedule_handlers import show_schedule_menu
from handlers.module4_automation.search_handlers import search_orders
from handlers.module5_data.order_table_handlers import show_order_table
from handlers.module5_data.report_handlers import show_my_report, show_report
from handlers.command_handlers_basic import show_valid_amount
from handlers.command_handlers_basic import start


def register_basic_handlers(application: Application) -> None:
    """注册基础命令处理器"""
    # 基础命令
    application.add_handler(
        CommandHandler(
            "start", private_chat_only(authorized_required(error_handler(start)))
        )
    )
    application.add_handler(
        CommandHandler(
            "report", private_chat_only(authorized_required(error_handler(show_report)))
        )
    )
    application.add_handler(
        CommandHandler("myreport", private_chat_only(error_handler(show_my_report)))
    )
    application.add_handler(
        CommandHandler(
            "valid_amount",
            private_chat_only(authorized_required(error_handler(show_valid_amount))),
        )
    )
    application.add_handler(
        CommandHandler(
            "search",
            private_chat_only(authorized_required(error_handler(search_orders))),
        )
    )
    application.add_handler(
        CommandHandler(
            "accounts",
            private_chat_only(authorized_required(error_handler(show_all_accounts))),
        )
    )
    application.add_handler(
        CommandHandler(
            "gcash", private_chat_only(authorized_required(error_handler(show_gcash)))
        )
    )
    application.add_handler(
        CommandHandler(
            "paymaya",
            private_chat_only(authorized_required(error_handler(show_paymaya))),
        )
    )
    application.add_handler(
        CommandHandler(
            "schedule",
            private_chat_only(authorized_required(error_handler(show_schedule_menu))),
        )
    )

    # 订单总表
    application.add_handler(CommandHandler("ordertable", show_order_table))
