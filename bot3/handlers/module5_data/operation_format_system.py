"""操作详情格式化 - 系统模块

包含格式化系统相关操作的逻辑。
"""

from handlers.module5_data.daily_operations_handlers import \
    format_operation_type


def format_system_operations(op_type: str, op_data: dict, detail: str) -> str:
    """格式化系统相关操作

    Args:
        op_type: 操作类型
        op_data: 操作数据
        detail: 当前详情字符串

    Returns:
        str: 格式化后的详情字符串
    """
    if op_type == "operation_undo":
        undone_operation_id = op_data.get("undone_operation_id")
        undone_operation_type = op_data.get("undone_operation_type", "unknown")
        detail += (
            f"\n   撤销的操作ID: {undone_operation_id} | "
            f"类型: {format_operation_type(undone_operation_type)}"
        )
    elif op_type == "weekday_groups_updated":
        updated_count = op_data.get("updated_count", 0)
        skipped_count = op_data.get("skipped_count", 0)
        error_count = op_data.get("error_count", 0)
        detail += f"\n   已更新: {updated_count} | 跳过: {skipped_count} | 错误: {error_count}"
    elif op_type == "statistics_fixed":
        fixed_groups = op_data.get("fixed_groups", [])
        fixed_count = op_data.get("fixed_count", 0)
        groups_str = ", ".join(fixed_groups[:5])
        if len(fixed_groups) > 5:
            groups_str += "..."
        detail += f"\n   修复的归属ID: {groups_str} | 修复数量: {fixed_count}"
    elif op_type == "operation_deleted":
        operation_id = op_data.get("deleted_operation_id")
        deleted_operation_type = op_data.get("deleted_operation_type", "unknown")
        detail += (
            f"\n   操作记录ID: {operation_id} | "
            f"类型: {format_operation_type(deleted_operation_type)}"
        )
    elif op_type == "daily_data_restored":
        date = op_data.get("date", "N/A")
        total = op_data.get("total", 0)
        success_count = op_data.get("success_count", 0)
        fail_count = op_data.get("fail_count", 0)
        detail += f"\n   日期: {date} | 总数: {total} | 成功: {success_count} | 失败: {fail_count}"

    return detail
