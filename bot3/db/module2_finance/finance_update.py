"""财务数据更新 - 更新模块

包含更新财务数据的逻辑。
"""

import logging
import sqlite3

logger = logging.getLogger(__name__)


def get_current_field_value(cursor: sqlite3.Cursor, field: str) -> float:
    """获取当前字段值

    Args:
        cursor: 数据库游标
        field: 字段名

    Returns:
        float: 当前字段值
    """
    cursor.execute("SELECT * FROM financial_data ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()

    if not row:
        return 0.0

    row_dict = dict(row)
    # 检查字段是否存在（兼容旧数据库，如overdue_orders/overdue_amount）
    if field not in row_dict:
        logger.warning(f"字段 {field} 不存在于 financial_data 表中（兼容旧数据库）")
        return 0.0

    return row_dict.get(field, 0)


def update_financial_field(
    cursor: sqlite3.Cursor, field: str, new_value: float
) -> bool:
    """更新财务数据字段

    Args:
        cursor: 数据库游标
        field: 字段名
        new_value: 新值

    Returns:
        bool: 是否成功
    """
    cursor.execute(
        f"""
    UPDATE financial_data
    SET "{field}" = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = (SELECT id FROM financial_data ORDER BY id DESC LIMIT 1)
    """,
        (new_value,),
    )

    if cursor.rowcount == 0:
        logger.warning(
            f"更新财务数据失败: field={field}, new_value={new_value}, rowcount=0"
        )
        return False

    logger.debug(f"财务数据已更新: {field} = {new_value}")
    return True
