"""订单创建辅助函数 - 验证模块

包含订单创建前的验证逻辑。
"""

import logging
from datetime import date
from typing import Any, Dict, Tuple

from telegram import Update

import db_operations
from constants import HISTORICAL_THRESHOLD_DATE
from utils.chat_helpers import is_group_chat

logger = logging.getLogger(__name__)


def check_historical_order(order_date: date) -> bool:
    """检查订单是否为历史订单

    Args:
        order_date: 订单日期

    Returns:
        bool: 是否为历史订单
    """
    threshold_date = date(*HISTORICAL_THRESHOLD_DATE)
    return order_date < threshold_date


async def validate_balance_for_order(
    update: Update, amount: float, is_historical: bool
) -> Tuple[bool, str]:
    """验证余额是否足够（仅非历史订单）

    Args:
        update: Telegram 更新对象
        amount: 订单金额
        is_historical: 是否为历史订单

    Returns:
        Tuple[bool, str]: (是否通过验证, 错误消息)
    """
    if is_historical:
        return True, ""

    financial_data = await db_operations.get_financial_data()
    if financial_data["liquid_funds"] < amount:
        msg = (
            f"❌ Insufficient Liquid Funds\n"
            f"Current Balance: {financial_data['liquid_funds']:.2f}\n"
            f"Required: {amount:.2f}\n"
            f"Missing: {amount - financial_data['liquid_funds']:.2f}"
        )
        if is_group_chat(update):
            await update.message.reply_text(msg)
        return False, msg

    return True, ""
