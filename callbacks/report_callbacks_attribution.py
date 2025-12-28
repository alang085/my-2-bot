"""报表归属管理相关回调处理"""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from handlers.data_access import get_all_group_ids_for_callback

logger = logging.getLogger(__name__)


async def handle_menu_attribution(query):
    """处理归属ID菜单回调"""
    # 直接显示归属ID列表供选择查看报表
    group_ids = await get_all_group_ids_for_callback()
    if not group_ids:
        await query.edit_message_text(
            "⚠️ 无归属数据",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 返回", callback_data="report_view_today_ALL")]]
            ),
        )
        return

    keyboard = []
    row = []
    for gid in sorted(group_ids):
        row.append(InlineKeyboardButton(gid, callback_data=f"report_view_today_{gid}"))
        if len(row) == 4:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔙 返回", callback_data="report_view_today_ALL")])
    await query.edit_message_text(
        "请选择归属ID查看报表:", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_search_orders(query, context):
    """处理查找订单回调"""
    try:
        if query.message:
            await query.message.reply_text(
                "🔍 查找订单\n\n"
                "输入查询条件：\n\n"
                "单一查询：\n"
                "• S01（按归属查询）\n"
                "• 三（按星期分组查询）\n"
                "• 正常（按状态查询）\n\n"
                "综合查询：\n"
                "• 三 正常（周三的正常订单）\n"
                "• S01 正常（S01的正常订单）\n\n"
                "请输入:（输入 'cancel' 取消）"
            )
        else:
            await query.answer("请输入查询条件", show_alert=True)
    except Exception as e:
        logger.error(f"发送查找订单提示失败: {e}", exc_info=True)
        await query.answer("请输入查询条件", show_alert=True)
    context.user_data["state"] = "REPORT_SEARCHING"


async def handle_change_attribution(query, context):
    """处理修改归属回调"""
    # 获取查找结果
    orders = context.user_data.get("report_search_orders", [])
    if not orders:
        await query.answer("❌ 没有找到订单，请先使用查找功能")
        return

    # 获取所有归属ID列表
    all_group_ids = await get_all_group_ids_for_callback()
    if not all_group_ids:
        await query.answer("❌ 没有可用的归属ID")
        return

    # 显示归属ID选择界面
    keyboard = []
    row = []
    for gid in sorted(all_group_ids):
        row.append(InlineKeyboardButton(gid, callback_data=f"report_change_to_{gid}"))
        if len(row) == 4:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔙 取消", callback_data="report_view_today_ALL")])

    order_count = len(orders)
    total_amount = sum(order.get("amount", 0) for order in orders)

    await query.edit_message_text(
        f"🔄 修改归属\n\n"
        f"找到订单: {order_count} 个\n"
        f"订单金额: {total_amount:,.2f}\n\n"
        f"请选择新的归属ID:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_change_to_attribution(query, update, context, new_group_id: str):
    """处理归属变更确认回调"""
    orders = context.user_data.get("report_search_orders", [])
    if not orders:
        await query.answer("❌ 没有找到订单")
        return

    # 执行归属变更
    from handlers.attribution_handlers import change_orders_attribution

    success_count, fail_count = await change_orders_attribution(
        update, context, orders, new_group_id
    )

    result_msg = (
        f"✅ 归属变更完成\n\n" f"成功: {success_count} 个订单\n" f"失败: {fail_count} 个订单"
    )

    await query.edit_message_text(result_msg)
    await query.answer("✅ 归属变更完成")

    # 清除查找结果
    context.user_data.pop("report_search_orders", None)


async def handle_broadcast_start(query, context):
    """处理群发消息开始回调"""
    try:
        # 检查是否有锁定的群组
        locked_groups = context.user_data.get("locked_groups", [])
        if not locked_groups:
            await query.answer("❌ 没有锁定的群组，请先使用查找功能", show_alert=True)
            return

        # 设置用户状态为群发模式
        context.user_data["state"] = "BROADCASTING"

        # 提示用户输入要发送的消息
        message = (
            f"📢 群发消息\n\n"
            f"已锁定 {len(locked_groups)} 个群组\n\n"
            f"请输入要发送的消息内容：\n\n"
            f"💡 提示：输入 'cancel' 可以取消群发"
        )

        try:
            if query.message:
                await query.message.reply_text(message)
            else:
                await query.answer("请输入要发送的消息", show_alert=True)
        except Exception as e:
            logger.error(f"发送群发提示失败: {e}", exc_info=True)
            await query.answer("请输入要发送的消息", show_alert=True)

        await query.answer()
    except Exception as e:
        logger.error(f"处理群发开始回调失败: {e}", exc_info=True)
        await query.answer("❌ 处理失败", show_alert=True)
