"""资金管理命令处理器"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from decorators import error_handler
from services.module2_finance.finance_service import FinanceService
from utils.handler_helpers import get_user_id

logger = logging.getLogger(__name__)


@error_handler
async def adjust_funds(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """调整流动资金余额命令"""
    from utils.handler_helpers import send_error_message, validate_args_count

    is_valid, error_msg = validate_args_count(context, 1, "/adjust <金额> [备注]")
    if not is_valid:
        await send_error_message(
            update,
            "❌ 用法: /adjust <金额> [备注]\n"
            "示例: /adjust +5000 收入备注\n"
            "      /adjust -3000 支出备注",
        )
        return

    amount_str = context.args[0]
    note = " ".join(context.args[1:]) if len(context.args) > 1 else "无备注"

    # 验证金额格式
    if not (amount_str.startswith("+") or amount_str.startswith("-")):
        await update.message.reply_text("❌ 金额格式错误，请使用+100或-200格式")
        return

    amount = float(amount_str)
    if amount == 0:
        await update.message.reply_text("❌ 调整金额不能为0")
        return

    # 使用FinanceService调整资金
    user_id = get_user_id(update)
    success, error_msg = await FinanceService.adjust_funds(amount, user_id)

    if not success:
        await update.message.reply_text(f"❌ 资金调整失败: {error_msg}")
        return

    # 获取调整后的财务数据
    financial_data = await FinanceService.get_financial_summary()
    await update.message.reply_text(
        "✅ 资金调整成功\n"
        f"调整类型: {'增加' if amount > 0 else '减少'}\n"
        f"调整金额: {abs(amount):.2f}\n"
        f"调整后余额: {financial_data['liquid_funds']:.2f}\n"
        f"备注: {note}"
    )
