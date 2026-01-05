"""订单总表处理器"""

# 标准库
import logging
from typing import Dict, List, Tuple

# 第三方库
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

# 本地模块
import db_operations
from decorators import authorized_required, error_handler, private_chat_only
from utils.date_helpers import get_daily_period_date

logger = logging.getLogger(__name__)


@error_handler
@authorized_required
@private_chat_only
async def _fetch_order_table_data(
    date: str,
) -> Tuple[List[Dict], float, List[Dict], List[Dict], List[Dict], Dict]:
    """获取订单总表所需数据

    Args:
        date: 日期字符串

    Returns:
        (
            valid_orders,
            daily_interest,
            completed_orders,
            breach_orders,
            breach_end_orders,
            daily_summary,
        )
    """
    valid_orders = await db_operations.get_all_valid_orders()
    daily_interest = await db_operations.get_daily_interest_total(date)
    # 各单页显示所有订单的总计，而不是当天的数据
    completed_orders = await db_operations.search_orders_advanced_all_states(
        {"state": "end"}
    )
    breach_orders = await db_operations.search_orders_advanced_all_states(
        {"state": "breach"}
    )
    breach_end_orders = await db_operations.search_orders_advanced_all_states(
        {"state": "breach_end"}
    )
    daily_summary = await db_operations.get_daily_summary(date)
    return (
        valid_orders,
        daily_interest,
        completed_orders,
        breach_orders,
        breach_end_orders,
        daily_summary,
    )


async def _send_order_table_excel(update: Update, file_path: str, date: str) -> None:
    """发送订单总表Excel文件

    Args:
        update: Telegram更新对象
        file_path: Excel文件路径
        date: 日期字符串
    """
    keyboard = [
        [InlineKeyboardButton("🔙 返回报表", callback_data="report_view_today_ALL")]
    ]

    with open(file_path, "rb") as f:
        await update.message.reply_document(
            document=f,
            filename=f"订单报表_{date}.xlsx",
            caption=(
                f"📊 订单报表 Excel 文件 ({date})\n\n包含：\n"
                f"• 有效订单总表\n• 当日完成订单\n• 当日违约订单\n"
                f"• 当日违约完成订单\n• 日切数据汇总\n"
                f"• 订单chat_id对应表（所有订单）"
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


def _cleanup_temp_files(file_path: str, processing_msg) -> None:
    """清理临时文件和处理中消息

    Args:
        file_path: Excel文件路径
        processing_msg: 处理中消息对象
    """
    import os

    try:
        if processing_msg:
            import asyncio

            asyncio.create_task(processing_msg.delete())
    except Exception:
        pass

    try:
        os.remove(file_path)
    except Exception:
        pass


async def show_order_table(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """显示订单总表（员工权限）"""
    try:
        processing_msg = await update.message.reply_text(
            "⏳ 正在生成订单报表Excel文件，请稍候..."
        )

        date = get_daily_period_date()
        (
            valid_orders,
            daily_interest,
            completed_orders,
            breach_orders,
            breach_end_orders,
            daily_summary,
        ) = await _fetch_order_table_data(date)

        from utils.excel_export import export_orders_to_excel

        file_path = await export_orders_to_excel(
            valid_orders,
            completed_orders,
            breach_orders,
            breach_end_orders,
            daily_interest,
            daily_summary,
        )

        await _send_order_table_excel(update, file_path, date)
        _cleanup_temp_files(file_path, processing_msg)

    except Exception as e:
        logger.error(f"显示订单总表失败: {e}", exc_info=True)
        await update.message.reply_text(f"❌ 显示订单总表失败: {e}")


@error_handler
@private_chat_only
async def export_order_table_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """导出订单总表为Excel（仅管理员）- 兼容函数，现在直接调用show_order_table"""
    # 由于show_order_table现在直接生成Excel，这个函数可以直接调用它
    await show_order_table(update, context)
