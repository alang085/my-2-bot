"""日结数据更新 - 更新模块

包含更新日结数据的逻辑。
"""

import logging
import sqlite3
from typing import Optional

logger = logging.getLogger(__name__)


def get_current_daily_value(
    cursor: sqlite3.Cursor, date: str, field: str, group_id: Optional[str]
) -> float:
    """获取当前日结数据字段值

    Args:
        cursor: 数据库游标
        date: 日期
        field: 字段名
        group_id: 归属ID

    Returns:
        float: 当前字段值
    """
    if group_id:
        cursor.execute(
            "SELECT * FROM daily_data WHERE date = ? AND group_id = ?", (date, group_id)
        )
    else:
        cursor.execute(
            "SELECT * FROM daily_data WHERE date = ? AND group_id IS NULL", (date,)
        )

    row = cursor.fetchone()

    if not row:
        return 0.0

    row_dict = dict(row)
    return row_dict.get(field, 0)


def update_daily_field(
    cursor: sqlite3.Cursor,
    date: str,
    field: str,
    new_value: float,
    group_id: Optional[str],
) -> bool:
    """更新日结数据字段

    Args:
        cursor: 数据库游标
        date: 日期
        field: 字段名
        new_value: 新值
        group_id: 归属ID

    Returns:
        bool: 是否成功
    """
    if group_id:
        cursor.execute(
            f"""
        UPDATE daily_data
        SET "{field}" = ?, updated_at = CURRENT_TIMESTAMP
        WHERE date = ? AND group_id = ?
        """,
            (new_value, date, group_id),
        )
    else:
        cursor.execute(
            f"""
        UPDATE daily_data
        SET "{field}" = ?, updated_at = CURRENT_TIMESTAMP
        WHERE date = ? AND group_id IS NULL
        """,
            (new_value, date),
        )

    if cursor.rowcount == 0:
        logger.warning(
            f"更新日结数据失败: date={date}, group_id={group_id}, "
            f"field={field}, new_value={new_value}, rowcount=0"
        )
        return False

    logger.debug(f"日结数据已更新: {date} {group_id or '全局'} {field} = {new_value}")
    return True
