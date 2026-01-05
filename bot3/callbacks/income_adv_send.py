"""收入高级查询分页 - 发送模块

包含发送分页消息的逻辑。
"""

import logging

from telegram import CallbackQuery, InlineKeyboardMarkup

from callbacks.report_callbacks_income import safe_edit_message_text

logger = logging.getLogger(__name__)


async def send_income_adv_page(
    query: CallbackQuery, report: str, reply_markup: InlineKeyboardMarkup
) -> None:
    """发送分页消息

    Args:
        query: 回调查询对象
        report: 报表文本
        reply_markup: 按钮标记
    """
    try:
        await safe_edit_message_text(query, report, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"编辑收入明细消息失败: {e}", exc_info=True)
        try:
            if query.message:
                await query.message.reply_text(report, reply_markup=reply_markup)
            else:
                await query.answer("❌ 显示失败（消息不存在）", show_alert=True)
        except Exception as e2:
            logger.error(f"发送报表消息失败: {e2}", exc_info=True)
            await query.answer("❌ 显示失败", show_alert=True)
