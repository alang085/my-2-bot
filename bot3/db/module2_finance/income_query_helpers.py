"""收入查询辅助函数

包含收入查询的辅助函数，提取复杂逻辑。
"""

from typing import Optional

from db.module2_finance.income_query_data import IncomeQueryParams
from utils.query_builder import QueryBuilder


def _create_params_if_needed(
    conn,
    cursor,
    start_date: Optional[str],
    end_date: Optional[str],
    type: Optional[str],
    customer: Optional[str],
    group_id: Optional[str],
    order_id: Optional[str],
    include_undone: bool,
    params: Optional["IncomeQueryParams"],
) -> "IncomeQueryParams":
    """创建参数对象（如果需要）

    Args:
        conn: 数据库连接
        cursor: 数据库游标
        start_date: 开始日期
        end_date: 结束日期
        type: 收入类型
        customer: 客户类型
        group_id: 归属ID
        order_id: 订单ID
        include_undone: 是否包含已撤销记录
        params: 收入查询参数（如果已提供）

    Returns:
        IncomeQueryParams: 参数对象
    """
    if params is None:
        if start_date is None:
            raise ValueError("必须提供start_date或params参数")
        params = IncomeQueryParams(
            conn=conn,
            cursor=cursor,
            start_date=start_date,
            end_date=end_date,
            type=type,
            customer=customer,
            group_id=group_id,
            order_id=order_id,
            include_undone=include_undone,
        )
    return params


def _apply_date_filters(builder: QueryBuilder, params: "IncomeQueryParams") -> None:
    """应用日期过滤条件

    Args:
        builder: QueryBuilder实例
        params: 收入查询参数
    """
    builder.where("date >= ?", params.start_date)
    end_date_value = params.end_date if params.end_date else params.start_date
    builder.where("date <= ?", end_date_value)


def _apply_other_filters(builder: QueryBuilder, params: "IncomeQueryParams") -> None:
    """应用其他过滤条件

    Args:
        builder: QueryBuilder实例
        params: 收入查询参数
    """
    if params.type:
        builder.where("type = ?", params.type)
    if params.customer:
        builder.where("customer = ?", params.customer)
    if params.group_id:
        builder.where("group_id = ?", params.group_id)
    if params.order_id:
        builder.where("order_id = ?", params.order_id)

    # 默认排除已撤销的记录
    if not params.include_undone:
        builder.where("(is_undone IS NULL OR is_undone = 0)")


def _apply_sorting(builder: QueryBuilder) -> None:
    """应用排序

    Args:
        builder: QueryBuilder实例
    """
    builder.order_by_field("date", "DESC")
    builder.order_by_field("created_at", "DESC")
