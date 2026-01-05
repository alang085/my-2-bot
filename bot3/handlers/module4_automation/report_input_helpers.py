"""报表相关文本输入辅助函数"""

# 标准库
import logging
from datetime import datetime

# 第三方库
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

# 本地模块
import db_operations

logger = logging.getLogger(__name__)


async def _handle_report_query(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str
):
    """处理报表查询"""
    from handlers.module4_automation.report_query_parse import \
        parse_report_query_params
    from handlers.module4_automation.report_query_send import \
        send_report_query_result

    try:
        # 解析查询参数
        success, error_msg, start_date, end_date, show_expenses = (
            await parse_report_query_params(update, context, text)
        )
        if not success:
            await update.message.reply_text(error_msg)
            return

        # 获取归属ID
        group_id = context.user_data.get("report_group_id")
        user_id = update.effective_user.id if update.effective_user else None
        if user_id:
            user_group_id = await db_operations.get_user_group_id(user_id)
            if user_group_id:
                group_id = user_group_id

        # 发送报表结果
        await send_report_query_result(
            update, context, start_date, end_date, group_id, show_expenses
        )

    except Exception as e:
        logger.error(f"查询报表出错: {e}")
        await update.message.reply_text(f"⚠️ Query Error: {e}")
        context.user_data["state"] = None
