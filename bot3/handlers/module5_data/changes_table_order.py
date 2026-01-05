"""每日变更表 - 订单模块

包含生成订单变更相关内容的逻辑。
"""

from constants import MAX_DISPLAY_ITEMS


def build_order_summary(changes: dict) -> str:
    """构建订单变更汇总

    Args:
        changes: 变更数据字典

    Returns:
        str: 订单变更汇总文本
    """
    text = "<b>📦 订单变更汇总</b>\n"
    new_clients_count = changes.get("new_clients_count", 0)
    new_clients_amount = changes.get("new_clients_amount", 0.0)
    text += f"新客户订单: {new_clients_count} 个, {new_clients_amount:,.2f}\n"
    old_clients_count = changes.get("old_clients_count", 0)
    old_clients_amount = changes.get("old_clients_amount", 0.0)
    text += f"老客户订单: {old_clients_count} 个, {old_clients_amount:,.2f}\n"
    completed_count = changes["completed_orders_count"]
    completed_amount = changes["completed_orders_amount"]
    text += f"完成订单: {completed_count} 个, {completed_amount:,.2f}\n"
    breach_count = changes.get("breach_orders_count", 0)
    breach_amount = changes.get("breach_orders_amount", 0.0)
    text += f"违约订单: {breach_count} 个, {breach_amount:,.2f}\n"
    breach_end_count = changes["breach_end_orders_count"]
    breach_end_amount = changes["breach_end_orders_amount"]
    text += f"违约完成: {breach_end_count} 个, {breach_end_amount:,.2f}\n\n"
    return text


def build_new_orders_detail(changes: dict) -> str:
    """构建新增订单明细

    Args:
        changes: 变更数据字典

    Returns:
        str: 新增订单明细文本
    """
    text = ""
    if changes["new_orders"]:
        text += "<b>🆕 新增订单明细</b>\n"
        text += "─" * 40 + "\n"
        for i, order in enumerate(changes["new_orders"][:MAX_DISPLAY_ITEMS], 1):
            order_id = order.get("order_id", "未知")
            customer = order.get("customer", "未知")
            amount = float(order.get("amount", 0) or 0)
            group_name = order.get("group_name", "未知")
            text += f"{i}. {order_id} | {customer} | {amount:,.2f} | {group_name}\n"
        if len(changes["new_orders"]) > MAX_DISPLAY_ITEMS:
            text += f"... 还有 {len(changes['new_orders']) - 10} 个订单\n"
        text += "\n"
    return text


def build_completed_orders_detail(changes: dict) -> str:
    """构建完成订单明细

    Args:
        changes: 变更数据字典

    Returns:
        str: 完成订单明细文本
    """
    text = ""
    if changes["completed_orders"]:
        text += "<b>✅ 完成订单明细</b>\n"
        text += "─" * 40 + "\n"
        for i, order in enumerate(changes["completed_orders"][:10], 1):
            order_id = order.get("order_id", "未知")
            amount = float(order.get("amount", 0) or 0)
            group_name = order.get("group_name", "未知")
            text += f"{i}. {order_id} | {amount:,.2f} | {group_name}\n"
        if len(changes["completed_orders"]) > 10:
            text += f"... 还有 {len(changes['completed_orders']) - 10} 个订单\n"
        text += "\n"
    return text


def build_breach_end_orders_detail(changes: dict) -> str:
    """构建违约完成订单明细

    Args:
        changes: 变更数据字典

    Returns:
        str: 违约完成订单明细文本
    """
    text = ""
    if changes["breach_end_orders"]:
        text += "<b>⚠️ 违约完成订单明细</b>\n"
        text += "─" * 40 + "\n"
        for i, order in enumerate(changes["breach_end_orders"][:10], 1):
            order_id = order.get("order_id", "未知")
            amount = float(order.get("amount", 0) or 0)
            group_name = order.get("group_name", "未知")
            text += f"{i}. {order_id} | {amount:,.2f} | {group_name}\n"
        if len(changes["breach_end_orders"]) > 10:
            text += f"... 还有 {len(changes['breach_end_orders']) - 10} 个订单\n"
        text += "\n"
    return text
