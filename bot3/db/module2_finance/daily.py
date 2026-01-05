"""
日结数据操作模块

包含按日期和归属ID的日结流量数据操作。
"""

# 标准库
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# 本地模块
from db.base import db_query, db_transaction

# 日志
logger = logging.getLogger(__name__)


# ========== 日结数据操作 ==========


@db_query
def get_daily_data(conn, cursor, date: str, group_id: Optional[str] = None) -> Dict:
    """获取日结数据"""
    if group_id:
        cursor.execute(
            "SELECT * FROM daily_data WHERE date = ? AND group_id = ?", (date, group_id)
        )
    else:
        # 全局日结数据（group_id为NULL）
        cursor.execute(
            "SELECT * FROM daily_data WHERE date = ? AND group_id IS NULL", (date,)
        )

    row = cursor.fetchone()
    if row:
        return dict(row)

    return {
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
        "liquid_flow": 0,
        "company_expenses": 0,
        "other_expenses": 0,
    }


@db_transaction
def update_daily_data(
    conn, cursor, date: str, field: str, amount: float, group_id: Optional[str] = None
) -> bool:
    """更新日结数据字段

    Args:
        conn: 数据库连接对象
        cursor: 数据库游标对象
        date: 日期字符串，格式 'YYYY-MM-DD'
        field: 要更新的字段名
        amount: 要增加/减少的金额（正数表示增加，负数表示减少）
        group_id: 归属ID，如果为 None 则更新全局日结数据

    Returns:
        bool: 如果成功更新，返回 True；否则返回 False

    Note:
        - 此函数会自动提交事务（通过 @db_transaction 装饰器）
        - 如果日结数据不存在，会自动创建
        - 使用增量更新（current_value + amount）
    """
    from db.module2_finance.daily_init import init_daily_data_if_needed
    from db.module2_finance.daily_update import (get_current_daily_value,
                                                 update_daily_field)
    from db.module2_finance.daily_validate import (validate_daily_field,
                                                   validate_date_format)

    # 验证字段名和日期格式
    if not validate_daily_field(field):
        return False

    if not validate_date_format(date):
        return False

    # 初始化日结数据（如果需要）
    init_daily_data_if_needed(cursor, date, group_id)

    # 获取当前值
    current_value = get_current_daily_value(cursor, date, field, group_id)

    # 计算新值并更新
    new_value = current_value + amount
    success = update_daily_field(cursor, date, field, new_value, group_id)

    if success:
        logger.debug(
            f"日结数据已更新: {date} {group_id or '全局'} {field} = {current_value} + {amount} = {new_value}"
        )

    return success


@db_query
def _build_date_range_where_clause(
    start_date: str, end_date: str, group_id: Optional[str]
) -> Tuple[str, List]:
    """构建日期范围查询条件

    Args:
        start_date: 起始日期
        end_date: 结束日期
        group_id: 归属ID

    Returns:
        (WHERE子句, 参数列表)
    """
    where_clause = "date >= ? AND date <= ?"
    params = [start_date, end_date]

    if group_id:
        where_clause += " AND group_id = ?"
        params.append(group_id)
    else:
        where_clause += " AND group_id IS NULL"

    return where_clause, params


def _get_stats_keys() -> List[str]:
    """获取统计字段键列表

    Returns:
        字段键列表
    """
    return [
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
        "liquid_flow",
        "company_expenses",
        "other_expenses",
    ]


def _build_stats_result(row, keys: List[str]) -> Dict:
    """构建统计结果字典

    Args:
        row: 查询结果行
        keys: 字段键列表

    Returns:
        统计结果字典
    """
    result = {}
    for i, key in enumerate(keys):
        result[key] = row[i] if row[i] is not None else 0
    return result


def get_stats_by_date_range(
    conn, cursor, start_date: str, end_date: str, group_id: Optional[str] = None
) -> Dict:
    """根据日期范围聚合统计数据"""
    where_clause, params = _build_date_range_where_clause(
        start_date, end_date, group_id
    )

    cursor.execute(
        f"""
    SELECT
        SUM(new_clients) as new_clients,
        SUM(new_clients_amount) as new_clients_amount,
        SUM(old_clients) as old_clients,
        SUM(old_clients_amount) as old_clients_amount,
        SUM(interest) as interest,
        SUM(completed_orders) as completed_orders,
        SUM(completed_amount) as completed_amount,
        SUM(breach_orders) as breach_orders,
        SUM(breach_amount) as breach_amount,
        SUM(breach_end_orders) as breach_end_orders,
        SUM(breach_end_amount) as breach_end_amount,
        SUM(liquid_flow) as liquid_flow,
        SUM(company_expenses) as company_expenses,
        SUM(other_expenses) as other_expenses
    FROM daily_data
    WHERE {where_clause}
    """,
        params,
    )

    row = cursor.fetchone()
    keys = _get_stats_keys()
    return _build_stats_result(row, keys)
