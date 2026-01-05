"""订单更新辅助函数

包含更新订单分类表的辅助函数。
"""

# 标准库
import logging
from datetime import datetime
from typing import Dict

# 本地模块
from db.module3_order.orders_basic import (
    _ensure_classified_table_exists, _get_classified_table_names,
    _insert_order_to_classified_table_sync)

logger = logging.getLogger(__name__)


def _update_classified_tables_on_order_id_change(
    cursor,
    old_order_id: str,
    new_order_data: Dict,
    old_classified_tables: list,
    old_created_at: str,
    updated_at: str,
) -> None:
    """处理订单ID变化时的分类表更新"""
    # 从所有旧分类表删除
    for table_name in old_classified_tables:
        _ensure_classified_table_exists(cursor, table_name)
        cursor.execute(
            f"DELETE FROM {table_name} WHERE order_id = ?", (old_order_id,)
        )  # nosec B608

    # 添加到新分类表
    new_classified_tables = _get_classified_table_names(new_order_data)
    for table_name in new_classified_tables:
        _insert_order_to_classified_table_sync(
            cursor, table_name, new_order_data, old_created_at or updated_at, updated_at
        )


def _update_classified_tables_on_state_change(
    cursor,
    old_state: str,
    new_state: str,
    old_order_id: str,
    order_data: Dict,
    old_created_at: str,
    updated_at: str,
) -> None:
    """处理订单状态变化时的分类表更新"""
    if old_state == new_state:
        return

    state_table_map = {
        "normal": "orders_normal",
        "overdue": "orders_overdue",
        "breach": "orders_breach",
        "end": "orders_end",
        "breach_end": "orders_breach_end",
    }
    old_state_table = state_table_map.get(old_state)
    new_state_table = state_table_map.get(new_state)

    if old_state_table:
        _ensure_classified_table_exists(cursor, old_state_table)
        cursor.execute(
            f"DELETE FROM {old_state_table} WHERE order_id = ?", (old_order_id,)
        )  # nosec B608

    if new_state_table:
        _insert_order_to_classified_table_sync(
            cursor,
            new_state_table,
            order_data,
            old_created_at or updated_at,
            updated_at,
        )


def _update_classified_tables_on_weekday_change(
    cursor,
    old_weekday_group: str,
    new_weekday_group: str,
    old_order_id: str,
    order_data: Dict,
    old_created_at: str,
    updated_at: str,
) -> None:
    """处理订单星期分组变化时的分类表更新"""
    if old_weekday_group == new_weekday_group:
        return

    weekday_map = {
        "一": "orders_monday",
        "二": "orders_tuesday",
        "三": "orders_wednesday",
        "四": "orders_thursday",
        "五": "orders_friday",
        "六": "orders_saturday",
        "日": "orders_sunday",
    }
    old_weekday_table = weekday_map.get(old_weekday_group)
    new_weekday_table = weekday_map.get(new_weekday_group)

    if old_weekday_table:
        _ensure_classified_table_exists(cursor, old_weekday_table)
        cursor.execute(
            f"DELETE FROM {old_weekday_table} WHERE order_id = ?", (old_order_id,)
        )  # nosec B608

    if new_weekday_table:
        _insert_order_to_classified_table_sync(
            cursor,
            new_weekday_table,
            order_data,
            old_created_at or updated_at,
            updated_at,
        )


def _update_classified_tables_on_customer_change(
    cursor,
    old_customer: str,
    new_customer: str,
    old_order_id: str,
    order_data: Dict,
    old_created_at: str,
    updated_at: str,
) -> None:
    """处理订单客户类型变化时的分类表更新"""
    if old_customer == new_customer:
        return

    old_customer_table = (
        "orders_new_customers" if old_customer == "A" else "orders_old_customers"
    )
    new_customer_table = (
        "orders_new_customers" if new_customer == "A" else "orders_old_customers"
    )

    _ensure_classified_table_exists(cursor, old_customer_table)
    cursor.execute(
        f"DELETE FROM {old_customer_table} WHERE order_id = ?", (old_order_id,)
    )  # nosec B608

    _insert_order_to_classified_table_sync(
        cursor, new_customer_table, order_data, old_created_at or updated_at, updated_at
    )


def _update_all_classified_tables_fields(
    params: "ClassifiedFieldsUpdateParams",
) -> None:
    """更新所有分类表中的字段（当order_id不变时）

    Args:
        params: 分类表字段更新参数
    """
    from db.module3_order.classified_fields_data import \
        ClassifiedFieldsUpdateParams

    cursor = params.cursor
    order_data = params.order_data
    new_order_id = params.new_order_id
    new_date_str = params.new_date_str
    new_weekday_group = params.new_weekday_group
    new_customer = params.new_customer
    new_amount = params.new_amount
    new_state = params.new_state
    updated_at = params.updated_at
    all_classified_tables = _get_classified_table_names(order_data)

    for table_name in all_classified_tables:
        _ensure_classified_table_exists(cursor, table_name)
        cursor.execute(
            f"""
            UPDATE {table_name}  # nosec B608
            SET date = ?, weekday_group = ?, customer = ?, amount = ?, state = ?, updated_at = ?
            WHERE order_id = ?
            """,
            (
                new_date_str,
                new_weekday_group,
                new_customer,
                new_amount,
                new_state,
                updated_at,
                new_order_id,
            ),
        )
