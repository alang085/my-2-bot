"""主入口用户管理命令处理器注册模块

包含用户权限管理相关命令处理器的注册逻辑。
"""

from telegram.ext import Application, CommandHandler

from decorators import admin_required, private_chat_only
from handlers.module1_user.attribution_handlers import (
    change_orders_attribution, create_attribution, list_attributions)
from handlers.module1_user.employee_handlers import (add_employee,
                                                     list_employees,
                                                     remove_employee)
from handlers.module1_user.user_mapping_handlers import (
    list_user_group_mappings, remove_user_group_id_handler,
    set_user_group_id_handler)


def register_user_handlers(application: Application) -> None:
    """注册用户管理相关命令处理器"""
    # 员工管理
    application.add_handler(
        CommandHandler("add_employee", private_chat_only(admin_required(add_employee)))
    )
    application.add_handler(
        CommandHandler(
            "remove_employee", private_chat_only(admin_required(remove_employee))
        )
    )
    application.add_handler(
        CommandHandler(
            "list_employees", private_chat_only(admin_required(list_employees))
        )
    )

    # 归属ID管理
    application.add_handler(
        CommandHandler(
            "create_attribution", private_chat_only(admin_required(create_attribution))
        )
    )
    application.add_handler(
        CommandHandler(
            "list_attributions", private_chat_only(admin_required(list_attributions))
        )
    )

    # 用户归属ID映射管理
    application.add_handler(
        CommandHandler(
            "set_user_group_id",
            private_chat_only(admin_required(set_user_group_id_handler)),
        )
    )
    application.add_handler(
        CommandHandler(
            "remove_user_group_id",
            private_chat_only(admin_required(remove_user_group_id_handler)),
        )
    )
    application.add_handler(
        CommandHandler(
            "list_user_group_mappings",
            private_chat_only(admin_required(list_user_group_mappings)),
        )
    )
