"""报表搜索 - 结果显示模块

包含显示搜索结果的逻辑。
"""

from typing import Dict, List, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

import db_operations


async def _search_orders_by_criteria(criteria: dict) -> List[Dict]:
    """根据条件搜索订单

    Args:
        criteria: 搜索条件

    Returns:
        订单列表
    """
    if "state" in criteria and criteria["state"]:
        return await db_operations.search_orders_advanced_all_states(criteria)
    else:
        return await db_operations.search_orders_advanced(criteria)


def _calculate_search_statistics(orders: List[Dict]) -> Tuple[int, float, List[int]]:
    """计算搜索统计信息

    Args:
        orders: 订单列表

    Returns:
        (订单数量, 总金额, 锁定的群组列表)
    """
    order_count = len(orders)
    total_amount = sum(order.get("amount", 0) for order in orders)
    locked_groups = list(set(order["chat_id"] for order in orders))
    return order_count, total_amount, locked_groups


def _build_search_result_message(
    order_count: int, total_amount: float, group_count: int
) -> str:
    """构建搜索结果消息

    Args:
        order_count: 订单数量
        total_amount: 总金额
        group_count: 群组数量

    Returns:
        结果消息文本
    """
    return (
        f"📊 查找结果\n\n"
        f"订单数量: {order_count}\n"
        f"订单金额: {total_amount:,.2f}\n"
        f"群组数量: {group_count}"
    )


def _build_search_result_keyboard() -> InlineKeyboardMarkup:
    """构建搜索结果键盘

    Returns:
        内联键盘
    """
    keyboard = [
        [
            InlineKeyboardButton("📢 群发消息", callback_data="broadcast_start"),
            InlineKeyboardButton(
                "🔄 修改归属", callback_data="report_change_attribution"
            ),
        ],
        [InlineKeyboardButton("🔙 返回", callback_data="report_menu_attribution")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def display_search_results(
    update: Update, context: ContextTypes.DEFAULT_TYPE, criteria: dict
) -> None:
    """显示搜索结果

    Args:
        update: Telegram更新对象
        context: 上下文对象
        criteria: 搜索条件
    """
    orders = await _search_orders_by_criteria(criteria)

    if not orders:
        await update.message.reply_text("❌ 未找到匹配的订单")
        context.user_data["state"] = None
        return

    order_count, total_amount, locked_groups = _calculate_search_statistics(orders)
    context.user_data["locked_groups"] = locked_groups
    context.user_data["report_search_orders"] = orders

    result_msg = _build_search_result_message(
        order_count, total_amount, len(locked_groups)
    )
    reply_markup = _build_search_result_keyboard()

    await update.message.reply_text(result_msg, reply_markup=reply_markup)
    context.user_data["state"] = None
