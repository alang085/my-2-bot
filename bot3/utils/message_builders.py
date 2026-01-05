"""消息构建工具类（兼容层）

此模块已拆分为多个子模块，保留此文件以保持向后兼容。
所有函数和类都从相应的子模块导入。
"""

from typing import Dict, List, Optional, Tuple

from telegram import Update

from constants import TELEGRAM_MESSAGE_MAX_LENGTH, TELEGRAM_MESSAGE_SAFE_LENGTH
from utils.chat_helpers import is_group_chat
from utils.message_builder_class import MessageBuilder


def _get_historical_order_metadata(is_historical: bool) -> Tuple[str, str, str]:
    """获取历史订单元数据

    Args:
        is_historical: 是否为历史订单

    Returns:
        (标题, 客户后缀, 页脚)
    """
    if is_historical:
        return (
            "✅ Historical Order Imported",
            " (Historical)",
            "\n⚠️ Funds Update: Skipped (Historical Data Only)\n"
            "📢 Broadcast: Skipped (Historical Data Only)",
        )
    else:
        return ("✅ Order Created Successfully", "", "")


def _build_order_message_header(
    title: str,
    order_id: str,
    group_id: str,
    created_at: str,
    weekday_group: Optional[str],
    is_historical: bool,
) -> str:
    """构建订单消息头部

    Args:
        title: 标题
        order_id: 订单ID
        group_id: 归属ID
        created_at: 创建时间
        weekday_group: 星期分组
        is_historical: 是否为历史订单

    Returns:
        消息头部文本
    """
    message = (
        f"{title}\n\n"
        f"📋 Order ID: {order_id}\n"
        f"🏷️ Group ID: {group_id}\n"
        f"📅 Date: {created_at}\n"
    )

    if weekday_group and not is_historical:
        message += f"👥 Week Group: {weekday_group}\n"

    return message


def _build_order_message_body(
    customer: str, customer_suffix: str, amount: float, initial_state: str, footer: str
) -> str:
    """构建订单消息主体

    Args:
        customer: 客户类型
        customer_suffix: 客户后缀
        amount: 订单金额
        initial_state: 初始状态
        footer: 页脚

    Returns:
        消息主体文本
    """
    customer_name = "New" if customer == "A" else "Returning"
    return (
        f"👤 Customer: {customer_name}{customer_suffix}\n"
        f"💰 Amount: {amount:.2f}\n"
        f"📈 Status: {initial_state}"
        f"{footer}"
    )


def build_order_creation_message(params: "OrderCreationMessageParams") -> str:
    """
    构建订单创建成功消息

    Args:
        params: 订单创建消息参数

    Returns:
        格式化后的消息字符串
    """
    from utils.order_message_data import OrderCreationMessageParams

    order_id = params.order_id
    group_id = params.group_id
    created_at = params.created_at
    weekday_group = params.weekday_group
    customer = params.customer
    amount = params.amount
    initial_state = params.initial_state
    is_historical = params.is_historical
    title, customer_suffix, footer = _get_historical_order_metadata(is_historical)
    header = _build_order_message_header(
        title, order_id, group_id, created_at, weekday_group, is_historical
    )
    body = _build_order_message_body(
        customer, customer_suffix, amount, initial_state, footer
    )
    return header + body
