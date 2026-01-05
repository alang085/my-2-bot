"""操作详情格式化 - 用户模块

包含格式化用户相关操作的逻辑。
"""

from handlers.module5_data.daily_operations_handlers import \
    format_operation_type


def format_user_operations(op_type: str, op_data: dict, detail: str) -> str:
    """格式化用户相关操作

    Args:
        op_type: 操作类型
        op_data: 操作数据
        detail: 当前详情字符串

    Returns:
        str: 格式化后的详情字符串
    """
    if op_type == "attribution_created":
        group_id = op_data.get("group_id", "N/A")
        detail += f"\n   归属ID: {group_id}"
    elif op_type == "employee_added":
        employee_id = op_data.get("employee_id")
        detail += f"\n   员工ID: {employee_id}"
    elif op_type == "employee_removed":
        employee_id = op_data.get("employee_id")
        detail += f"\n   员工ID: {employee_id}"
    elif op_type == "user_permission_set":
        user_id = op_data.get("user_id")
        group_id = op_data.get("group_id", "N/A")
        detail += f"\n   用户ID: {user_id} | 归属ID: {group_id}"
    elif op_type == "user_permission_removed":
        user_id = op_data.get("user_id")
        detail += f"\n   用户ID: {user_id}"

    return detail
