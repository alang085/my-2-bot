"""开始页面 - 消息构建模块

包含构建管理员命令消息的逻辑。
"""

from callbacks.main_callback_start_pages import get_financial_data_for_callback


async def build_admin_commands_message() -> str:
    """构建管理员命令消息

    Returns:
        str: 完整的命令消息
    """
    from callbacks.start_admin_message_admin import \
        build_admin_commands_section
    from callbacks.start_admin_message_employee import \
        build_employee_commands_message

    # 构建员工命令
    employee_commands = await build_employee_commands_message()

    # 构建管理员命令
    admin_commands = build_admin_commands_section()

    return employee_commands + admin_commands
