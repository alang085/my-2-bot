"""搜索回调归属变更模块

包含归属变更相关的回调处理逻辑。
"""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from handlers.data_access import get_all_group_ids_for_callback

logger = logging.getLogger(__name__)


async def handle_search_change_attribution(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """显示归属变更选择界面"""
    # 获取查找结果
    orders = context.user_data.get("search_orders", [])
    if not orders:
        await query.answer("❌ 没有找到订单，请先使用查找功能", show_alert=True)
        # 尝试重新显示查找菜单
        try:
            keyboard = [
                [
                    InlineKeyboardButton("按状态", callback_data="search_menu_state"),
                    InlineKeyboardButton(
                        "按归属ID", callback_data="search_menu_attribution"
                    ),
                    InlineKeyboardButton(
                        "按星期分组", callback_data="search_menu_group"
                    ),
                ]
            ]
            await query.edit_message_text(
                "❌ 没有找到订单\n\n请先使用查找功能找到订单后，再更改归属。",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        except Exception:
            pass
        return

    # 获取所有归属ID列表
    all_group_ids = await get_all_group_ids_for_callback()
    if not all_group_ids:
        await query.answer("❌ 没有可用的归属ID", show_alert=True)
        await query.edit_message_text(
            "❌ 没有可用的归属ID\n\n请先使用 /create_attribution 创建归属ID。"
        )
        return

    # 显示归属ID选择界面
    keyboard = []
    row = []
    for gid in sorted(all_group_ids):
        row.append(InlineKeyboardButton(gid, callback_data=f"search_change_to_{gid}"))
        if len(row) == 4:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔙 取消", callback_data="search_start")])

    order_count = len(orders)
    total_amount = sum(order.get("amount", 0) for order in orders)

    await query.edit_message_text(
        f"🔄 更改归属\n\n"
        f"找到订单: {order_count} 个\n"
        f"订单金额: {total_amount:,.2f}\n\n"
        f"请选择新的归属ID:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_search_change_to(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query, data: str
) -> None:
    """处理归属变更"""
    new_group_id = data[17:]  # 提取新的归属ID

    orders = context.user_data.get("search_orders", [])
    if not orders:
        await query.answer("❌ 没有找到订单，请重新查找", show_alert=True)
        # 尝试重新显示查找菜单
        try:
            keyboard = [
                [
                    InlineKeyboardButton("按状态", callback_data="search_menu_state"),
                    InlineKeyboardButton(
                        "按归属ID", callback_data="search_menu_attribution"
                    ),
                    InlineKeyboardButton(
                        "按星期分组", callback_data="search_menu_group"
                    ),
                ]
            ]
            await query.edit_message_text(
                "❌ 查找结果已过期\n\n请重新使用查找功能。",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        except Exception:
            pass
        return

    # 执行归属变更
    try:
        from handlers.module1_user.attribution_handlers import \
            change_orders_attribution

        success_count, fail_count = await change_orders_attribution(
            update, context, orders, new_group_id
        )

        result_msg = (
            f"✅ 归属变更完成\n\n"
            f"成功: {success_count} 个订单\n"
            f"失败: {fail_count} 个订单\n\n"
            f"新归属ID: {new_group_id}"
        )

        await query.edit_message_text(result_msg)
        await query.answer("✅ 归属变更完成")

        # 清除查找结果
        context.user_data.pop("search_orders", None)
    except Exception as e:
        logger.error(f"归属变更失败: {e}", exc_info=True)
        await query.answer(f"❌ 归属变更失败: {str(e)}", show_alert=True)
