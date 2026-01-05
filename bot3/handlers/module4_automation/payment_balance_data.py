"""支付余额更新数据类

使用dataclass封装支付余额更新相关的参数。
"""

from dataclasses import dataclass

from telegram import Update
from telegram.ext import ContextTypes


@dataclass
class BalanceUpdateResultParams:
    """余额更新结果参数

    封装发送余额更新结果所需的所有参数。
    """

    update: Update
    context: ContextTypes.DEFAULT_TYPE
    success: bool
    account_type: str
    account_name: str
    account_number: str
    new_balance: float
    error_msg: str = ""
