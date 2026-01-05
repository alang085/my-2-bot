"""支付余额更新 - 验证模块

包含验证更新余额请求的逻辑。
"""

from telegram import Update
from telegram.ext import ContextTypes


def validate_balance_update_request(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str
) -> tuple[bool, str, int | None, float | None]:
    """验证更新余额请求

    Args:
        update: Telegram更新对象
        context: 上下文对象
        text: 输入文本

    Returns:
        Tuple: (是否有效, 错误消息, 账户ID, 金额)
    """
    # 从user_state中提取账户ID
    user_state = context.user_data.get("state", "")
    if not user_state.startswith("UPDATING_BALANCE_BY_ID_"):
        return False, "❌ 错误：状态异常", None

    account_id = context.user_data.get("updating_balance_account_id")
    if not account_id:
        # 尝试从state中提取
        try:
            account_id = int(user_state.replace("UPDATING_BALANCE_BY_ID_", ""))
        except ValueError:
            return False, "❌ 错误：找不到账户ID", None

    # 解析金额（使用验证工具）
    from utils.validation_helpers import validate_amount

    is_valid, new_balance, error_msg = validate_amount(text)
    if not is_valid:
        return False, error_msg or "❌ 请输入有效的金额", None, None

    return True, "", account_id, new_balance
