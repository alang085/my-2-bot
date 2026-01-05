"""
基准报表操作模块

包含基准报表的查询和保存功能。
"""

# 标准库
import logging
from typing import List, Optional

# 本地模块
from db.base import db_query, db_transaction

# 日志
logger = logging.getLogger(__name__)


@db_query
def check_baseline_exists(conn, cursor) -> bool:
    """检查基准日期是否存在"""
    cursor.execute("SELECT COUNT(*) FROM baseline_report WHERE id = 1")
    count = cursor.fetchone()[0]
    return count > 0


@db_query
def get_baseline_date(conn, cursor) -> Optional[str]:
    """获取基准日期"""
    cursor.execute("SELECT baseline_date FROM baseline_report WHERE id = 1")
    row = cursor.fetchone()
    return row[0] if row else None


@db_transaction
def save_baseline_date(conn, cursor, date: str) -> bool:
    """保存基准日期（第一次执行时）"""
    try:
        # 检查是否已存在
        cursor.execute("SELECT COUNT(*) FROM baseline_report WHERE id = 1")
        exists = cursor.fetchone()[0] > 0

        if exists:
            # 更新
            cursor.execute(
                """
            UPDATE baseline_report
            SET baseline_date = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
            """,
                (date,),
            )
        else:
            # 插入
            cursor.execute(
                """
            INSERT INTO baseline_report (id, baseline_date)
            VALUES (1, ?)
            """,
                (date,),
            )
        return True
    except Exception as e:
        logger.error(f"保存基准日期失败: {e}", exc_info=True)
        return False


@db_query
def get_incremental_orders(conn, cursor, baseline_date: str) -> List[dict]:
    """获取基准日期之后的所有订单（创建或更新）"""
    cursor.execute(
        """
    SELECT * FROM orders
    WHERE date >= ? OR updated_at >= ?
    ORDER BY date ASC, order_id ASC
    """,
        (baseline_date, f"{baseline_date} 00:00:00"),
    )
    rows = cursor.fetchall()
    return [dict(row) for row in rows]
