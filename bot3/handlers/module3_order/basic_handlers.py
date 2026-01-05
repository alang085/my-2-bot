"""订单相关命令处理器"""

import logging
from typing import Dict, Optional, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

import db_operations
from decorators import authorized_required, error_handler, group_chat_only
from utils.handler_helpers import get_and_validate_order, get_chat_info
from utils.order_helpers import try_create_order_from_title

logger = logging.getLogger(__name__)


@error_handler
@authorized_required
@group_chat_only
async def create_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """创建新订单 (读取群名)"""
    try:
        chat = update.effective_chat
        if not chat:
            logger.error("Cannot get chat from update")
            return

        title = chat.title
        if not title:
            await update.message.reply_text("❌ Cannot get group title.")
            return

        logger.info(f"Creating order from title: {title} in chat {chat.id}")
        await try_create_order_from_title(
            update, context, chat, title, manual_trigger=True
        )
    except Exception as e:
        logger.error(f"Error in create_order: {e}", exc_info=True)
        if update.message:
            await update.message.reply_text(f"❌ Error creating order: {str(e)}")


@error_handler
@authorized_required
@group_chat_only
async def _get_order_and_interest_info(
    chat_id: int,
) -> Tuple[Optional[Dict], Optional[Dict]]:
    """获取订单和利息信息

    Args:
        chat_id: 群组ID

    Returns:
        (订单字典, 利息信息字典)，如果订单不存在则返回(None, None)
    """
    order_model, _, _, error_msg = await get_and_validate_order(chat_id)
    if error_msg:
        return None, None

    order = await db_operations.get_order_by_chat_id(chat_id)
    if not order:
        return None, None

    interest_info = await db_operations.get_interest_by_order_id(order["order_id"])
    return order, interest_info


def _build_order_status_message(order: Dict, interest_info: Dict) -> str:
    """构建订单状态消息

    Args:
        order: 订单字典
        interest_info: 利息信息字典

    Returns:
        消息文本
    """
    interest_total = interest_info.get("total_amount", 0.0) or 0.0
    interest_count = interest_info.get("count", 0) or 0

    msg = (
        "📋 Current Order Status:\n"
        "──────────────────\n"
        f"📝 Order ID: `{order['order_id']}`\n"
        f"🏷️ Group ID: `{order['group_id']}`\n"
        f"📅 Date: {order['date']}\n"
        f"👥 Week Group: {order['weekday_group']}\n"
        f"👤 Customer: {order['customer']}\n"
        f"💰 Amount: {order['amount']:.2f}\n"
        f"📊 State: {order['state']}\n"
    )

    if interest_count > 0:
        msg += (
            "──────────────────\n"
            "💵 Interest Collected:\n"
            f"   Total: {interest_total:,.2f}\n"
            f"   Times: {interest_count}\n"
        )
    else:
        msg += "──────────────────\n" "💵 Interest Collected: 0.00\n"

    msg += "──────────────────"
    return msg


def _build_order_action_keyboard() -> InlineKeyboardMarkup:
    """构建订单操作按钮

    Returns:
        内联键盘对象
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Normal", callback_data="order_action_normal"),
            InlineKeyboardButton("⚠️ Overdue", callback_data="order_action_overdue"),
        ],
        [
            InlineKeyboardButton("🏁 End", callback_data="order_action_end"),
            InlineKeyboardButton("🚫 Breach", callback_data="order_action_breach"),
        ],
        [
            InlineKeyboardButton(
                "💸 Breach End", callback_data="order_action_breach_end"
            )
        ],
        [
            InlineKeyboardButton(
                "💳 Send Account", callback_data="payment_select_account"
            )
        ],
        [
            InlineKeyboardButton(
                "🔄 Change Attribution", callback_data="order_action_change_attribution"
            )
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


async def show_current_order(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """显示当前订单状态和操作菜单"""
    chat_id, reply_func = get_chat_info(update)
    if not chat_id or not reply_func:
        return

    order, interest_info = await _get_order_and_interest_info(chat_id)
    if order is None:
        await reply_func(
            "❌ No active order in this group.\nUse /create to start a new order."
        )
        return

    msg = _build_order_status_message(order, interest_info)
    keyboard = _build_order_action_keyboard()
    await reply_func(msg, reply_markup=keyboard, parse_mode="Markdown")
