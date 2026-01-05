"""每日数据变更表处理器"""

# 标准库
import logging
from datetime import datetime

import pytz
# 第三方库
from telegram import Update
from telegram.ext import ContextTypes

# 本地模块
import db_operations
from decorators import authorized_required, error_handler, private_chat_only

logger = logging.getLogger(__name__)

BEIJING_TZ = pytz.timezone("Asia/Shanghai")


@error_handler
@authorized_required
@private_chat_only
async def show_daily_changes_table(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """显示每日数据变更表（员工权限）"""
    try:
        # 解析日期参数（如果有）
        from utils.handler_helpers import (parse_date_from_args,
                                           send_error_message)

        if context.args and len(context.args) > 0:
            start_date, end_date, error_msg = parse_date_from_args(
                context, 0, allow_range=False
            )
            if error_msg:
                await send_error_message(update, error_msg)
                return
            date_str = start_date
        else:
            # 默认使用当前日期
            date_str = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d")

        # 获取每日数据变更
        changes = await get_daily_changes(date_str)

        # 生成表格文本
        table_text = generate_changes_table(date_str, changes)

        await update.message.reply_text(table_text, parse_mode="HTML")

    except Exception as e:
        logger.error(f"显示每日数据变更表失败: {e}", exc_info=True)
        await update.message.reply_text(f"❌ 查询失败: {str(e)}")


async def get_daily_changes(date: str) -> dict:
    """获取指定日期的数据变更"""
    from handlers.module5_data.daily_changes_finance import get_finance_changes
    from handlers.module5_data.daily_changes_orders import get_order_changes

    try:
        # 获取订单变更
        order_changes = await get_order_changes(date)

        # 获取财务变更
        finance_changes = await get_finance_changes(date)

        # 合并结果
        return {
            "date": date,
            **order_changes,
            **finance_changes,
        }
    except Exception as e:
        logger.error(f"获取每日数据变更失败: {e}", exc_info=True)
        return {
            "date": date,
            "new_orders": [],
            "new_clients_count": 0,
            "new_clients_amount": 0.0,
            "old_clients_count": 0,
            "old_clients_amount": 0.0,
            "completed_orders": [],
            "completed_orders_count": 0,
            "completed_orders_amount": 0.0,
            "breach_orders": [],
            "breach_orders_count": 0,
            "breach_orders_amount": 0.0,
            "breach_end_orders": [],
            "breach_end_orders_count": 0,
            "breach_end_orders_amount": 0.0,
            "interest_records": [],
            "total_interest": 0.0,
            "principal_records": [],
            "total_principal": 0.0,
            "expense_records": [],
            "company_expenses": 0.0,
            "other_expenses": 0.0,
            "total_expenses": 0.0,
        }


def generate_changes_table(date: str, changes: dict) -> str:
    """生成每日数据变更表文本"""
    from handlers.module5_data.changes_table_expense import (
        build_expense_records_detail, build_expense_summary,
        build_total_summary)
    from handlers.module5_data.changes_table_income import (
        build_income_summary, build_interest_records_detail,
        build_principal_records_detail)
    from handlers.module5_data.changes_table_order import (
        build_breach_end_orders_detail, build_completed_orders_detail,
        build_new_orders_detail, build_order_summary)

    text = "📊 <b>每日数据变更表</b>\n"
    text += f"日期: {date}\n"
    text += "═" * 40 + "\n\n"

    # 订单变更
    text += build_order_summary(changes)
    text += build_new_orders_detail(changes)
    text += build_completed_orders_detail(changes)
    text += build_breach_end_orders_detail(changes)

    # 收入变更
    text += build_income_summary(changes)
    text += build_interest_records_detail(changes)
    text += build_principal_records_detail(changes)

    # 开销变更
    text += build_expense_summary(changes)
    text += build_expense_records_detail(changes)

    # 总计
    text += build_total_summary(changes)

    return text
