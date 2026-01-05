"""报表回调 - 验证模块

包含验证报表回调请求的逻辑。
"""

import logging
from typing import Optional, Tuple

from telegram import CallbackQuery, Update
from telegram.ext import ContextTypes

from handlers.data_access import get_user_group_id

# check_user_permission 在 report_callbacks_base.py 中定义
# 导入将在运行时动态处理

logger = logging.getLogger(__name__)


async def validate_report_callback(
    update: Update, query: CallbackQuery
) -> Tuple[bool, Optional[int], Optional[str]]:
    """验证报表回调请求

    Args:
        update: Telegram更新对象
        query: 回调查询对象

    Returns:
        Tuple: (是否有效, 用户ID, 用户归属ID)
    """
    data = query.data
    if not data:
        logger.error("handle_report_callback: data is None")
        return False, None, None

    logger.debug(f"handle_report_callback: processing callback data={data}")

    # 获取用户ID
    user_id = update.effective_user.id if update.effective_user else None
    if not user_id:
        logger.error("handle_report_callback: user_id is None")
        try:
            await query.answer("❌ 无法获取用户信息", show_alert=True)
        except Exception as e:
            logger.error(f"handle_report_callback: failed to answer query: {e}")
        return False, None, None

    # 检查用户是否有权限查看特定归属ID的报表
    from callbacks.report_callbacks_base import check_user_permission

    user_group_id = await get_user_group_id(user_id)
    if not await check_user_permission(user_id, user_group_id, data, query):
        return False, None, None

    return True, user_id, user_group_id
