"""支付账号更新辅助函数

包含支付账号更新的辅助函数，提取复杂逻辑。
"""

from typing import List, Optional, Tuple


def _build_update_list(
    account_number: Optional[str] = None,
    account_name: Optional[str] = None,
    balance: Optional[float] = None,
) -> Tuple[List[str], List]:
    """构建更新列表和参数列表

    Args:
        account_number: 账号号码
        account_name: 账号名称
        balance: 余额

    Returns:
        Tuple[updates, params]: 更新列表和参数列表
    """
    updates = []
    params = []

    if account_number is not None:
        updates.append("account_number = ?")
        params.append(account_number)

    if account_name is not None:
        updates.append("account_name = ?")
        params.append(account_name)

    if balance is not None:
        updates.append("balance = ?")
        params.append(balance)

    return updates, params


def _handle_balance_history_update(
    cursor, account_id: int, balance: Optional[float]
) -> None:
    """处理余额历史记录更新

    Args:
        cursor: 数据库游标
        account_id: 账户ID
        balance: 余额
    """
    if balance is None:
        return

    cursor.execute(
        "SELECT account_type FROM payment_accounts WHERE id = ?", (account_id,)
    )
    account_row = cursor.fetchone()
    if not account_row:
        return

    account_type = account_row["account_type"].lower()
    if account_type in ("gcash", "paymaya"):
        from db.module2_finance.payments import _save_balance_history

        _save_balance_history(cursor, account_id, account_type, balance)
