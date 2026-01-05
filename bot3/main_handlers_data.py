"""主入口数据管理命令处理器注册模块

包含数据管理相关命令处理器的注册逻辑。
"""

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from decorators import admin_required, error_handler, private_chat_only
from handlers.module5_data.admin_correction_handlers import admin_correct
from handlers.module5_data.daily_changes_handlers import \
    show_daily_changes_table
from handlers.module5_data.daily_operations_handlers import (
    show_daily_operations, show_daily_operations_summary)
from handlers.module5_data.diagnostic_handlers import (
    check_mismatch, diagnose_data_inconsistency)
from handlers.module5_data.import_handlers import (import_orders_command,
                                                   import_orders_from_excel)
from handlers.module5_data.restore_handlers import restore_daily_data
from handlers.module5_data.weekday_handlers import (check_weekday_groups,
                                                    update_weekday_groups)
from handlers.module5_data.undo_handlers import undo_last_operation


def register_data_handlers(application: Application) -> None:
    """注册数据管理相关命令处理器"""
    # 订单导入
    application.add_handler(CommandHandler("import_orders", import_orders_command))
    application.add_handler(
        MessageHandler(
            filters.Document.FileExtension("xlsx")
            | filters.Document.FileExtension("xls"),
            import_orders_from_excel,
        )
    )

    # 每日数据变更表
    application.add_handler(CommandHandler("daily_changes", show_daily_changes_table))

    # 每日操作记录
    application.add_handler(CommandHandler("daily_operations", show_daily_operations))
    application.add_handler(
        CommandHandler("daily_operations_summary", show_daily_operations_summary)
    )
    application.add_handler(CommandHandler("restore_daily_data", restore_daily_data))

    # 撤销操作命令
    from decorators import authorized_required

    application.add_handler(
        CommandHandler("undo", authorized_required(error_handler(undo_last_operation)))
    )

    # 数据同步命令
    application.add_handler(
        CommandHandler(
            "check_weekday_groups",
            private_chat_only(admin_required(check_weekday_groups)),
        )
    )
    application.add_handler(
        CommandHandler(
            "update_weekday_groups",
            private_chat_only(admin_required(update_weekday_groups)),
        )
    )

    # 数据诊断命令
    application.add_handler(
        CommandHandler(
            "check_mismatch",
            private_chat_only(admin_required(error_handler(check_mismatch))),
        )
    )
    application.add_handler(
        CommandHandler(
            "diagnose_data",
            private_chat_only(
                admin_required(error_handler(diagnose_data_inconsistency))
            ),
        )
    )

    # 管理员修正命令
    application.add_handler(
        CommandHandler(
            "admin_correct",
            private_chat_only(admin_required(error_handler(admin_correct))),
        )
    )
