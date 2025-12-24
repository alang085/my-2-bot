"""订单总表处理器"""

# 标准库
import logging

# 第三方库
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

# 本地模块
import db_operations
from decorators import authorized_required, error_handler, private_chat_only
from utils.date_helpers import get_daily_period_date

logger = logging.getLogger(__name__)


@authorized_required
@error_handler
@private_chat_only
async def show_order_table(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """显示订单总表（员工权限）"""
    try:
        # 发送处理中消息
        processing_msg = await update.message.reply_text("⏳ 正在生成订单报表Excel文件，请稍候...")

        # 获取所有有效订单
        valid_orders = await db_operations.get_all_valid_orders()

        # 获取当日利息总额
        date = get_daily_period_date()
        daily_interest = await db_operations.get_daily_interest_total(date)

        # 获取当日完成的订单
        completed_orders = await db_operations.get_completed_orders_by_date(date)

        # 获取当日违约完成的订单（仅当日有变动的）
        breach_end_orders = await db_operations.get_breach_end_orders_by_date(date)

        # 获取日切数据
        daily_summary = await db_operations.get_daily_summary(date)

        # 导出Excel
        from utils.excel_export import export_orders_to_excel

        file_path = await export_orders_to_excel(
            valid_orders, completed_orders, breach_end_orders, daily_interest, daily_summary
        )

        # 构建按钮
        keyboard = [[InlineKeyboardButton("🔙 返回报表", callback_data="report_view_today_ALL")]]

        # 发送Excel文件
        with open(file_path, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=f"订单报表_{date}.xlsx",
                caption=f"📊 订单报表 Excel 文件 ({date})\n\n包含：\n• 有效订单总表\n• 当日完成订单\n• 当日违约完成订单\n• 日切数据汇总",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        # 删除处理中消息
        try:
            await processing_msg.delete()
        except:
            pass

        # 删除临时文件
        import os

        try:
            os.remove(file_path)
        except:
            pass
    except Exception as e:
        logger.error(f"显示订单总表失败: {e}", exc_info=True)
        await update.message.reply_text(f"❌ 显示订单总表失败: {e}")


@error_handler
@private_chat_only
async def export_order_table_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """导出订单总表为Excel（仅管理员）- 兼容函数，现在直接调用show_order_table"""
    # 由于show_order_table现在直接生成Excel，这个函数可以直接调用它
    await show_order_table(update, context)
