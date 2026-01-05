"""操作详情格式化 - 财务模块

包含格式化财务相关操作的逻辑。
"""

from constants import MAX_NOTE_LENGTH
from handlers.module5_data.daily_operations_handlers import \
    format_operation_type


def format_finance_operations(op_type: str, op_data: dict, detail: str) -> str:
    """格式化财务相关操作

    Args:
        op_type: 操作类型
        op_data: 操作数据
        detail: 当前详情字符串

    Returns:
        str: 格式化后的详情字符串
    """
    if op_type == "interest":
        amount = op_data.get("amount", 0)
        detail += f"\n   金额: {amount:,.2f}"
    elif op_type == "principal_reduction":
        amount = op_data.get("amount", 0)
        old_amount = op_data.get("old_amount", 0)
        new_amount = op_data.get("new_amount", 0)
        detail += f"\n   减少: {amount:,.2f} | {old_amount:,.2f} → {new_amount:,.2f}"
    elif op_type == "expense":
        amount = op_data.get("amount", 0)
        expense_type = op_data.get("type", "unknown")
        note = op_data.get("note", "")
        detail += f"\n   类型: {expense_type} | 金额: {amount:,.2f}"
        if note:
            detail += f"\n   备注: {note[:MAX_NOTE_LENGTH]}"
    elif op_type == "funds_adjustment":
        amount = op_data.get("amount", 0)
        adjustment_type = "增加" if amount > 0 else "减少"
        new_balance = op_data.get("new_balance", 0)
        note = op_data.get("note", "")
        detail += f"\n   类型: {adjustment_type} | 金额: {abs(amount):,.2f} | 新余额: {new_balance:,.2f}"
        if note:
            detail += f"\n   备注: {note[:MAX_NOTE_LENGTH]}"

    return detail
