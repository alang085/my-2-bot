"""操作详情格式化 - 支付模块

包含格式化支付相关操作的逻辑。
"""

from constants import MAX_ACCOUNT_NAME_LENGTH


def format_payment_operations(op_type: str, op_data: dict, detail: str) -> str:
    """格式化支付相关操作

    Args:
        op_type: 操作类型
        op_data: 操作数据
        detail: 当前详情字符串

    Returns:
        str: 格式化后的详情字符串
    """
    if op_type == "payment_account_balance_updated":
        account_type = op_data.get("account_type", "unknown")
        old_balance = op_data.get("old_balance", 0)
        new_balance = op_data.get("new_balance", 0)
        account_id = op_data.get("account_id")
        if account_id:
            detail += (
                f"\n   账户ID: {account_id} | 类型: {account_type} | "
                f"{old_balance:,.2f} → {new_balance:,.2f}"
            )
        else:
            detail += (
                f"\n   类型: {account_type} | {old_balance:,.2f} → {new_balance:,.2f}"
            )
    elif op_type == "payment_account_updated":
        account_type = op_data.get("account_type", "unknown")
        account_number = op_data.get("account_number", "N/A")
        account_name = op_data.get("account_name", "N/A")
        detail += (
            f"\n   类型: {account_type} | 账号: {account_number} | "
            f"名称: {account_name[:MAX_ACCOUNT_NAME_LENGTH]}"
        )

    return detail
