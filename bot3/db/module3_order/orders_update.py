"""订单更新操作模块

包含订单的更新功能。
"""

# 标准库
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple

# 本地模块
from db.base import db_transaction
from db.module3_order.orders_basic import (
    _ensure_classified_table_exists, _get_classified_table_names,
    _insert_order_to_classified_table_sync)
from utils.cache import invalidate_cache
from utils.chat_helpers import get_weekday_group_from_date

# 日志
logger = logging.getLogger(__name__)


@db_transaction
def update_order_amount(conn, cursor, chat_id: int, new_amount: float) -> bool:
    """更新订单金额"""
    cursor.execute(
        """
    UPDATE orders
    SET amount = ?, updated_at = CURRENT_TIMESTAMP
    WHERE chat_id = ? AND state NOT IN (?, ?)
    """,
        (new_amount, chat_id, "end", "breach_end"),
    )
    return cursor.rowcount > 0


@db_transaction
def _get_order_and_state(cursor, chat_id: int) -> tuple[Optional[dict], Optional[str]]:
    """获取订单信息和当前状态

    Args:
        cursor: 数据库游标
        chat_id: 群组ID

    Returns:
        (订单字典, 当前状态)，如果订单不存在则返回(None, None)
    """
    cursor.execute("SELECT * FROM orders WHERE chat_id = ?", (chat_id,))
    order_row = cursor.fetchone()
    if not order_row:
        return None, None

    order = dict(order_row)
    return order, order["state"]


def _update_main_table_state(cursor, chat_id: int, new_state: str) -> bool:
    """更新主表订单状态

    Args:
        cursor: 数据库游标
        chat_id: 群组ID
        new_state: 新状态

    Returns:
        是否成功
    """
    cursor.execute(
        """
    UPDATE orders
    SET state = ?, updated_at = CURRENT_TIMESTAMP
    WHERE chat_id = ?
    """,
        (new_state, chat_id),
    )
    return cursor.rowcount > 0


def _sync_classified_tables(
    cursor, order: dict, old_state: str, new_state: str
) -> None:
    """同步更新分类表

    Args:
        cursor: 数据库游标
        order: 订单字典
        old_state: 旧状态
        new_state: 新状态
    """
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
            f"DELETE FROM {old_state_table} WHERE chat_id = ?", (order["chat_id"],)
        )  # nosec B608

    if new_state_table:
        _ensure_classified_table_exists(cursor, new_state_table)
        updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _insert_order_to_classified_table_sync(
            cursor,
            new_state_table,
            order,
            order.get("created_at", updated_at),
            updated_at,
        )


def update_order_state(conn, cursor, chat_id: int, new_state: str) -> bool:
    """更新订单状态，并同步更新分类表

    此函数会：
    1. 更新主表订单状态
    2. 从旧状态分类表移除订单
    3. 将订单添加到新状态分类表
    """
    order, old_state = _get_order_and_state(cursor, chat_id)
    if order is None:
        return False

    if old_state == new_state:
        return True

    if not _update_main_table_state(cursor, chat_id, new_state):
        return False

    _sync_classified_tables(cursor, order, old_state, new_state)

    try:
        invalidate_cache("order_")
        invalidate_cache("financial_")
    except Exception:
        pass

    return True


@db_transaction
def update_order_group_id(conn, cursor, chat_id: int, new_group_id: str) -> bool:
    """更新订单归属ID"""
    cursor.execute(
        """
    UPDATE orders
    SET group_id = ?, updated_at = CURRENT_TIMESTAMP
    WHERE chat_id = ?
    """,
        (new_group_id, chat_id),
    )
    return cursor.rowcount > 0


@db_transaction
def update_order_weekday_group(
    conn, cursor, chat_id: int, new_weekday_group: str
) -> bool:
    """更新订单星期分组"""
    cursor.execute(
        """
    UPDATE orders
    SET weekday_group = ?, updated_at = CURRENT_TIMESTAMP
    WHERE chat_id = ?
    """,
        (new_weekday_group, chat_id),
    )
    rowcount = cursor.rowcount
    if rowcount > 0:
        logger.debug(
            f"更新订单星期分组: chat_id={chat_id}, weekday_group={new_weekday_group}, rowcount={rowcount}"
        )
    return rowcount > 0


@db_transaction
def update_order_date(conn, cursor, chat_id: int, new_date: str) -> bool:
    """更新订单日期"""
    cursor.execute(
        """
    UPDATE orders
    SET date = ?, updated_at = CURRENT_TIMESTAMP
    WHERE chat_id = ?
    """,
        (new_date, chat_id),
    )
    return cursor.rowcount > 0


@db_transaction
def update_order_chat_id(conn, cursor, order_id: str, new_chat_id: int) -> bool:
    """更新订单的chat_id（主表和所有分类表）"""
    try:
        # 1. 获取订单当前信息
        cursor.execute(
            "SELECT chat_id, state FROM orders WHERE order_id = ?", (order_id,)
        )
        order_row = cursor.fetchone()
        if not order_row:
            logger.warning(f"订单 {order_id} 不存在")
            return False

        old_chat_id = order_row["chat_id"]
        state = order_row["state"]

        # 如果chat_id已经匹配，跳过
        if old_chat_id == new_chat_id:
            logger.debug(f"订单 {order_id} 的chat_id已经是 {new_chat_id}，跳过")
            return True

        # 2. 更新主表
        cursor.execute(
            "UPDATE orders SET chat_id = ?, updated_at = CURRENT_TIMESTAMP WHERE order_id = ?",
            (new_chat_id, order_id),
        )

        if cursor.rowcount == 0:
            return False

        # 3. 更新分类表
        state_table_map = {
            "normal": "orders_normal",
            "overdue": "orders_overdue",
            "breach": "orders_breach",
            "end": "orders_end",
            "breach_end": "orders_breach_end",
        }

        state_table = state_table_map.get(state)
        if state_table:
            _ensure_classified_table_exists(cursor, state_table)
            cursor.execute(
                f"UPDATE {state_table} SET chat_id = ? WHERE order_id = ?",  # nosec B608
                (new_chat_id, order_id),
            )

        logger.debug(
            f"✅ 成功更新订单 {order_id} 的chat_id: {old_chat_id} -> {new_chat_id}"
        )
        return True

    except Exception as e:
        logger.error(f"更新订单 {order_id} 的chat_id失败: {e}", exc_info=True)
        return False


@db_transaction
def update_order_from_parsed_info(
    conn, cursor, chat_id: int, parsed_info: Dict
) -> bool:
    """根据群名解析的信息更新订单（主表和所有分类表）"""
    from db.module3_order.orders_update_classified import \
        update_classified_tables
    from db.module3_order.orders_update_fetch import fetch_existing_order
    from db.module3_order.orders_update_main import update_main_table
    from db.module3_order.orders_update_prepare import prepare_new_order_data

    try:
        # 1. 获取现有订单信息
        success, old_order = fetch_existing_order(cursor, chat_id)
        if not success or not old_order:
            return False

        old_order_id = old_order["order_id"]
        old_state = old_order["state"]

        # 2. 准备新订单数据
        new_order_data = prepare_new_order_data(parsed_info, old_order)
        updated_at = new_order_data["updated_at"]

        # 3. 更新主表
        if not update_main_table(cursor, chat_id, new_order_data):
            return False

        # 4. 处理分类表更新
        update_classified_tables(cursor, old_order, new_order_data, updated_at)

        new_order_id = new_order_data["order_id"]
        new_state = new_order_data["state"]
        logger.info(
            f"✅ 成功更新订单: chat_id={chat_id}, order_id={old_order_id} -> {new_order_id}, "
            f"state={old_state} -> {new_state}"
        )
        return True

    except Exception as e:
        logger.error(f"更新订单失败（chat_id: {chat_id}）: {e}", exc_info=True)
        return False
