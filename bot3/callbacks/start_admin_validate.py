"""开始页面 - 管理员验证模块

包含验证管理员权限的逻辑。
"""

from telegram import Update
from telegram.ext import ContextTypes

from constants import ADMIN_IDS
from utils.chat_helpers import is_group_chat


async def validate_admin_access(update: Update, query) -> tuple[bool, str]:
    """验证管理员访问权限

    Args:
        update: Telegram更新对象
        query: 回调查询对象

    Returns:
        Tuple: (是否有效, 错误消息)
    """
    user_id = update.effective_user.id if update.effective_user else None
    if not user_id or user_id not in ADMIN_IDS:
        is_group = is_group_chat(update)
        msg = (
            "❌ This feature is for administrators only"
            if is_group
            else "❌ 此功能仅限管理员使用"
        )
        return False, msg

    return True, ""
