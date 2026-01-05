"""报表回调订单总表处理模块

包含订单总表相关的回调处理逻辑。
"""

import logging

from telegram.ext import ContextTypes

from callbacks.report_callbacks_base import MockUpdate
from config import ADMIN_IDS

logger = logging.getLogger(__name__)


async def handle_order_table_view(
    query, context: ContextTypes.DEFAULT_TYPE, user_id: int
) -> None:
    """处理订单总表查看"""
    if not user_id or user_id not in ADMIN_IDS:
        await query.answer("❌ 此功能仅限管理员使用", show_alert=True)
        return

    await query.answer()
    from handlers.module5_data.order_table_handlers import show_order_table

    # 使用共享的 MockUpdate 类
    mock_update = MockUpdate(query, context.bot)
    await show_order_table(mock_update, context)


async def handle_order_table_export_excel(
    query, context: ContextTypes.DEFAULT_TYPE, user_id: int
) -> None:
    """处理订单总表Excel导出"""
    if not user_id or user_id not in ADMIN_IDS:
        await query.answer("❌ 此功能仅限管理员使用", show_alert=True)
        return

    await query.answer("正在生成Excel文件，请稍候...")
    from handlers.module5_data.report_handlers import export_order_table_excel

    # 使用共享的 MockUpdate 类
    mock_update = MockUpdate(query, context.bot)
    await export_order_table_excel(mock_update, context)
