"""主入口财务管理命令处理器注册模块

包含财务管理相关命令处理器的注册逻辑。
"""

from telegram.ext import Application, CommandHandler

from decorators import admin_required, error_handler, private_chat_only
from handlers.module2_finance.adjustment_handlers import adjust_funds
from handlers.module2_finance.payment_handlers import balance_history


def register_finance_handlers(application: Application) -> None:
    """注册财务管理相关命令处理器"""
    # 资金管理
    application.add_handler(
        CommandHandler(
            "adjust", private_chat_only(admin_required(error_handler(adjust_funds)))
        )
    )

    # 余额历史查询
    application.add_handler(CommandHandler("balance_history", balance_history))
