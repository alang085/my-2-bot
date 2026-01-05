"""
增量订单查询模块

包含增量订单的查询和详细信息组装功能。
"""

# 标准库
import logging
from typing import Dict, List

# 本地模块
from db.base import db_query

# 日志
logger = logging.getLogger(__name__)


@db_query
def _fetch_incremental_orders(cursor, baseline_date: str) -> List[Dict]:
    """获取增量订单"""
    cursor.execute(
        """
    SELECT * FROM orders
    WHERE date >= ? OR updated_at >= ?
    ORDER BY date ASC, order_id ASC
    """,
        (baseline_date, f"{baseline_date} 00:00:00"),
    )
    order_rows = cursor.fetchall()
    return [dict(row) for row in order_rows]


def _fetch_interest_records(cursor, order_ids: List[str], baseline_date: str):
    """批量获取利息记录"""
    if not order_ids:
        return []
    placeholders = ",".join(["?"] * len(order_ids))
    cursor.execute(
        f"""
    SELECT * FROM income_records
    WHERE order_id IN ({placeholders}) AND type = 'interest' AND date >= ?
    AND (is_undone IS NULL OR is_undone = 0)
    ORDER BY order_id, date ASC, created_at ASC
    """,
        order_ids + [baseline_date],
    )
    return cursor.fetchall()


def _fetch_principal_records(cursor, order_ids: List[str], baseline_date: str):
    """批量获取本金归还记录"""
    if not order_ids:
        return []
    placeholders = ",".join(["?"] * len(order_ids))
    cursor.execute(
        f"""
    SELECT order_id, SUM(amount) as total_principal_reduction
    FROM income_records
    WHERE order_id IN ({placeholders}) AND type = 'principal_reduction' AND date >= ?
    AND (is_undone IS NULL OR is_undone = 0)
    GROUP BY order_id
    """,
        order_ids + [baseline_date],
    )
    return cursor.fetchall()


def _build_interests_map(interest_rows) -> Dict[str, List[Dict]]:
    """构建利息映射表"""
    interests_map = {}
    for row in interest_rows:
        order_id = row["order_id"]
        if order_id not in interests_map:
            interests_map[order_id] = []
        interests_map[order_id].append(dict(row))
    return interests_map


def _build_principal_map(principal_rows) -> Dict[str, float]:
    """构建本金归还映射表"""
    return {row[0]: (row[1] if row[1] else 0.0) for row in principal_rows}


def _generate_order_note(
    order: Dict, baseline_date: str, principal_reduction: float
) -> str:
    """生成订单备注"""
    note_parts = []
    if order.get("created_at", "")[:10] >= baseline_date:
        note_parts.append("新订单")
    if principal_reduction > 0:
        note_parts.append(f"归还本金 {principal_reduction:.2f}元")
    if order["state"] == "end":
        note_parts.append("订单完成")
    elif order["state"] == "breach_end":
        note_parts.append("违约完成")
    return "→".join(note_parts) if note_parts else ""


def _assemble_order_details(
    orders: List[Dict],
    interests_map: Dict[str, List[Dict]],
    principal_map: Dict[str, float],
    baseline_date: str,
) -> List[Dict]:
    """组装订单详细信息"""
    result = []
    for order in orders:
        order_id = order["order_id"]
        interests = interests_map.get(order_id, [])
        principal_reduction = principal_map.get(order_id, 0.0)
        total_interest = sum(i["amount"] for i in interests)
        note = _generate_order_note(order, baseline_date, principal_reduction)

        result.append(
            {
                **order,
                "interests": interests,
                "total_interest": total_interest,
                "principal_reduction": principal_reduction,
                "note": note,
            }
        )
    return result


def get_incremental_orders_with_details(conn, cursor, baseline_date: str) -> List[Dict]:
    """获取增量订单及其详细信息（优化批量查询）"""
    orders = _fetch_incremental_orders(cursor, baseline_date)
    if not orders:
        return []

    order_ids = [order["order_id"] for order in orders]
    interest_rows = _fetch_interest_records(cursor, order_ids, baseline_date)
    principal_rows = _fetch_principal_records(cursor, order_ids, baseline_date)

    interests_map = _build_interests_map(interest_rows)
    principal_map = _build_principal_map(principal_rows)

    return _assemble_order_details(orders, interests_map, principal_map, baseline_date)
