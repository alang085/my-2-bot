"""订单删除操作模块

包含订单的删除功能。
"""

# 本地模块
from db.base import db_transaction
from db.module3_order.orders_basic import (_ensure_classified_table_exists,
                                           _get_classified_table_names)


@db_transaction
def delete_order_by_chat_id(conn, cursor, chat_id: int) -> bool:
    """删除订单（用于撤销订单创建）

    此函数会：
    1. 删除主表订单
    2. 删除所有分类表中的订单数据
    """
    # 1. 先获取订单信息，以便删除分类表数据
    cursor.execute("SELECT * FROM orders WHERE chat_id = ?", (chat_id,))
    order_row = cursor.fetchone()
    if not order_row:
        return False

    order = dict(order_row)
    order_id = order.get("order_id")

    # 2. 获取所有相关分类表名
    classified_tables = _get_classified_table_names(order)

    # 3. 从所有分类表删除订单数据
    for table_name in classified_tables:
        _ensure_classified_table_exists(cursor, table_name)
        cursor.execute(
            f"DELETE FROM {table_name} WHERE order_id = ?", (order_id,)
        )  # nosec B608

    # 4. 删除主表订单
    cursor.execute("DELETE FROM orders WHERE chat_id = ?", (chat_id,))
    return cursor.rowcount > 0


@db_transaction
def delete_order_by_order_id(conn, cursor, order_id: str) -> bool:
    """根据订单ID删除订单

    此函数会：
    1. 删除主表订单
    2. 删除所有分类表中的订单数据
    """
    # 1. 先获取订单信息，以便删除分类表数据
    cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
    order_row = cursor.fetchone()
    if not order_row:
        return False

    order = dict(order_row)

    # 2. 获取所有相关分类表名
    classified_tables = _get_classified_table_names(order)

    # 3. 从所有分类表删除订单数据
    for table_name in classified_tables:
        _ensure_classified_table_exists(cursor, table_name)
        cursor.execute(
            f"DELETE FROM {table_name} WHERE order_id = ?", (order_id,)
        )  # nosec B608

    # 4. 删除主表订单
    cursor.execute("DELETE FROM orders WHERE order_id = ?", (order_id,))
    return cursor.rowcount > 0
