"""搜索金额输入 - 解析模块

包含解析和验证金额的逻辑。
"""

from telegram import Update
from telegram.ext import ContextTypes

from utils.amount_helpers import parse_amount
from utils.error_messages import ErrorMessages


async def parse_and_validate_amount(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str
) -> float | None:
    """解析和验证金额

    Args:
        update: Telegram 更新对象
        context: 上下文对象
        text: 输入文本

    Returns:
        float: 解析后的金额，如果无效则返回 None
    """
    # 解析金额
    target_amount = parse_amount(text)
    if target_amount is None or target_amount <= 0:
        await update.message.reply_text(
            f"{ErrorMessages.invalid_amount_format()}\n\n"
            "请输入有效的金额，例如：\n"
            "• 20万\n"
            "• 200000\n\n"
            "输入 'cancel' 取消"
        )
        return None

    return target_amount
