"""
操作历史查询模块

包含操作历史的查询和更新功能。
"""

# 标准库
import json
import logging
from typing import Dict, List, Optional

# 本地模块
from db.base import db_query, db_transaction

# 日志
logger = logging.getLogger(__name__)


def _build_filter_conditions(
    date: Optional[str] = None,
    user_id: Optional[int] = None,
    operation_type: Optional[str] = None,
) -> tuple[str, List]:
    """构建筛选条件

    Args:
        date: 日期字符串
        user_id: 用户ID
        operation_type: 操作类型

    Returns:
        (WHERE子句, 参数列表)
    """
    conditions = []
    params = []

    if date:
        conditions.append("DATE(created_at) = ?")
        params.append(date)

    if user_id:
        conditions.append("user_id = ?")
        params.append(user_id)

    if operation_type:
        conditions.append("operation_type = ?")
        params.append(operation_type)

    where_clause = " AND ".join(conditions) if conditions else "1=1"
    return where_clause, params


def _parse_operation_data(rows: List) -> List[Dict]:
    """解析操作数据

    Args:
        rows: 查询结果行

    Returns:
        操作历史列表
    """
    result = []
    for row in rows:
        op = dict(row)
        try:
            op["operation_data"] = json.loads(op["operation_data"])
        except (json.JSONDecodeError, TypeError):
            op["operation_data"] = {}
        result.append(op)
    return result


def get_operations_by_filters(
    conn,
    cursor,
    date: Optional[str] = None,
    user_id: Optional[int] = None,
    operation_type: Optional[str] = None,
    limit: int = 100,
) -> List[Dict]:
    """根据多个条件筛选操作历史

    Args:
        date: 日期字符串，格式 'YYYY-MM-DD'，可选
        user_id: 用户ID，可选
        operation_type: 操作类型，可选
        limit: 返回的最大记录数

    Returns:
        操作历史列表
    """
    where_clause, params = _build_filter_conditions(date, user_id, operation_type)
    params.append(limit)

    query = f"""
    SELECT * FROM operation_history
    WHERE {where_clause}
    ORDER BY created_at DESC, id DESC
    LIMIT ?
    """

    cursor.execute(query, params)
    rows = cursor.fetchall()
    return _parse_operation_data(rows)


@db_transaction
def update_operation_data(
    conn, cursor, operation_id: int, new_operation_data: Dict
) -> bool:
    """更新操作记录的数据（用于管理员修正）

    Args:
        operation_id: 操作记录ID
        new_operation_data: 新的操作数据字典

    Returns:
        是否更新成功
    """
    cursor.execute(
        """
    UPDATE operation_history
    SET operation_data = ?
    WHERE id = ?
    """,
        (json.dumps(new_operation_data, ensure_ascii=False), operation_id),
    )
    return cursor.rowcount > 0
