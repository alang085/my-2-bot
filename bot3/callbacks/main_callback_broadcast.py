"""主回调广播处理模块

包含广播相关的回调处理逻辑。
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from utils.broadcast_helpers import format_broadcast_message
from utils.chat_helpers import is_group_chat

logger = logging.getLogger(__name__)


async def handle_broadcast_send_12(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """处理发送本金12%版本"""
    principal_12 = context.user_data.get("broadcast_principal_12", 0)
    outstanding_interest = context.user_data.get("broadcast_outstanding_interest", 0)
    date_str = context.user_data.get("broadcast_date_str", "")
    weekday_str = context.user_data.get("broadcast_weekday_str", "Friday")

    if principal_12 == 0:
        is_group = is_group_chat(update)
        msg = "❌ Data error" if is_group else "❌ 数据错误"
        await query.answer(msg, show_alert=True)
        return

    # 使用统一的播报模板函数
    message = format_broadcast_message(
        principal=principal_12,
        principal_12=principal_12,
        outstanding_interest=outstanding_interest,
        date_str=date_str,
        weekday_str=weekday_str,
    )

    try:
        is_group = is_group_chat(update)
        await context.bot.send_message(chat_id=query.message.chat_id, text=message)
        success_msg = "✅ 12% version sent" if is_group else "✅ 本金12%版本已发送"
        await query.answer(success_msg)
        done_msg = "✅ Broadcast completed" if is_group else "✅ 播报完成"
        await query.edit_message_text(done_msg)
        # 清除临时数据
        context.user_data.pop("broadcast_principal_12", None)
        context.user_data.pop("broadcast_outstanding_interest", None)
        context.user_data.pop("broadcast_date_str", None)
        context.user_data.pop("broadcast_weekday_str", None)
    except Exception as e:
        logger.error(f"发送播报消息失败: {e}", exc_info=True)
        is_group = is_group_chat(update)
        error_msg = f"❌ Send failed: {e}" if is_group else f"❌ 发送失败: {e}"
        await query.answer(error_msg, show_alert=True)


async def handle_broadcast_done(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """处理播报完成"""
    is_group = is_group_chat(update)
    done_msg = "✅ Broadcast completed" if is_group else "✅ 播报完成"
    await query.answer(done_msg)
    await query.edit_message_text(done_msg)
    # 清除临时数据
    context.user_data.pop("broadcast_principal_12", None)
    context.user_data.pop("broadcast_outstanding_interest", None)
    context.user_data.pop("broadcast_date_str", None)
    context.user_data.pop("broadcast_weekday_str", None)
