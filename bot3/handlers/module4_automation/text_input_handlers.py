"""文本输入处理器（主路由函数）"""

# 标准库
import logging

# 第三方库
from telegram import Update
from telegram.ext import ContextTypes

# 本地模块
from decorators import error_handler
from handlers.module4_automation.order_input_helpers import \
    _handle_breach_end_amount
from handlers.module4_automation.text_input_routers import (
    route_config_states, route_finance_states, route_group_message_states,
    route_payment_states, route_schedule_states, route_search_states)

logger = logging.getLogger(__name__)


@error_handler
def _should_process_text_input(update: Update, user_state: str) -> bool:
    """判断是否应该处理文本输入"""
    if not update.message or not update.message.text:
        return False

    if update.message.text.startswith("+"):
        return False

    allow_group = user_state in ["WAITING_BREACH_END_AMOUNT", "BROADCAST_PAYMENT"]
    if update.effective_chat.type != "private" and not allow_group:
        return False

    return bool(user_state)


async def _handle_cancel_operation(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """处理取消操作"""
    context.user_data["state"] = None
    await update.message.reply_text("✅ Operation Cancelled")


async def _handle_group_allowed_states(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_state: str, text: str
) -> bool:
    """处理允许群组的状态，返回是否已处理"""
    if user_state == "WAITING_BREACH_END_AMOUNT":
        await _handle_breach_end_amount(update, context, text)
        return True

    if user_state == "BROADCAST_PAYMENT":
        from handlers.module4_automation.broadcast_handlers import \
            handle_broadcast_payment_input

        await handle_broadcast_payment_input(update, context, text)
        return True

    return False


async def _handle_announcement_interval_setting(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str
) -> None:
    """处理公告间隔设置"""
    if text.strip().lower() == "cancel":
        context.user_data["state"] = None
        await update.message.reply_text("✅ 操作已取消")
        return

    try:
        interval_hours = int(text.strip())
        if interval_hours < 1:
            await update.message.reply_text("❌ 间隔必须大于0，输入 'cancel' 取消")
            return

        success = await db_operations.save_announcement_schedule(
            interval_hours=interval_hours, is_active=1
        )

        if success:
            await update.message.reply_text(
                f"✅ 发送间隔已设置为 {interval_hours} 小时\n\n"
                f"注意：需要重启机器人才能生效"
            )
        else:
            await update.message.reply_text("❌ 设置失败")
    except ValueError:
        await update.message.reply_text("❌ 请输入有效的数字，输入 'cancel' 取消")
    except Exception as e:
        logger.error(f"设置公告间隔失败: {e}", exc_info=True)
        await update.message.reply_text(f"❌ 设置失败: {e}")

    context.user_data["state"] = None


async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理文本输入（用于搜索和群发）"""
    user_state = context.user_data.get("state")
    if not _should_process_text_input(update, user_state):
        return

    text = update.message.text.strip()

    if text.lower() == "cancel":
        await _handle_cancel_operation(update, context)
        return

    if await _handle_group_allowed_states(update, context, user_state, text):
        return

    if update.effective_chat.type != "private":
        return

    from handlers.module4_automation.text_input_route import \
        route_text_input_by_state

    if await route_text_input_by_state(update, context, user_state, text):
        return

    if user_state == "SETTING_ANNOUNCEMENT_INTERVAL":
        await _handle_announcement_interval_setting(update, context, text)
