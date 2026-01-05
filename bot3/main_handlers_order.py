"""主入口订单命令处理器注册模块

包含订单相关命令处理器的注册逻辑。
"""

from telegram.ext import Application, CommandHandler

from decorators import authorized_required, error_handler, group_chat_only
from handlers.module3_order.amount_handlers import handle_amount_operation
from handlers.module3_order.basic_handlers import (create_order,
                                                   show_current_order)
from handlers.module3_order.state_handlers import (set_breach, set_breach_end,
                                                   set_end, set_normal,
                                                   set_overdue)
from handlers.module4_automation.broadcast_handlers import broadcast_payment


def register_order_handlers(application: Application) -> None:
    """注册订单相关命令处理器"""
    # 订单操作命令
    application.add_handler(
        CommandHandler(
            "create", error_handler(authorized_required(group_chat_only(create_order)))
        )
    )
    application.add_handler(
        CommandHandler("normal", authorized_required(group_chat_only(set_normal)))
    )
    application.add_handler(
        CommandHandler("overdue", authorized_required(group_chat_only(set_overdue)))
    )
    application.add_handler(
        CommandHandler("end", authorized_required(group_chat_only(set_end)))
    )
    application.add_handler(
        CommandHandler("breach", authorized_required(group_chat_only(set_breach)))
    )
    application.add_handler(
        CommandHandler(
            "breach_end", authorized_required(group_chat_only(set_breach_end))
        )
    )
    application.add_handler(
        CommandHandler(
            "order", authorized_required(group_chat_only(show_current_order))
        )
    )
    application.add_handler(
        CommandHandler(
            "broadcast", authorized_required(group_chat_only(broadcast_payment))
        )
    )

    # 消息处理器（金额操作）
    from telegram.ext import MessageHandler, filters

    application.add_handler(
        MessageHandler(
            filters.TEXT & filters.Regex(r"^\+[\d.]+[bB]?$"),
            error_handler(
                authorized_required(group_chat_only(handle_amount_operation))
            ),
        )
    )
