"""撤销操作服务 - 封装撤销相关的业务逻辑"""

import logging
from typing import Any, Dict, Optional, Tuple

import db_operations
from utils.date_helpers import get_daily_period_date

logger = logging.getLogger(__name__)


class UndoService:
    """撤销操作业务服务"""

    @staticmethod
    async def get_last_operation(
        user_id: int, chat_id: int, date: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """获取最后一个操作

        Args:
            user_id: 用户ID
            chat_id: 聊天ID
            date: 日期（可选，默认今天）

        Returns:
            操作记录字典，如果不存在则返回 None
        """
        if date is None:
            date = get_daily_period_date()
        return await db_operations.get_last_operation(user_id, chat_id, date)

    @staticmethod
    async def mark_operation_as_undone(operation_id: int) -> Tuple[bool, Optional[str]]:
        """标记操作为已撤销

        Args:
            operation_id: 操作ID

        Returns:
            Tuple[success, error_message]:
                - success: 是否成功
                - error_message: 错误消息（如果失败）
        """
        try:
            success = await db_operations.mark_operation_as_undone(operation_id)
            if success:
                return True, None
            else:
                return False, "❌ 标记操作失败"
        except Exception as e:
            logger.error(f"标记操作失败: {e}", exc_info=True)
            return False, f"❌ 标记操作失败: {str(e)}"

    @staticmethod
    async def record_undo_operation(
        user_id: int,
        chat_id: int,
        undone_operation_id: int,
        undone_operation_type: str,
    ) -> Tuple[bool, Optional[str]]:
        """记录撤销操作

        Args:
            user_id: 用户ID
            chat_id: 聊天ID
            undone_operation_id: 被撤销的操作ID
            undone_operation_type: 被撤销的操作类型

        Returns:
            Tuple[success, error_message]:
                - success: 是否成功
                - error_message: 错误消息（如果失败）
        """
        try:
            await db_operations.record_operation(
                user_id=user_id,
                operation_type="operation_undo",
                operation_data={
                    "undone_operation_id": undone_operation_id,
                    "undone_operation_type": undone_operation_type,
                },
                chat_id=chat_id,
            )
            return True, None
        except Exception as e:
            logger.error(f"记录撤销操作失败: {e}", exc_info=True)
            return False, f"❌ 记录撤销操作失败: {str(e)}"
