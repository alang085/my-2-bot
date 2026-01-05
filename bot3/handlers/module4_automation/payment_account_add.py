"""支付账户添加辅助函数"""

# 标准库
import logging
from typing import Optional, Tuple

# 第三方库
from telegram import Update
from telegram.ext import ContextTypes

# 本地模块
import db_operations
from utils.validation_helpers import validate_account_name

logger = logging.getLogger(__name__)


def _parse_add_account_input(text: str) -> Tuple[Optional[str], Optional[str]]:
    """解析添加账户输入

    Args:
        text: 输入文本

    Returns:
        (账号号码, 账户名称) 或 (None, None)
    """
    parts = text.strip().split(maxsplit=1)
    if len(parts) < 2:
        return None, None
    return parts[0].strip(), parts[1].strip()


async def _validate_add_account_input(
    update: Update, account_number: Optional[str], account_name: Optional[str]
) -> Tuple[bool, Optional[str]]:
    """验证添加账户输入

    Args:
        update: Telegram更新对象
        account_number: 账号号码
        account_name: 账户名称

    Returns:
        (是否有效, 验证后的账户名称)
    """
    if not account_number or not account_name:
        await update.message.reply_text(
            "❌ 格式错误\n" "格式: <账号号码> <账户名称>\n" "示例: 09171234567 张三"
        )
        return False, None

    is_valid, validated_name, error_msg = validate_account_name(account_name)
    if not is_valid:
        await update.message.reply_text(error_msg or "❌ 账户名称无效")
        return False, None

    if not account_number:
        await update.message.reply_text("❌ 账号号码不能为空")
        return False, None

    return True, validated_name


async def _refresh_account_display(
    update: Update, context: ContextTypes.DEFAULT_TYPE, account_type: str
) -> None:
    """刷新账户显示

    Args:
        update: Telegram更新对象
        context: 上下文对象
        account_type: 账户类型
    """
    if account_type == "gcash":
        from handlers.module2_finance.payment_handlers import show_gcash

        await show_gcash(update, context)
    else:
        from handlers.module2_finance.payment_handlers import show_paymaya

        await show_paymaya(update, context)


async def _handle_add_account(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, account_type: str
):
    """处理添加账户输入"""
    account_number, account_name = _parse_add_account_input(text)
    is_valid, validated_name = await _validate_add_account_input(
        update, account_number, account_name
    )

    if not is_valid:
        return

    account_id = await db_operations.create_payment_account(
        account_type, account_number, validated_name
    )

    if account_id:
        account_name_display = "GCASH" if account_type == "gcash" else "PayMaya"
        await update.message.reply_text(
            f"✅ {account_name_display}账户已添加\n\n"
            f"账号号码: {account_number}\n"
            f"账户名称: {validated_name}"
        )
        await _refresh_account_display(update, context, account_type)
    else:
        await update.message.reply_text("❌ 添加失败")

    context.user_data["state"] = None
