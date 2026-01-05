"""
支付账号操作模块

包含GCASH和PayMaya账号的管理，以及支出记录操作。
"""

# 标准库
import logging
from datetime import datetime
from typing import Dict, List, Optional

# 第三方库
import pytz

# 本地模块
from db.base import db_query, db_transaction
from utils.query_builder import QueryBuilder

# 日志
logger = logging.getLogger(__name__)


# ========== 支付账号操作 ==========


@db_query
def get_payment_account(conn, cursor, account_type: str) -> Optional[Dict]:
    """获取支付账号信息"""
    query, params = (
        QueryBuilder("payment_accounts").where("account_type = ?", account_type).build()
    )
    cursor.execute(query, params)
    row = cursor.fetchone()
    if row:
        return dict(row)
    return None


@db_query
def get_all_payment_accounts(conn, cursor) -> List[Dict]:
    """获取所有支付账号信息"""
    query, params = (
        QueryBuilder("payment_accounts")
        .order_by_field("account_type")
        .order_by_field("account_name")
        .build()
    )
    cursor.execute(query, params)
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


@db_query
def get_payment_accounts_by_type(conn, cursor, account_type: str) -> List[Dict]:
    """获取指定类型的所有支付账号信息"""
    query, params = (
        QueryBuilder("payment_accounts")
        .where("account_type = ?", account_type)
        .order_by_field("account_name")
        .build()
    )
    cursor.execute(query, params)
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


@db_query
def get_payment_account_by_id(conn, cursor, account_id: int) -> Optional[Dict]:
    """根据ID获取支付账号信息"""
    query, params = QueryBuilder("payment_accounts").where("id = ?", account_id).build()
    cursor.execute(query, params)
    row = cursor.fetchone()
    if row:
        return dict(row)
    return None


@db_transaction
def create_payment_account(
    conn,
    cursor,
    account_type: str,
    account_number: str,
    account_name: str = "",
    balance: float = 0,
) -> int:
    """创建新的支付账号，返回账户ID"""
    cursor.execute(
        """
    INSERT INTO payment_accounts (account_type, account_number, account_name, balance)
    VALUES (?, ?, ?, ?)
    """,
        (account_type, account_number, account_name or "", balance or 0),
    )
    return cursor.lastrowid


@db_transaction
def _save_balance_history(
    cursor, account_id: int, account_type: str, balance: float
) -> None:
    """保存余额历史记录"""
    from datetime import datetime

    import pytz

    tz = pytz.timezone("Asia/Shanghai")
    date_str = datetime.now(tz).strftime("%Y-%m-%d")

    cursor.execute(
        """
        SELECT id FROM payment_balance_history
        WHERE account_id = ? AND date = ?
        """,
        (account_id, date_str),
    )
    existing = cursor.fetchone()

    if existing:
        cursor.execute(
            """
            UPDATE payment_balance_history
            SET balance = ?, created_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (balance, existing[0]),
        )
    else:
        cursor.execute(
            """
            INSERT INTO payment_balance_history (account_id, account_type, balance, date)
            VALUES (?, ?, ?, ?)
            """,
            (account_id, account_type, balance, date_str),
        )
    logger.debug(
        f"已实时保存账户 {account_id} ({account_type}) 的余额历史: {balance:,.2f}"
    )


def _validate_update_fields(updates: list) -> bool:
    """验证更新字段名是否在白名单中"""
    valid_field_names = ["account_number", "account_name", "balance", "updated_at"]
    for update_clause in updates:
        field_name = update_clause.split(" = ")[0]
        if field_name not in valid_field_names:
            logger.error(f"无效的支付账户字段名: {field_name}")
            return False
    return True


def _build_update_query(updates: list, params: list, account_id: int) -> tuple:
    """构建更新查询语句和参数"""
    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(account_id)
    set_clause = ", ".join(updates)
    query = f"UPDATE payment_accounts SET {set_clause} WHERE id = ?"  # nosec B608
    return query, params


def update_payment_account_by_id(
    conn,
    cursor,
    account_id: int,
    account_number: str = None,
    account_name: str = None,
    balance: float = None,
) -> bool:
    """根据ID更新支付账号信息"""
    from db.module2_finance.payments_update_helpers import (
        _build_update_list, _handle_balance_history_update)

    updates, params = _build_update_list(account_number, account_name, balance)

    if not updates:
        return False

    if not _validate_update_fields(updates):
        return False

    query, params = _build_update_query(updates, params, account_id)

    try:
        cursor.execute(query, params)
        _handle_balance_history_update(cursor, account_id, balance)
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"更新支付账号时出错: {e}", exc_info=True)
        return False


@db_transaction
def delete_payment_account(conn, cursor, account_id: int) -> bool:
    """删除支付账号"""
    cursor.execute("DELETE FROM payment_accounts WHERE id = ?", (account_id,))
    return cursor.rowcount > 0


@db_transaction
def update_payment_account(
    conn,
    cursor,
    account_type: str,
    account_number: str = None,
    account_name: str = None,
    balance: float = None,
) -> bool:
    """更新支付账号信息（兼容旧代码，更新该类型的第一个账户）"""
    cursor.execute(
        "SELECT * FROM payment_accounts WHERE account_type = ? LIMIT 1", (account_type,)
    )
    row = cursor.fetchone()

    if row:
        # 更新现有记录
        account_id = row["id"]
        # 在同一个事务中，直接调用同步函数
        return update_payment_account_by_id(
            conn, cursor, account_id, account_number, account_name, balance
        )
    else:
        # 创建新记录
        if account_number:
            create_payment_account(
                conn,
                cursor,
                account_type,
                account_number,
                account_name or "",
                balance or 0,
            )
            return True
        return False


@db_transaction
def record_expense(conn, cursor, date: str, type: str, amount: float, note: str) -> int:
    """记录开销，返回开销记录ID"""
    from db.module2_finance.expense_daily import update_daily_data_for_expense
    from db.module2_finance.expense_financial import \
        update_financial_data_for_expense
    from db.module2_finance.expense_validate import (get_expense_field,
                                                     validate_expense_record)

    # 验证开销类型
    is_valid, error_msg = validate_expense_record(type, amount)
    if not is_valid:
        raise ValueError(error_msg)

    # 插入开销记录
    cursor.execute(
        """
    INSERT INTO expense_records (date, type, amount, note)
    VALUES (?, ?, ?, ?)
    """,
        (date, type, amount, note),
    )
    expense_id = cursor.lastrowid

    # 获取开销字段名
    field = get_expense_field(type)

    # 更新财务数据
    update_financial_data_for_expense(cursor, amount)

    # 更新日结数据
    update_daily_data_for_expense(cursor, date, field, amount)

    # 清除相关缓存
    try:
        from utils.cache import invalidate_cache

        invalidate_cache("expense_")
        invalidate_cache("financial_")
    except Exception:
        pass  # 缓存失效失败不影响主流程

    return expense_id


@db_query
def get_expense_records(
    conn, cursor, start_date: str, end_date: str = None, type: Optional[str] = None
) -> List[Dict]:
    """获取开销记录（支持日期范围）"""
    query = "SELECT * FROM expense_records WHERE date >= ?"
    params = [start_date]

    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    else:
        query += " AND date <= ?"
        params.append(start_date)

    if type:
        query += " AND type = ?"
        params.append(type)

    query += " ORDER BY date DESC, created_at ASC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


@db_transaction
def delete_expense_record(conn, cursor, expense_id: int) -> bool:
    """删除开销记录"""
    cursor.execute("DELETE FROM expense_records WHERE id = ?", (expense_id,))
    return cursor.rowcount > 0


@db_transaction
def delete_income_record(conn, cursor, income_id: int) -> bool:
    """强制删除收入记录（不可恢复）"""
    cursor.execute("DELETE FROM income_records WHERE id = ?", (income_id,))
    return cursor.rowcount > 0


@db_transaction
def mark_income_undone(conn, cursor, income_id: int) -> bool:
    """标记收入记录为已撤销（不删除，保留历史记录）"""
    # income_records表没有updated_at字段，只更新is_undone
    cursor.execute(
        """
    UPDATE income_records
    SET is_undone = 1
    WHERE id = ?
    """,
        (income_id,),
    )
    return cursor.rowcount > 0
