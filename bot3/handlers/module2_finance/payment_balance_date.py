"""支付余额历史处理 - 指定日期余额模块

包含显示指定日期余额的逻辑。
"""

import logging
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from handlers.module2_finance.payment_balance_message import send_message
from services.module2_finance.payment_service import PaymentService

logger = logging.getLogger(__name__)


async def show_date_balance(
    update: Update, context: ContextTypes.DEFAULT_TYPE, date_str: str
) -> None:
    """显示指定日期的余额

    Args:
        update: Telegram 更新对象
        context: 上下文对象
        date_str: 日期字符串（格式：YYYY-MM-DD）
    """
    # 获取该日期的余额汇总
    summary = await PaymentService.get_balance_summary_by_date(date_str)

    if not summary or summary.get("total", 0) == 0:
        msg = f"❌ {date_str} 没有余额数据\n\n"
        msg += "💡 提示：余额统计每天11:00自动保存"
        await send_message(update, msg)
        return

    gcash_total = summary.get("gcash_total", 0.0)
    paymaya_total = summary.get("paymaya_total", 0.0)
    total = summary.get("total", 0.0)
    account_details = summary.get("account_details", [])

    # 格式化日期显示
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    weekday = date_obj.strftime("%A")

    msg = f"💰 余额统计（{date_str} {weekday}）\n\n"
    msg += f"GCash总计: {gcash_total:,.2f}\n"
    msg += f"PayMaya总计: {paymaya_total:,.2f}\n"
    msg += "─────────────\n"
    msg += f"总计: {total:,.2f}\n\n"

    # 显示每个账户的详细信息
    if account_details:
        msg += _format_account_details(account_details)

    await send_message(update, msg)


def _format_account_details(account_details: list) -> str:
    """格式化账户明细

    Args:
        account_details: 账户明细列表

    Returns:
        str: 格式化后的消息
    """
    msg = "📋 账户明细：\n\n"
    current_type = None

    for detail in account_details:
        account_type = detail.get("account_type", "")
        account_name = detail.get("account_name", "未设置")
        account_number = detail.get("account_number", "未设置")
        balance = detail.get("balance", 0.0)

        # 按账户类型分组显示
        if account_type != current_type:
            if current_type is not None:
                msg += "\n"
            type_name = "GCASH" if account_type == "gcash" else "PayMaya"
            msg += f"💳 {type_name}:\n"
            current_type = account_type

        display_name = (
            account_name
            if account_name and account_name != "未设置"
            else account_number
        )
        msg += f"   • {display_name}: {balance:,.2f}\n"

    return msg
