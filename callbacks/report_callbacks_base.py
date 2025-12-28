"""报表回调基础类和辅助函数"""

import logging

from config import ADMIN_IDS
from handlers.data_access import get_user_authorization_status

logger = logging.getLogger(__name__)


# Mock classes for testing/exporting
class MockMessage:
    """模拟 Message 对象，用于回调中调用需要 Update 的函数"""

    def __init__(self, original_message, bot):
        self.chat_id = original_message.chat_id
        self.message_id = original_message.message_id
        self._bot = bot
        self._original_message = original_message

    async def reply_text(self, text, reply_markup=None, parse_mode=None):
        return await self._bot.send_message(
            chat_id=self.chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )

    async def reply_document(self, document, filename=None, caption=None, reply_markup=None):
        return await self._bot.send_document(
            chat_id=self.chat_id,
            document=document,
            filename=filename,
            caption=caption,
            reply_markup=reply_markup,
        )


class MockUpdate:
    """模拟 Update 对象，用于回调中调用需要 Update 的函数"""

    def __init__(self, query, bot):
        self.effective_user = query.from_user
        self.message = MockMessage(query.message, bot)


async def check_expense_permission(user_id: int) -> bool:
    """检查用户是否有权限录入开销（异步版本）"""
    if not user_id:
        return False
    if user_id in ADMIN_IDS:
        return True
    return await get_user_authorization_status(user_id)


async def check_user_permission(user_id: int, user_group_id: str, data: str, query) -> bool:
    """检查用户权限并处理权限限制

    Returns:
        bool: True 表示有权限继续，False 表示已处理权限错误
    """
    if user_group_id:
        # 用户有权限限制，检查回调中的归属ID
        if data.startswith("report_view_"):
            # 提取归属ID
            parts = data.split("_")
            if len(parts) >= 4:
                callback_group_id = parts[3] if parts[3] != "ALL" else None
                if callback_group_id and callback_group_id != user_group_id:
                    await query.answer("❌ 您没有权限查看该归属ID的报表", show_alert=True)
                    return False
        elif data.startswith("report_menu_attribution") or data.startswith("report_search_orders"):
            # 限制用户不能使用归属查询和查找功能
            await query.answer("❌ 您没有权限使用此功能", show_alert=True)
            return False
    return True
