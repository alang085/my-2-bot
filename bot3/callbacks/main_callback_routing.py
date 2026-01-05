"""主回调路由模块

包含将回调数据路由到不同处理器的逻辑。
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from callbacks.payment_callbacks import handle_payment_callback
from callbacks.report_callbacks import handle_report_callback
from callbacks.search_callbacks import handle_search_callback
from handlers.data_access import get_user_authorization_status

logger = logging.getLogger(__name__)


async def route_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE, data: str, user_id: int
) -> bool:
    """路由回调到相应的处理器

    返回 True 如果已处理，False 如果未处理
    """
    query = update.callback_query

    # 对于报表回调、收入明细回调和订单总表回调，允许受限用户使用
    report_or_income_or_table = (
        data.startswith("report_")
        or data.startswith("income_")
        or data.startswith("order_table_")
        or data == "broadcast_start"
    )
    if report_or_income_or_table:
        if data.startswith("report_"):
            callback_name = "handle_report_callback"
            handler = handle_report_callback
        elif data.startswith("order_table_"):
            callback_name = "handle_report_callback (order_table)"
            handler = handle_report_callback
        else:
            callback_name = "handle_report_callback (income)"
            handler = handle_report_callback

        logger.debug(f"button_callback: routing {data} to {callback_name}")
        try:
            await handler(update, context)
        except Exception as e:
            logger.error(
                f"button_callback: error in {callback_name}: {e}", exc_info=True
            )
            try:
                await query.answer("❌ 处理回调时出错", show_alert=True)
            except Exception:
                pass
        return True

    # 检查授权（管理员或员工）
    from config import ADMIN_IDS

    is_admin = user_id in ADMIN_IDS
    is_authorized = await get_user_authorization_status(user_id)

    if not is_admin and not is_authorized:
        await query.answer("⚠️ Permission denied.", show_alert=True)
        return True

    # 必须先 answer，防止客户端转圈
    try:
        await query.answer()
    except Exception:
        pass  # 忽略 answer 错误（例如 query 已过期）

    # 记录日志以便排查
    logger.info(f"Processing callback: {data} from user {update.effective_user.id}")

    # 路由到不同的处理器
    if data.startswith("search_"):
        await handle_search_callback(update, context)
        return True
    elif data.startswith("payment_"):
        await handle_payment_callback(update, context)
        return True

    return False
