"""收入明细基础操作模块

包含收入记录的创建和基础查询功能。
"""

# 标准库
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# 第三方库
import pytz

# 本地模块
from db.base import db_query, db_transaction
from db.module2_finance.income_data import (IncomeInsertParams,
                                            IncomeRecordParams)

# QueryBuilder 使用延迟导入以避免循环导入


def _get_beijing_timestamp() -> str:
    """获取北京时间戳字符串

    Returns:
        北京时间字符串
    """
    tz_beijing = pytz.timezone("Asia/Shanghai")
    return datetime.now(tz_beijing).strftime("%Y-%m-%d %H:%M:%S")


def _prepare_income_record_values(
    params: IncomeRecordParams, created_by: Optional[int], created_at: str
) -> Tuple:
    """准备收入记录插入值

    Args:
        params: 收入记录参数
        created_by: 创建者ID
        created_at: 创建时间

    Returns:
        值元组
    """
    return (
        params.date,
        params.type,
        params.amount,
        params.group_id,
        params.order_id,
        params.order_date,
        params.customer,
        params.weekday_group,
        params.notes,
        created_by,
        created_at,
    )


def _insert_income_record(
    params: IncomeInsertParams, created_by: Optional[int], created_at: str
) -> int:
    """插入收入记录到数据库

    Args:
        params: 收入插入参数（包含cursor）
        created_by: 创建者ID
        created_at: 创建时间

    Returns:
        收入记录ID
    """
    record_params = IncomeRecordParams(
        date=params.date,
        type=params.type,
        amount=params.amount,
        group_id=params.group_id,
        order_id=params.order_id,
        order_date=params.order_date,
        customer=params.customer,
        weekday_group=params.weekday_group,
        notes=params.notes,
    )
    values = _prepare_income_record_values(record_params, created_by, created_at)

    params.cursor.execute(
        """
    INSERT INTO income_records (
        date, type, amount, group_id, order_id, order_date,
        customer, weekday_group, note, created_by, created_at, is_undone
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
    """,
        values,
    )
    return params.cursor.lastrowid


def _invalidate_income_cache() -> None:
    """清除收入相关缓存"""
    try:
        from utils.cache import invalidate_cache

        invalidate_cache("income_")
        invalidate_cache("financial_")
    except Exception:
        pass  # 缓存失效失败不影响主流程


def _record_income_impl(params: "IncomeRecordFullParams") -> int:
    """记录收入明细（内部实现）

    Args:
        params: 收入记录完整参数

    Returns:
        收入记录ID
    """
    from db.module2_finance.income_data import IncomeRecordFullParams

    created_at = _get_beijing_timestamp()
    insert_params = IncomeInsertParams(
        cursor=params.cursor,
        date=params.date,
        type=params.type,
        amount=params.amount,
        group_id=params.group_id,
        order_id=params.order_id,
        order_date=params.order_date,
        customer=params.customer,
        weekday_group=params.weekday_group,
        notes=params.note,
    )
    income_id = _insert_income_record(insert_params, params.created_by, created_at)
    _invalidate_income_cache()
    return income_id


@db_transaction
def record_income(
    conn,
    cursor,
    date: str,
    type: str,
    amount: float,
    group_id: Optional[str] = None,
    order_id: Optional[str] = None,
    order_date: Optional[str] = None,
    customer: Optional[str] = None,
    weekday_group: Optional[str] = None,
    note: Optional[str] = None,
    created_by: Optional[int] = None,
) -> int:
    """记录收入明细，返回收入记录ID（向后兼容包装）

    Args:
        conn: 数据库连接（由装饰器注入）
        cursor: 数据库游标（由装饰器注入）
        date: 日期
        type: 类型
        amount: 金额
        group_id: 归属ID
        order_id: 订单ID
        order_date: 订单日期
        customer: 客户
        weekday_group: 星期分组
        note: 备注
        created_by: 创建者ID

    Returns:
        收入记录ID
    """
    from db.module2_finance.income_data import IncomeRecordFullParams

    params = IncomeRecordFullParams(
        conn=conn,
        cursor=cursor,
        date=date,
        type=type,
        amount=amount,
        group_id=group_id,
        order_id=order_id,
        order_date=order_date,
        customer=customer,
        weekday_group=weekday_group,
        note=note,
        created_by=created_by,
    )
    return _record_income_impl(params)


@db_query
def get_income_records(
    conn=None,
    cursor=None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    type: Optional[str] = None,
    customer: Optional[str] = None,
    group_id: Optional[str] = None,
    order_id: Optional[str] = None,
    include_undone: bool = False,
    params: Optional["IncomeQueryParams"] = None,
) -> List[Dict]:
    """获取收入明细（支持多维度过滤）

    支持两种调用方式：
    1. 旧方式（向后兼容）：直接传递参数
    2. 新方式：传递IncomeQueryParams对象

    Args:
        conn: 数据库连接（旧方式，由装饰器提供）
        cursor: 数据库游标（旧方式，由装饰器提供）
        start_date: 开始日期（旧方式）
        end_date: 结束日期（旧方式）
        type: 收入类型（旧方式）
        customer: 客户类型（旧方式）
        group_id: 归属ID（旧方式）
        order_id: 订单ID（旧方式）
        include_undone: 是否包含已撤销记录（旧方式）
        params: 收入查询参数（新方式）

    Returns:
        收入记录列表
    """
    from db.module2_finance.income_query_helpers import (
        _apply_date_filters, _apply_other_filters, _apply_sorting,
        _create_params_if_needed)

    # 向后兼容：如果使用旧方式调用，创建params对象
    params = _create_params_if_needed(
        conn,
        cursor,
        start_date,
        end_date,
        type,
        customer,
        group_id,
        order_id,
        include_undone,
        params,
    )

    # 延迟导入以避免循环导入
    from utils.query_builder import QueryBuilder

    builder = QueryBuilder("income_records")

    # 应用过滤条件
    _apply_date_filters(builder, params)
    _apply_other_filters(builder, params)
    _apply_sorting(builder)

    query, query_params = builder.build()
    params.cursor.execute(query, query_params)
    rows = params.cursor.fetchall()
    return [dict(row) for row in rows]


@db_query
def get_interest_by_order_id(conn, cursor, order_id: str) -> Dict:
    """获取指定订单的所有利息收入汇总（排除已撤销的记录）"""
    # 延迟导入以避免循环导入
    from utils.query_builder import QueryBuilder

    query, params = (
        QueryBuilder("income_records")
        .select(
            [
                "COUNT(*) as count",
                "SUM(amount) as total_amount",
                "MIN(date) as first_date",
                "MAX(date) as last_date",
            ]
        )
        .where("order_id = ?", order_id)
        .where("type = ?", "interest")
        .where("(is_undone IS NULL OR is_undone = 0)")
        .build()
    )
    cursor.execute(query, params)
    row = cursor.fetchone()
    if row and row[0] > 0:
        return {
            "count": row[0],
            "total_amount": row[1] or 0.0,
            "first_date": row[2],
            "last_date": row[3],
        }
    return {"count": 0, "total_amount": 0.0, "first_date": None, "last_date": None}


@db_query
def get_all_interest_by_order_id(conn, cursor, order_id: str) -> List[Dict]:
    """获取指定订单的所有利息收入明细（排除已撤销的记录）"""
    cursor.execute(
        """
    SELECT * FROM income_records
    WHERE order_id = ? AND type = 'interest' AND (is_undone IS NULL OR is_undone = 0)
    ORDER BY date ASC, created_at ASC
    """,
        (order_id,),
    )

    rows = cursor.fetchall()
    return [dict(row) for row in rows]


@db_query
def get_interests_by_order_ids(
    conn, cursor, order_ids: List[str]
) -> Dict[str, List[Dict]]:
    """批量获取多个订单的利息收入明细（优化N+1查询）

    Args:
        order_ids: 订单ID列表

    Returns:
        字典，key为order_id，value为该订单的利息记录列表
    """
    if not order_ids:
        return {}

    # 使用IN查询批量获取（排除已撤销的记录）
    placeholders = ",".join(["?"] * len(order_ids))
    cursor.execute(
        f"""
    SELECT * FROM income_records
    WHERE order_id IN ({placeholders})
    AND type = 'interest'
    AND (is_undone IS NULL OR is_undone = 0)
    ORDER BY order_id, date ASC, created_at ASC
    """,
        order_ids,
    )

    rows = cursor.fetchall()

    # 按order_id分组
    result = {}
    for row in rows:
        order_id = row["order_id"]
        if order_id not in result:
            result[order_id] = []
        result[order_id].append(dict(row))

    # 确保所有order_id都有条目（即使没有利息记录）
    for order_id in order_ids:
        if order_id not in result:
            result[order_id] = []

    return result
