"""客户价值数据库操作"""

import logging
from typing import Any, Dict, List, Optional

from db.base import db_query, db_transaction

logger = logging.getLogger(__name__)


async def create_value_record(customer_id: str) -> bool:
    """创建客户价值记录"""
    query = """
        INSERT INTO customer_value (
            customer_id, total_borrowed, total_interest_paid, total_profit,
            order_count, completed_order_count, average_order_amount
        ) VALUES (?, 0, 0, 0, 0, 0, 0)
    """
    return await execute_transaction(query, (customer_id,))


async def get_value_by_customer_id(customer_id: str) -> Optional[dict[str, Any]]:
    """根据客户ID获取价值记录"""
    result = await execute_query(
        "SELECT * FROM customer_value WHERE customer_id = ? LIMIT 1",
        (customer_id,),
        fetch_one=True,
    )
    if result and isinstance(result, dict):
        return result
    return None


async def update_value_on_order(
    customer_id: str, order_amount: float, is_completed: bool = False
) -> bool:
    """订单时更新价值"""
    value = await get_value_by_customer_id(customer_id)
    if not value:
        await create_value_record(customer_id)
        value = await get_value_by_customer_id(customer_id)

    if not value:
        return False

    new_total_borrowed = value["total_borrowed"] + order_amount
    new_order_count = value["order_count"] + 1
    new_completed_count = (
        value["completed_order_count"] + 1
        if is_completed
        else value["completed_order_count"]
    )
    new_avg = new_total_borrowed / new_order_count if new_order_count > 0 else 0

    query = """
        UPDATE customer_value 
        SET total_borrowed = ?, order_count = ?, completed_order_count = ?,
            average_order_amount = ?, last_calculated = CURRENT_TIMESTAMP 
        WHERE customer_id = ?
    """
    return await execute_transaction(
        query,
        (
            new_total_borrowed,
            new_order_count,
            new_completed_count,
            new_avg,
            customer_id,
        ),
    )


async def update_value_on_payment(customer_id: str, interest_amount: float) -> bool:
    """付息时更新价值"""
    value = await get_value_by_customer_id(customer_id)
    if not value:
        await create_value_record(customer_id)
        value = await get_value_by_customer_id(customer_id)

    if not value:
        return False

    new_interest_paid = value["total_interest_paid"] + interest_amount
    new_profit = new_interest_paid  # 简化：利润 = 总付息（可后续优化）

    query = """
        UPDATE customer_value 
        SET total_interest_paid = ?, total_profit = ?, last_calculated = CURRENT_TIMESTAMP 
        WHERE customer_id = ?
    """
    return await execute_transaction(
        query, (new_interest_paid, new_profit, customer_id)
    )


async def _calculate_order_statistics(orders: List[Dict]) -> Dict[str, Any]:
    """计算订单统计信息

    Args:
        orders: 订单列表

    Returns:
        统计信息字典
    """
    total_borrowed = sum(order["amount"] for order in orders)
    completed_count = sum(1 for order in orders if order["state"] == "end")
    order_count = len(orders)
    avg_amount = total_borrowed / order_count if order_count > 0 else 0

    return {
        "total_borrowed": total_borrowed,
        "completed_count": completed_count,
        "order_count": order_count,
        "avg_amount": avg_amount,
    }


async def _calculate_interest_statistics(orders: List[Dict]) -> float:
    """计算利息统计

    Args:
        orders: 订单列表

    Returns:
        总利息金额
    """
    order_ids = [order.get("order_id") for order in orders if order.get("order_id")]
    if not order_ids:
        return 0.0

    placeholders = ",".join("?" * len(order_ids))
    income_query = f"""
        SELECT amount FROM income_records 
        WHERE order_id IN ({placeholders}) AND type = 'interest'
    """
    income_records = (
        await execute_query(income_query, tuple(order_ids), fetch_all=True) or []
    )
    return sum(record["amount"] for record in income_records)


async def _update_customer_value_in_db(
    customer_id: str, stats: Dict[str, Any], total_interest_paid: float
) -> bool:
    """更新数据库中的客户价值

    Args:
        customer_id: 客户ID
        stats: 统计信息字典
        total_interest_paid: 总利息金额

    Returns:
        是否成功
    """
    query = """
        UPDATE customer_value 
        SET total_borrowed = ?, total_interest_paid = ?, total_profit = ?,
            order_count = ?, completed_order_count = ?, average_order_amount = ?,
            last_calculated = CURRENT_TIMESTAMP 
        WHERE customer_id = ?
    """
    return await execute_transaction(
        query,
        (
            stats["total_borrowed"],
            total_interest_paid,
            total_interest_paid,
            stats["order_count"],
            stats["completed_count"],
            stats["avg_amount"],
            customer_id,
        ),
    )


async def calculate_customer_value(customer_id: str) -> Optional[dict]:
    """计算客户价值（重新计算）"""
    orders = (
        await execute_query(
            "SELECT amount, state FROM orders WHERE customer_id = ?",
            (customer_id,),
            fetch_all=True,
        )
        or []
    )

    stats = await _calculate_order_statistics(orders)
    total_interest_paid = await _calculate_interest_statistics(orders)

    success = await _update_customer_value_in_db(
        customer_id, stats, total_interest_paid
    )

    if success:
        return {
            "total_borrowed": stats["total_borrowed"],
            "total_interest_paid": total_interest_paid,
            "total_profit": total_interest_paid,
            "order_count": stats["order_count"],
            "completed_order_count": stats["completed_count"],
            "average_order_amount": stats["avg_amount"],
        }
    return None


async def get_top_customers(
    min_score: Optional[int] = None,
    min_profit: Optional[float] = None,
    min_orders: Optional[int] = None,
    limit: int = 20,
) -> list[dict]:
    """获取优质客户列表"""
    conditions = []
    params = []

    if min_score is not None:
        conditions.append("cc.credit_score >= ?")
        params.append(min_score)

    if min_profit is not None:
        conditions.append("cv.total_profit >= ?")
        params.append(min_profit)

    if min_orders is not None:
        conditions.append("cv.completed_order_count >= ?")
        params.append(min_orders)

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    query = f"""
        SELECT cp.*, cc.credit_score, cc.credit_level, cv.total_profit,
               cv.completed_order_count 
        FROM customer_profiles cp
        LEFT JOIN customer_credit cc ON cp.customer_id = cc.customer_id
        LEFT JOIN customer_value cv ON cp.customer_id = cv.customer_id
        WHERE {where_clause}
        ORDER BY cv.total_profit DESC, cc.credit_score DESC
        LIMIT ?
    """
    params.append(limit)

    return await execute_query(query, tuple(params), fetch_all=True) or []
