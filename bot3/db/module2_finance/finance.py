"""
财务数据操作模块

包含全局财务数据和分组财务数据的查询和更新。
"""

# 标准库
import logging
from typing import Dict, List, Optional

# 本地模块
from db.base import db_query, db_transaction
from utils.query_builder import QueryBuilder

# 日志
logger = logging.getLogger(__name__)


# ========== 财务数据操作 ==========


@db_query
def get_financial_data(conn, cursor) -> Dict:
    """获取全局财务数据"""
    query, params = (
        QueryBuilder("financial_data").order_by_field("id", "DESC").limit(1).build()
    )
    cursor.execute(query, params)
    row = cursor.fetchone()
    if row:
        return dict(row)
    return {
        "valid_orders": 0,
        "valid_amount": 0,
        "liquid_funds": 0,
        "new_clients": 0,
        "new_clients_amount": 0,
        "old_clients": 0,
        "old_clients_amount": 0,
        "interest": 0,
        "completed_orders": 0,
        "completed_amount": 0,
        "breach_orders": 0,
        "breach_amount": 0,
        "breach_end_orders": 0,
        "breach_end_amount": 0,
    }


@db_transaction
def _check_field_exists(cursor, field: str) -> bool:
    """检查字段是否存在

    Args:
        cursor: 数据库游标对象
        field: 字段名

    Returns:
        字段是否存在
    """
    cursor.execute("SELECT * FROM financial_data ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    if row:
        row_dict = dict(row)
        return field in row_dict
    return False


def _invalidate_financial_cache() -> None:
    """清除财务数据缓存"""
    try:
        from utils.cache import invalidate_cache

        invalidate_cache("financial_")
    except Exception:
        pass


@db_transaction
def update_financial_data(conn, cursor, field: str, amount: float) -> bool:
    """更新财务数据字段

    Args:
        conn: 数据库连接对象
        cursor: 数据库游标对象
        field: 要更新的字段名
        amount: 要增加/减少的金额（正数表示增加，负数表示减少）

    Returns:
        bool: 如果成功更新，返回 True；否则返回 False

    Note:
        - 此函数会自动提交事务（通过 @db_transaction 装饰器）
        - 如果字段不存在，会使用默认值 0
        - 使用增量更新（current_value + amount）
    """
    from db.module2_finance.finance_init import init_financial_data_if_needed
    from db.module2_finance.finance_update import (get_current_field_value,
                                                   update_financial_field)
    from db.module2_finance.finance_validate import validate_financial_field

    if not validate_financial_field(field):
        return False

    init_financial_data_if_needed(cursor)

    if not _check_field_exists(cursor, field):
        return False

    current_value = get_current_field_value(cursor, field)
    new_value = current_value + amount
    success = update_financial_field(cursor, field, new_value)

    if success:
        logger.debug(
            f"财务数据已更新: {field} = {current_value} + {amount} = {new_value}"
        )
        _invalidate_financial_cache()

    return success


# ========== 分组数据操作 ==========


@db_query
def get_grouped_data(conn, cursor, group_id: Optional[str] = None) -> Dict:
    """获取分组数据"""
    if group_id:
        query, params = (
            QueryBuilder("grouped_data").where("group_id = ?", group_id).build()
        )
        cursor.execute(query, params)
        row = cursor.fetchone()
        if row:
            return dict(row)
        return {
            "group_id": group_id,
            "valid_orders": 0,
            "valid_amount": 0,
            "liquid_funds": 0,
            "new_clients": 0,
            "new_clients_amount": 0,
            "old_clients": 0,
            "old_clients_amount": 0,
            "interest": 0,
            "completed_orders": 0,
            "completed_amount": 0,
            "breach_orders": 0,
            "breach_amount": 0,
            "breach_end_orders": 0,
            "breach_end_amount": 0,
        }
    else:
        # 获取所有分组数据
        query, params = QueryBuilder("grouped_data").build()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        result = {}
        for row in rows:
            result[row["group_id"]] = dict(row)
        return result


@db_transaction
def _validate_grouped_data_field(field: str) -> bool:
    """验证分组数据字段名"""
    valid_fields = [
        "valid_orders",
        "valid_amount",
        "liquid_funds",
        "new_clients",
        "new_clients_amount",
        "old_clients",
        "old_clients_amount",
        "interest",
        "completed_orders",
        "completed_amount",
        "breach_orders",
        "breach_amount",
        "breach_end_orders",
        "breach_end_amount",
        "overdue_orders",
        "overdue_amount",
    ]
    if field not in valid_fields:
        logger.error(f"无效的分组数据字段名: {field}")
        return False
    return True


def _get_or_create_grouped_data(
    cursor, group_id: str, field: str
) -> tuple[float, bool]:
    """获取或创建分组数据，返回(当前值, 是否为新创建)"""
    query, params = QueryBuilder("grouped_data").where("group_id = ?", group_id).build()
    cursor.execute(query, params)
    row = cursor.fetchone()

    if not row:
        cursor.execute(
            """
        INSERT INTO grouped_data (
            group_id, valid_orders, valid_amount, liquid_funds,
            new_clients, new_clients_amount,
            old_clients, old_clients_amount,
            interest, completed_orders, completed_amount,
            breach_orders, breach_amount,
            breach_end_orders, breach_end_amount
        ) VALUES (?, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        """,
            (group_id,),
        )
        return 0.0, True

    row_dict = dict(row)
    if field not in row_dict:
        logger.warning(f"字段 {field} 不存在于 grouped_data 表中（兼容旧数据库）")
        return 0.0, False
    return row_dict.get(field, 0), False


def _update_grouped_data_field(
    cursor, group_id: str, field: str, new_value: float
) -> bool:
    """更新分组数据字段值"""
    cursor.execute(
        f"""
        UPDATE grouped_data
    SET "{field}" = ?, updated_at = CURRENT_TIMESTAMP
    WHERE group_id = ?
    """,
        (new_value, group_id),
    )
    return cursor.rowcount > 0


@db_transaction
def update_grouped_data(conn, cursor, group_id: str, field: str, amount: float) -> bool:
    """更新分组数据字段

    Args:
        conn: 数据库连接对象
        cursor: 数据库游标对象
        group_id: 归属ID
        field: 要更新的字段名
        amount: 要增加/减少的金额（正数表示增加，负数表示减少）

    Returns:
        bool: 如果成功更新，返回 True；否则返回 False

    Note:
        - 此函数会自动提交事务（通过 @db_transaction 装饰器）
        - 如果分组不存在，会自动创建
        - 使用增量更新（current_value + amount）
    """
    if not _validate_grouped_data_field(field):
        return False

    if not group_id:
        logger.error("group_id 不能为空")
        return False

    current_value, is_new = _get_or_create_grouped_data(cursor, group_id, field)
    if not is_new and current_value is None:
        return False

    new_value = current_value + amount
    if not _update_grouped_data_field(cursor, group_id, field, new_value):
        logger.warning(
            f"更新分组数据失败: group_id={group_id}, field={field}, amount={amount}, rowcount=0"
        )
        return False

    logger.debug(
        f"分组数据已更新: {group_id} {field} = {current_value} + {amount} = {new_value}"
    )
    return True


@db_query
def get_all_group_ids(conn, cursor) -> List[str]:
    """获取所有归属ID列表"""
    query, params = (
        QueryBuilder("grouped_data")
        .select("DISTINCT group_id")
        .order_by_field("group_id")
        .build()
    )
    cursor.execute(query, params)
    rows = cursor.fetchall()
    return [row[0] for row in rows]
