"""Handler上下文类

封装常用handler操作的上下文类。
"""

# 标准库
from typing import Any, Dict, Optional, Tuple

from telegram import Update

from utils.chat_helpers import is_group_chat
from utils.formatting_helpers import format_error
from utils.message_helpers import send_bilingual_message, send_success_message
from utils.models import OrderModel, OrderStateModel
from utils.order_validation_helpers import validate_and_get_order
from utils.permission_helpers import require_permission
from utils.update_info import get_chat_info, get_user_id


class HandlerContext:
    """Handler上下文类，封装常用操作"""

    def __init__(self, update: Update, context: Any):
        """初始化Handler上下文

        Args:
            update: Telegram Update 对象
            context: ContextTypes.DEFAULT_TYPE 对象
        """
        self.update = update
        self.context = context
        self._chat_id: Optional[int] = None
        self._user_id: Optional[int] = None
        self._is_group: Optional[bool] = None
        self._reply_func: Optional[Any] = None

    @property
    def chat_id(self) -> Optional[int]:
        """获取聊天ID"""
        if self._chat_id is None:
            self._chat_id, self._reply_func = get_chat_info(self.update)
        return self._chat_id

    @property
    def user_id(self) -> Optional[int]:
        """获取用户ID"""
        if self._user_id is None:
            self._user_id = get_user_id(self.update)
        return self._user_id

    @property
    def is_group(self) -> bool:
        """判断是否为群聊"""
        if self._is_group is None:
            self._is_group = is_group_chat(self.update)
        return self._is_group

    @property
    def reply_func(self) -> Optional[Any]:
        """获取回复函数"""
        if self._reply_func is None:
            _, self._reply_func = get_chat_info(self.update)
        return self._reply_func

    async def send_message(self, message: str) -> None:
        """发送消息

        注意：由于消息发送规则（群组英文，私聊中文），
        如果只有一个消息字符串，将同时作为英文和中文消息使用。
        """
        await send_bilingual_message(self.update, message, message)

    async def send_error(
        self, error: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """发送错误消息"""
        error_msg = format_error(error, details, self.is_group)
        await self.send_message(error_msg)

    async def send_success(
        self, short_message: str, detailed_message: Optional[str] = None
    ) -> None:
        """发送成功消息"""
        message = send_success_message(
            self.update, short_message, detailed_message, self.is_group
        )
        await self.send_message(message)

    async def get_order(
        self,
        allowed_states: Optional[Tuple[str, ...]] = None,
        validate_amount_field: bool = False,
    ) -> Tuple[
        Optional[OrderModel], Optional[OrderStateModel], Optional[float], Optional[str]
    ]:
        """获取并验证订单"""
        return await validate_and_get_order(
            self.update, self.chat_id, allowed_states, validate_amount_field
        )

    async def check_permission(
        self, require_admin: bool = False, require_authorized: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """检查权限"""
        return await require_permission(self.update, require_admin, require_authorized)
