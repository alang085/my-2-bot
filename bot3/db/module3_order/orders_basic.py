"""订单基础操作模块

包含订单的创建和分类表管理功能。
"""

# 标准库
import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Tuple

# 本地模块
from db.base import db_transaction
from utils.models import OrderCreateModel, validate_amount

# 日志
logger = logging.getLogger(__name__)


def _validate_table_name(table_name: str) -> bool:
    """验证表名是否安全（防止SQL注入）

    Args:
        table_name: 表名

    Returns:
        bool: 如果表名安全返回True，否则返回False
    """
    # 允许的表名前缀白名单
    allowed_prefixes = [
        "orders_normal",
        "orders_overdue",
        "orders_breach",
        "orders_end",
        "orders_breach_end",
        "orders_new_customers",
        "orders_old_customers",
        "orders_monday",
        "orders_tuesday",
        "orders_wednesday",
        "orders_thursday",
        "orders_friday",
        "orders_saturday",
        "orders_sunday",
    ]

    # 检查是否是白名单中的表名
    if table_name in allowed_prefixes:
        return True

    # 检查是否是归属ID表（orders_S01, orders_S02等）
    if table_name.startswith("orders_") and len(table_name) > 7:
        suffix = table_name[7:]  # 去掉 "orders_" 前缀
        # 验证后缀只包含字母和数字
        if suffix.replace("_", "").isalnum():
            return True

    return False


def _ensure_classified_table_exists(cursor, table_name: str) -> None:
    """确保分类表存在，如果不存在则创建"""
    # 验证表名安全性
    if not _validate_table_name(table_name):
        raise ValueError(f"不安全的表名: {table_name}")

    # 检查表是否存在
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    if cursor.fetchone():
        return  # 表已存在

    # 创建表（表名已通过_validate_table_name验证）
    schema = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (  # nosec B608
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT UNIQUE NOT NULL,
        group_id TEXT NOT NULL,
        chat_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        weekday_group TEXT NOT NULL,
        customer TEXT NOT NULL,
        amount REAL NOT NULL,
        state TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """
    cursor.execute(schema)

    # 创建索引（表名已通过_validate_table_name验证）
    cursor.execute(
        f"CREATE INDEX IF NOT EXISTS idx_{table_name}_order_id "
        f"ON {table_name}(order_id)"
    )  # nosec B608
    cursor.execute(
        f"CREATE INDEX IF NOT EXISTS idx_{table_name}_chat_id "
        f"ON {table_name}(chat_id)"
    )  # nosec B608
    cursor.execute(
        f"CREATE INDEX IF NOT EXISTS idx_{table_name}_date " f"ON {table_name}(date)"
    )  # nosec B608
    logger.info(f"已动态创建分类表: {table_name}")


def _get_classified_table_names(order_data: Dict) -> List[str]:
    """根据订单属性获取所有相关分类表名"""
    tables = []

    # 状态分类
    state = order_data.get("state", "normal")
    state_table_map = {
        "normal": "orders_normal",
        "overdue": "orders_overdue",
        "breach": "orders_breach",
        "end": "orders_end",
        "breach_end": "orders_breach_end",
    }
    if state in state_table_map:
        tables.append(state_table_map[state])

    # 客户类型分类
    customer = order_data.get("customer", "B")
    if customer == "A":
        tables.append("orders_new_customers")
    else:
        tables.append("orders_old_customers")

    # 星期分组分类
    weekday_group = order_data.get("weekday_group", "一")
    weekday_map = {
        "一": "orders_monday",
        "二": "orders_tuesday",
        "三": "orders_wednesday",
        "四": "orders_thursday",
        "五": "orders_friday",
        "六": "orders_saturday",
        "日": "orders_sunday",
    }
    if weekday_group in weekday_map:
        tables.append(weekday_map[weekday_group])

    # 归属ID分类
    group_id = order_data.get("group_id", "S01")
    tables.append(f"orders_{group_id}")

    return tables


def _insert_order_to_classified_table_sync(
    cursor, table_name: str, order_data: Dict, created_at: str, updated_at: str
) -> bool:
    """同步版本的分类表插入（用于事务中）"""
    try:
        # 确保分类表存在
        _ensure_classified_table_exists(cursor, table_name)

        cursor.execute(
            f"""
        INSERT INTO {table_name} (
            order_id, group_id, chat_id, date, weekday_group,
            customer, amount, state, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                order_data["order_id"],
                order_data["group_id"],
                order_data["chat_id"],
                order_data["date"],
                order_data["weekday_group"],
                order_data["customer"],
                order_data["amount"],
                order_data["state"],
                created_at,
                updated_at,
            ),
        )
        return True
    except sqlite3.IntegrityError as e:
        logger.warning(f"订单插入分类表 {table_name} 失败（重复）: {e}")
        return False
    except sqlite3.OperationalError as e:
        logger.error(f"分类表 {table_name} 操作失败: {e}", exc_info=True)
        return False


@db_transaction
def create_order(conn, cursor, order_data: Dict) -> bool:
    """创建新订单"""
    try:
        # 如果提供了 created_at 和 updated_at，使用提供的值；否则使用当前时间
        created_at = order_data.get("created_at")
        updated_at = order_data.get("updated_at")

        if created_at is None:
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if updated_at is None:
            updated_at = created_at  # 新订单的 updated_at 等于 created_at

        cursor.execute(
            """
        INSERT INTO orders (
            order_id, group_id, chat_id, date, weekday_group,
            customer, amount, state, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                order_data["order_id"],
                order_data["group_id"],
                order_data["chat_id"],
                order_data["date"],
                order_data["weekday_group"],
                order_data["customer"],
                order_data["amount"],
                order_data["state"],
                created_at,
                updated_at,
            ),
        )
        # 清除相关缓存（延迟导入以避免循环导入）
        try:
            from utils.cache import invalidate_cache

            invalidate_cache("order_")
            invalidate_cache("financial_")
            invalidate_cache("group_ids_")
        except Exception:
            pass  # 缓存失效失败不影响主流程

        return True
    except sqlite3.IntegrityError as e:
        logger.warning(f"订单创建失败（重复）: {e}")
        return False


@db_transaction
def insert_order_to_classified_table(
    conn, cursor, table_name: str, order_data: Dict
) -> bool:
    """将订单插入到指定的分类表"""
    try:
        # 确保分类表存在（动态创建）
        _ensure_classified_table_exists(cursor, table_name)

        # 如果提供了 created_at 和 updated_at，使用提供的值；否则使用当前时间
        created_at = order_data.get("created_at")
        updated_at = order_data.get("updated_at")

        if created_at is None:
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if updated_at is None:
            updated_at = created_at

        cursor.execute(
            f"""
        INSERT INTO {table_name} (  # nosec B608
            order_id, group_id, chat_id, date, weekday_group,
            customer, amount, state, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                order_data["order_id"],
                order_data["group_id"],
                order_data["chat_id"],
                order_data["date"],
                order_data["weekday_group"],
                order_data["customer"],
                order_data["amount"],
                order_data["state"],
                created_at,
                updated_at,
            ),
        )
        return True
    except sqlite3.IntegrityError as e:
        logger.warning(f"订单插入分类表 {table_name} 失败（重复）: {e}")
        return False
    except sqlite3.OperationalError as e:
        logger.error(f"分类表 {table_name} 操作失败: {e}", exc_info=True)
        return False


@db_transaction
def _validate_order_data(order_data: Dict) -> Dict:
    """验证订单数据

    Args:
        order_data: 订单数据字典

    Returns:
        验证后的订单数据字典

    Raises:
        ValueError: 如果验证失败
    """
    try:
        validated_amount = validate_amount(order_data.get("amount", 0))
        order_data["amount"] = validated_amount

        state = order_data.get("state", "normal")
        valid_states = ("normal", "overdue", "breach", "end", "breach_end")
        if state not in valid_states:
            raise ValueError(f"订单状态必须是 {valid_states} 之一，当前状态: {state}")
        order_data["state"] = state

        order_model = OrderCreateModel(**order_data)
        return order_model.to_dict()
    except ValueError as e:
        logger.error(f"订单数据验证失败: {e}")
        raise
    except Exception as e:
        logger.error(f"订单数据验证出错: {e}", exc_info=True)
        raise ValueError(f"订单数据验证失败: {str(e)}")


def _prepare_timestamps(order_data: Dict) -> tuple[str, str]:
    """准备时间戳

    Args:
        order_data: 订单数据字典

    Returns:
        (created_at, updated_at)
    """
    created_at = order_data.get("created_at")
    updated_at = order_data.get("updated_at")

    if created_at is None:
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if updated_at is None:
        updated_at = created_at

    return created_at, updated_at


def _insert_order_to_main_table(
    cursor, order_data: Dict, created_at: str, updated_at: str
) -> bool:
    """插入订单到主表

    Args:
        cursor: 数据库游标
        order_data: 订单数据字典
        created_at: 创建时间
        updated_at: 更新时间

    Returns:
        是否成功
    """
    try:
        cursor.execute(
            """
            INSERT INTO orders (
                order_id, group_id, chat_id, date, weekday_group,
                customer, amount, state, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_data["order_id"],
                order_data["group_id"],
                order_data["chat_id"],
                order_data["date"],
                order_data["weekday_group"],
                order_data["customer"],
                order_data["amount"],
                order_data["state"],
                created_at,
                updated_at,
            ),
        )
        return True
    except sqlite3.IntegrityError as e:
        logger.warning(f"订单创建失败（重复）: {e}")
        return False


def _insert_order_to_classified_tables(
    cursor, order_data: Dict, created_at: str, updated_at: str
) -> None:
    """插入订单到所有分类表

    Args:
        cursor: 数据库游标
        order_data: 订单数据字典
        created_at: 创建时间
        updated_at: 更新时间
    """
    classified_tables = _get_classified_table_names(order_data)
    for table_name in classified_tables:
        _insert_order_to_classified_table_sync(
            cursor, table_name, order_data, created_at, updated_at
        )


def create_order_in_classified_tables(conn, cursor, order_data: Dict) -> bool:
    """将订单插入主表和所有相关分类表"""
    try:
        order_data = _validate_order_data(order_data)
        created_at, updated_at = _prepare_timestamps(order_data)

        if not _insert_order_to_main_table(cursor, order_data, created_at, updated_at):
            return False

        _insert_order_to_classified_tables(cursor, order_data, created_at, updated_at)
        return True
    except ValueError as e:
        logger.error(f"订单数据验证失败: {e}")
        raise
    except Exception as e:
        logger.error(f"创建订单到分类表失败: {e}", exc_info=True)
        return False


def _prepare_batch_insert_values(
    orders_data: List[Dict], created_at: str, updated_at: str
) -> List[Tuple]:
    """准备批量插入的值列表

    Args:
        orders_data: 订单数据列表
        created_at: 创建时间
        updated_at: 更新时间

    Returns:
        值列表
    """
    return [
        (
            order["order_id"],
            order["group_id"],
            order["chat_id"],
            order["date"],
            order["weekday_group"],
            order["customer"],
            order["amount"],
            order["state"],
            created_at,
            updated_at,
        )
        for order in orders_data
    ]


def _execute_batch_insert_for_table(
    cursor, table_name: str, values: List[Tuple]
) -> None:
    """为单个表执行批量插入

    Args:
        cursor: 数据库游标
        table_name: 表名
        values: 值列表
    """
    _ensure_classified_table_exists(cursor, table_name)

    cursor.executemany(
        f"""
        INSERT OR IGNORE INTO {table_name} (
            order_id, group_id, chat_id, date, weekday_group,
            customer, amount, state, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        values,
    )


def _batch_insert_to_classified_tables(
    cursor,
    table_names: List[str],
    orders_data: List[Dict],
    created_at: str,
    updated_at: str,
) -> bool:
    """
    批量插入订单到分类表（使用executemany优化性能）

    Args:
        cursor: 数据库游标
        table_names: 分类表名列表
        orders_data: 订单数据列表（所有订单应该有相同的分类表）
        created_at: 创建时间
        updated_at: 更新时间

    Returns:
        是否成功
    """
    try:
        values = _prepare_batch_insert_values(orders_data, created_at, updated_at)

        for table_name in table_names:
            _execute_batch_insert_for_table(cursor, table_name, values)

        return True
    except sqlite3.OperationalError as e:
        logger.error(f"批量插入分类表失败: {e}", exc_info=True)
        return False
