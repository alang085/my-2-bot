"""主回调处理器"""

# 标准库
import logging

# 第三方库
from telegram import Update
from telegram.ext import ContextTypes

# 本地模块
from callbacks.main_callback_broadcast import (handle_broadcast_done,
                                               handle_broadcast_send_12)
from callbacks.main_callback_operations import (handle_cancel_restore,
                                                handle_confirm_restore,
                                                handle_daily_ops_summary,
                                                handle_restore_daily_data,
                                                handle_show_all_operations)
from callbacks.main_callback_routing import route_callback
from callbacks.main_callback_start_pages import (
    handle_start_hide_admin_commands, handle_start_page_group,
    handle_start_page_payment, handle_start_page_private,
    handle_start_show_admin_commands)

logger = logging.getLogger(__name__)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """主按钮回调入口"""
    query = update.callback_query
    data = query.data

    # 获取用户ID
    user_id = update.effective_user.id if update.effective_user else None

    # 路由到不同的处理器
    if await route_callback(update, context, data, user_id):
        return

    # 处理广播相关回调
    if data == "broadcast_send_12":
        await handle_broadcast_send_12(update, context, query)
        return
    elif data == "broadcast_done":
        await handle_broadcast_done(update, context, query)
        return

    # 处理启动页面相关回调
    if data == "start_page_private":
        await handle_start_page_private(update, context, query)
        return
    elif data == "start_page_payment":
        await handle_start_page_payment(update, context, query)
        return
    elif data == "start_page_group":
        await handle_start_page_group(update, context, query)
        return
    elif data == "start_show_admin_commands":
        await handle_start_show_admin_commands(update, context, query)
        return
    elif data == "start_hide_admin_commands":
        await handle_start_hide_admin_commands(update, context, query)
        return

    # 处理操作记录相关回调
    if data.startswith("show_all_operations_"):
        await handle_show_all_operations(update, context, query, data)
        return
    elif data.startswith("restore_daily_data_"):
        await handle_restore_daily_data(update, context, query, data)
        return
    elif data.startswith("confirm_restore_"):
        await handle_confirm_restore(update, context, query, data)
        return
    elif data == "cancel_restore":
        await handle_cancel_restore(update, context, query)
        return
    elif data.startswith("daily_ops_summary_"):
        await handle_daily_ops_summary(update, context, query, data)
        return

    # 未处理的回调
    logger.warning(f"Unhandled callback data: {data}")
    try:
        if query.message:
            await query.message.reply_text(f"⚠️ 未知的操作: {data}")
        else:
            await query.answer("⚠️ 未知的操作", show_alert=True)
    except Exception as e:
        logger.error(f"发送未知操作提示失败: {e}", exc_info=True)
        try:
            await query.answer("⚠️ 未知的操作", show_alert=True)
        except Exception:
            pass
