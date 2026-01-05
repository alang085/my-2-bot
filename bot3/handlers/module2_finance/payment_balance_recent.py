"""支付余额历史处理 - 最近余额模块

包含显示最近7天余额统计的逻辑。
"""

import logging
from datetime import datetime, timedelta

import pytz
from telegram import Update
from telegram.ext import ContextTypes

from handlers.module2_finance.payment_balance_message import send_message
from services.module2_finance.payment_service import PaymentService

logger = logging.getLogger(__name__)


async def show_recent_balance(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """显示最近7天的余额统计

    Args:
        update: Telegram 更新对象
        context: 上下文对象
    """
    beijing_tz = pytz.timezone("Asia/Shanghai")
    now = datetime.now(beijing_tz)

    msg = "📊 最近7天余额统计\n\n"
    has_data = False

    for i in range(7):
        date = now - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")

        # 获取该日期的余额汇总
        summary = await PaymentService.get_balance_summary_by_date(date_str)

        if summary and summary.get("total", 0) > 0:
            has_data = True
            gcash_total = summary.get("gcash_total", 0.0)
            paymaya_total = summary.get("paymaya_total", 0.0)
            total = summary.get("total", 0.0)

            # 格式化日期显示
            weekday = date.strftime("%a")
            date_display = date.strftime("%m-%d")

            msg += f"📅 {date_display} ({weekday})\n"
            msg += f"   GCash: {gcash_total:,.2f}\n"
            msg += f"   PayMaya: {paymaya_total:,.2f}\n"
            msg += f"   总计: {total:,.2f}\n\n"

    if not has_data:
        msg += "❌ 暂无历史余额数据\n\n"
        msg += "💡 提示：余额统计每天11:00自动保存"

    await send_message(update, msg)
