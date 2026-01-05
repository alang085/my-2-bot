"""操作详情格式化 - 订单模块

包含格式化订单相关操作的逻辑。
"""

from handlers.module5_data.daily_operations_handlers import \
    format_operation_type


def format_order_operations(op_type: str, op_data: dict, detail: str) -> str:
    """格式化订单相关操作

    Args:
        op_type: 操作类型
        op_data: 操作数据
        detail: 当前详情字符串

    Returns:
        str: 格式化后的详情字符串
    """
    if op_type == "order_created":
        order_id = op_data.get("order_id", "N/A")
        amount = op_data.get("amount", 0)
        detail += f"\n   订单号: {order_id} | 金额: {amount:,.2f}"
    elif op_type == "order_state_change":
        old_state = op_data.get("old_state", "N/A")
        new_state = op_data.get("new_state", "N/A")
        detail += f"\n   {old_state} → {new_state}"
    elif op_type == "order_completed":
        amount = op_data.get("amount", 0)
        detail += f"\n   金额: {amount:,.2f}"
    elif op_type == "order_breach_end":
        amount = op_data.get("amount", 0)
        detail += f"\n   金额: {amount:,.2f}"

    return detail
