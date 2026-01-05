"""订单更新 - 分类表更新模块

包含更新分类表的逻辑。
"""

import logging
from typing import Any, Dict

from db.module3_order.order_update_data import ClassifiedTableUpdateParams
from db.module3_order.orders_update_helpers import (
    _get_classified_table_names, _update_all_classified_tables_fields,
    _update_classified_tables_on_customer_change,
    _update_classified_tables_on_order_id_change,
    _update_classified_tables_on_state_change,
    _update_classified_tables_on_weekday_change)

logger = logging.getLogger(__name__)


def update_classified_tables(
    cursor,
    old_order: Dict[str, Any],
    new_order_data: Dict[str, Any],
    updated_at: str,
) -> None:
    """更新分类表

    Args:
        cursor: 数据库游标
        old_order: 旧订单信息
        new_order_data: 新订单数据
        updated_at: 更新时间
    """
    old_order_id = old_order["order_id"]
    new_order_id = new_order_data["order_id"]
    old_state = old_order["state"]
    new_state = new_order_data["state"]
    old_weekday_group = old_order["weekday_group"]
    new_weekday_group = new_order_data["weekday_group"]
    old_customer = old_order["customer"]
    new_customer = new_order_data["customer"]
    old_created_at = old_order.get("created_at")

    # 如果 order_id 变化，需要从所有旧分类表删除，然后添加到新分类表
    if old_order_id != new_order_id:
        _handle_order_id_change(
            cursor,
            old_order,
            old_order_id,
            new_order_data,
            old_created_at or updated_at,
            updated_at,
        )
    else:
        # 如果 order_id 不变，只需要更新相关分类表
        params = ClassifiedTableUpdateParams(
            cursor=cursor,
            old_state=old_state,
            new_state=new_state,
            old_weekday_group=old_weekday_group,
            new_weekday_group=new_weekday_group,
            old_customer=old_customer,
            new_customer=new_customer,
            order_id=old_order_id,
            order_data=new_order_data,
            old_created_at=old_created_at or updated_at,
            updated_at=updated_at,
        )
        _handle_order_id_unchanged(params)


def _handle_order_id_change(
    cursor,
    old_order: Dict[str, Any],
    old_order_id: str,
    new_order_data: Dict[str, Any],
    old_created_at: str,
    updated_at: str,
) -> None:
    """处理 order_id 变化的情况

    Args:
        cursor: 数据库游标
        old_order: 旧订单信息
        old_order_id: 旧订单ID
        new_order_data: 新订单数据
        old_created_at: 旧创建时间
        updated_at: 更新时间
    """
    old_order_data = old_order.copy()
    old_classified_tables = _get_classified_table_names(old_order_data)

    _update_classified_tables_on_order_id_change(
        cursor,
        old_order_id,
        new_order_data,
        old_classified_tables,
        old_created_at,
        updated_at,
    )


def _update_classified_tables_for_changes(params: ClassifiedTableUpdateParams) -> None:
    """更新分类表的变化（状态、星期分组、客户类型）

    Args:
        params: 分类表更新参数
    """
    _update_classified_tables_on_state_change(
        params.cursor,
        params.old_state,
        params.new_state,
        params.order_id,
        params.order_data,
        params.old_created_at,
        params.updated_at,
    )
    _update_classified_tables_on_weekday_change(
        params.cursor,
        params.old_weekday_group,
        params.new_weekday_group,
        params.order_id,
        params.order_data,
        params.old_created_at,
        params.updated_at,
    )
    _update_classified_tables_on_customer_change(
        params.cursor,
        params.old_customer,
        params.new_customer,
        params.order_id,
        params.order_data,
        params.old_created_at,
        params.updated_at,
    )


def _update_classified_tables_on_changes(params: ClassifiedTableUpdateParams) -> None:
    """更新分类表的变化

    Args:
        params: 分类表更新参数
    """
    _update_classified_tables_for_changes(params)


def _update_all_classified_fields(params: ClassifiedFieldsUpdateParams) -> None:
    """更新所有分类表字段

    Args:
        params: 分类表字段更新参数
    """
    _update_all_classified_tables_fields(params)


def _handle_order_id_unchanged(params: ClassifiedTableUpdateParams) -> None:
    """处理 order_id 不变的情况

    Args:
        params: 分类表更新参数
    """
    _update_classified_tables_on_changes(params)

    fields_params = ClassifiedFieldsUpdateParams(
        cursor=params.cursor,
        order_data=params.order_data,
        new_order_id=params.order_id,
        new_date_str=params.order_data.get("date", ""),
        new_weekday_group=params.new_weekday_group,
        new_customer=params.new_customer,
        new_amount=params.order_data.get("amount", 0.0),
        new_state=params.new_state,
        updated_at=params.updated_at,
    )
    _update_all_classified_fields(fields_params)
