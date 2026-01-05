"""订单操作回调处理器 - 归属管理模块

包含归属变更相关的回调处理逻辑。
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from handlers.data_access import (get_all_group_ids_for_callback,
                                  get_order_by_chat_id_for_callback)
from handlers.module1_user.attribution_handlers import \
    change_orders_attribution
from handlers.module3_order.basic_handlers import show_current_order
from utils.chat_helpers import is_group_chat


async def handle_order_change_attribution(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """处理更改归属的回调"""
    # 获取当前订单
    chat_id = query.message.chat_id
    order = await get_order_by_chat_id_for_callback(chat_id)
    if not order:
        is_group = is_group_chat(update)
        msg = "❌ Order not found" if is_group else "❌ 没有找到订单"
        await query.answer(msg, show_alert=True)
        return

    # 获取所有归属ID列表
    all_group_ids = await get_all_group_ids_for_callback()
    if not all_group_ids:
        is_group = is_group_chat(update)
        msg = "❌ No available Group ID" if is_group else "❌ 没有可用的归属ID"
        await query.answer(msg, show_alert=True)
        return

    # 显示归属ID选择界面
    is_group = is_group_chat(update)
    keyboard = _build_attribution_keyboard(all_group_ids, order["group_id"], is_group)
    msg_text = _build_attribution_message(order, is_group)

    await query.edit_message_text(msg_text, reply_markup=InlineKeyboardMarkup(keyboard))
    await query.answer()


async def handle_order_change_to(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query, data: str
) -> None:
    """处理选择归属ID的回调"""
    new_group_id = data[16:]  # 提取新的归属ID

    # 获取当前订单
    chat_id = query.message.chat_id
    order = await get_order_by_chat_id_for_callback(chat_id)
    is_group = is_group_chat(update)

    if not order:
        msg = "❌ Order not found" if is_group else "❌ 没有找到订单"
        await query.answer(msg, show_alert=True)
        return

    # 如果归属ID相同，无需更改
    if order["group_id"] == new_group_id:
        msg = "✅ Group ID unchanged" if is_group else "✅ 归属ID未变更"
        await query.answer(msg, show_alert=True)
        return

    # 执行归属变更（单个订单）
    orders = [order]
    success_count, fail_count = await change_orders_attribution(
        update, context, orders, new_group_id
    )

    if success_count > 0:
        msg = "✅ Attribution changed" if is_group else "✅ 归属变更完成"
        await query.answer(msg)
        # 在群聊中不刷新订单信息显示，只保留结果消息
        # 在私聊中可以刷新显示
        if not is_group:
            await show_current_order(update, context)
    else:
        msg = "❌ Attribution change failed" if is_group else "❌ 归属变更失败"
        await query.answer(msg, show_alert=True)


def _build_attribution_keyboard(
    all_group_ids: list, current_group_id: str, is_group: bool
) -> list:
    """构建归属ID选择键盘"""
    keyboard = []
    row = []
    for gid in sorted(all_group_ids):
        # 当前归属ID显示为选中状态
        if gid == current_group_id:
            row.append(
                InlineKeyboardButton(f"✓ {gid}", callback_data=f"order_change_to_{gid}")
            )
        else:
            row.append(
                InlineKeyboardButton(gid, callback_data=f"order_change_to_{gid}")
            )
        if len(row) == 4:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    back_text = "🔙 Back" if is_group else "🔙 返回"
    keyboard.append(
        [InlineKeyboardButton(back_text, callback_data="order_action_back")]
    )
    return keyboard


def _build_attribution_message(order: dict, is_group: bool) -> str:
    """构建归属变更消息"""
    if is_group:
        return (
            f"🔄 Change Attribution\n\n"
            f"Current Attribution: {order['group_id']}\n"
            f"Order ID: {order['order_id']}\n"
            f"Amount: {order['amount']:.2f}\n\n"
            f"Please select new Attribution ID:"
        )
    else:
        return (
            f"🔄 更改归属\n\n"
            f"当前归属: {order['group_id']}\n"
            f"订单ID: {order['order_id']}\n"
            f"金额: {order['amount']:.2f}\n\n"
            f"请选择新的归属ID:"
        )
