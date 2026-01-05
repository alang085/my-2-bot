"""支付余额历史处理 - 当前余额模块

包含显示当前余额的逻辑。
"""

import logging
from datetime import datetime

import pytz
from telegram import Update
from telegram.ext import ContextTypes

from services.module2_finance.payment_service import PaymentService

logger = logging.getLogger(__name__)


async def show_current_balance(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """显示当前余额

    Args:
        update: Telegram 更新对象
        context: 上下文对象
    """
    # 获取所有账号
    accounts = await PaymentService.get_all_accounts()

    if not accounts:
        await _send_message(update, "❌ 没有账户数据")
        return

    # 计算总金额
    gcash_total, paymaya_total, total = await PaymentService.calculate_total_balance(
        accounts
    )

    # 获取当前日期
    beijing_tz = pytz.timezone("Asia/Shanghai")
    now = datetime.now(beijing_tz)
    date_str = now.strftime("%Y-%m-%d")

    # 获取各账户的最后更新时间
    gcash_accounts = [acc for acc in accounts if acc.get("account_type") == "gcash"]
    paymaya_accounts = [acc for acc in accounts if acc.get("account_type") == "paymaya"]

    def format_updated_time(account_list):
        """格式化账户最后更新时间"""
        if not account_list:
            return None
        # 获取最新的updated_at时间
        updated_times = [
            acc.get("updated_at") for acc in account_list if acc.get("updated_at")
        ]
        if not updated_times:
            return None
        # 找到最新的更新时间
        latest_time = max(updated_times)
        if latest_time:
            # 格式化时间显示
            try:
                if isinstance(latest_time, str):
                    dt = datetime.strptime(latest_time[:19], "%Y-%m-%d %H:%M:%S")
                else:
                    dt = latest_time
                return dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                return None
        return None

    gcash_time = format_updated_time(gcash_accounts)
    paymaya_time = format_updated_time(paymaya_accounts)

    # 简单干净的显示
    msg = f"💰 账户总余额（{date_str}）\n\n"
    if gcash_time:
        msg += f"GCash: {gcash_total:,.2f} (更新于 {gcash_time})\n"
    else:
        msg += f"GCash: {gcash_total:,.2f}\n"

    if paymaya_time:
        msg += f"PayMaya: {paymaya_total:,.2f} (更新于 {paymaya_time})\n"
    else:
        msg += f"PayMaya: {paymaya_total:,.2f}\n"

    msg += "─────────────\n"
    msg += f"总计: {total:,.2f}\n\n"
    msg += "💡 提示：\n"
    msg += "• 使用 /balance_history 2025-01-15 查看指定日期\n"
    msg += "• 使用 /balance_history recent 查看最近7天"

    await _send_message(update, msg)


async def _send_message(update: Update, msg: str) -> None:
    """发送消息（支持message和callback_query）

    Args:
        update: Telegram 更新对象
        msg: 消息内容
    """
    from handlers.module2_finance.payment_balance_message import send_message

    await send_message(update, msg)
