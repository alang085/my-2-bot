"""文本输入路由辅助函数

包含根据用户状态路由到不同处理函数的辅助函数。
"""

# 标准库
import logging

# 第三方库
from telegram import Update
from telegram.ext import ContextTypes

# 本地模块
from handlers.module4_automation.finance_input_helpers import (
    _handle_expense_input, _handle_expense_query, _handle_income_query_date)
from handlers.module4_automation.group_message_input_helpers import (
    _handle_broadcast, _handle_set_bot_links, _handle_set_worker_links)
from handlers.module4_automation.order_input_helpers import \
    _handle_breach_end_amount
from handlers.module4_automation.payment_input_helpers import (
    _handle_add_account, _handle_edit_account, _handle_edit_account_by_id,
    _handle_update_balance, _handle_update_balance_by_id)
from handlers.module4_automation.report_input_helpers import \
    _handle_report_query
from handlers.module4_automation.search_input_helpers import (
    _handle_report_search, _handle_search_amount_input, _handle_search_input)

logger = logging.getLogger(__name__)


async def route_finance_states(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_state: str, text: str
) -> bool:
    """路由财务相关状态"""
    if user_state in ["QUERY_EXPENSE_COMPANY", "QUERY_EXPENSE_OTHER"]:
        await _handle_expense_query(update, context, text, user_state)
        return True

    if user_state in ["WAITING_EXPENSE_COMPANY", "WAITING_EXPENSE_OTHER"]:
        await _handle_expense_input(update, context, text, user_state)
        return True

    if user_state == "QUERY_INCOME":
        from handlers.module2_finance.income_handlers import \
            handle_income_query_input

        await handle_income_query_input(update, context, text)
        return True

    if user_state == "INCOME_QUERY_DATE":
        await _handle_income_query_date(update, context, text)
        return True

    return False


async def route_search_states(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_state: str, text: str
) -> bool:
    """路由搜索相关状态"""
    if user_state == "SEARCHING":
        await _handle_search_input(update, context, text)
        return True

    if user_state == "SEARCHING_AMOUNT":
        await _handle_search_amount_input(update, context, text)
        return True

    if user_state == "REPORT_QUERY":
        await _handle_report_query(update, context, text)
        return True

    if user_state == "REPORT_SEARCHING":
        await _handle_report_search(update, context, text)
        return True

    return False


async def route_payment_states(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_state: str, text: str
) -> bool:
    """路由支付账户相关状态"""
    if user_state == "UPDATING_BALANCE_GCASH":
        await _handle_update_balance(update, context, text, "gcash")
        return True

    if user_state == "UPDATING_BALANCE_PAYMAYA":
        await _handle_update_balance(update, context, text, "paymaya")
        return True

    if user_state == "EDITING_ACCOUNT_GCASH":
        await _handle_edit_account(update, context, text, "gcash")
        return True

    if user_state == "EDITING_ACCOUNT_PAYMAYA":
        await _handle_edit_account(update, context, text, "paymaya")
        return True

    if user_state == "ADDING_ACCOUNT_GCASH":
        await _handle_add_account(update, context, text, "gcash")
        return True

    if user_state == "ADDING_ACCOUNT_PAYMAYA":
        await _handle_add_account(update, context, text, "paymaya")
        return True

    if user_state == "EDITING_ACCOUNT_BY_ID_GCASH":
        await _handle_edit_account_by_id(update, context, text, "gcash")
        return True

    if user_state == "EDITING_ACCOUNT_BY_ID_PAYMAYA":
        await _handle_edit_account_by_id(update, context, text, "paymaya")
        return True

    if user_state and user_state.startswith("UPDATING_BALANCE_BY_ID_"):
        await _handle_update_balance_by_id(update, context, text)
        return True

    return False


async def route_group_message_states(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_state: str, text: str
) -> bool:
    """路由群组消息相关状态"""
    if user_state == "BROADCASTING":
        await _handle_broadcast(update, context, text)
        return True

    from constants import USER_STATES

    setting_bot_links_prefix = f"{USER_STATES['SETTING_BOT_LINKS']}_"
    if user_state and user_state.startswith(setting_bot_links_prefix):
        await _handle_set_bot_links(update, context, text)
        return True

    setting_worker_links_prefix = f"{USER_STATES['SETTING_WORKER_LINKS']}_"
    if user_state and user_state.startswith(setting_worker_links_prefix):
        await _handle_set_worker_links(update, context, text)
        return True

    return False


async def _handle_adding_group_config(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str
) -> None:
    """处理添加总群配置"""
    import db_operations

    if text.strip().lower() == "cancel":
        context.user_data["state"] = None
        await update.message.reply_text("✅ 操作已取消")
        return

    try:
        chat_id = int(text.strip())

        try:
            chat = await context.bot.get_chat(chat_id)
            chat_title = chat.title or "未设置"
        except Exception:
            chat_title = "未设置"

        success = await db_operations.save_group_message_config(
            chat_id=chat_id, chat_title=chat_title, is_active=1
        )

        if success:
            await update.message.reply_text(
                f"✅ 总群配置已添加\n\n"
                f"群组ID: {chat_id}\n"
                f"群组名称: {chat_title}\n\n"
                f"请使用 /groupmsg 设置消息内容"
            )
        else:
            await update.message.reply_text("❌ 添加失败，可能已存在")
        context.user_data["state"] = None
    except ValueError:
        await update.message.reply_text("❌ 群组ID必须是数字")
    except Exception as e:
        logger.error(f"添加总群配置失败: {e}", exc_info=True)
        await update.message.reply_text(f"❌ 添加失败: {e}")
        context.user_data["state"] = None


async def _handle_adding_announcement(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str
) -> None:
    """处理添加公告"""
    import db_operations

    if text.strip().lower() == "cancel":
        context.user_data["state"] = None
        await update.message.reply_text("✅ 操作已取消")
        return

    try:
        ann_id = await db_operations.save_company_announcement(text.strip())
        if ann_id:
            await update.message.reply_text(f"✅ 公告已添加 (ID: {ann_id})")
        else:
            await update.message.reply_text("❌ 添加失败")
    except Exception as e:
        logger.error(f"添加公告失败: {e}", exc_info=True)
        await update.message.reply_text(f"❌ 添加失败: {e}")

    context.user_data["state"] = None


async def _handle_adding_antifraud_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str
) -> None:
    """处理添加防诈骗语录"""
    import db_operations

    if text.strip().lower() == "cancel":
        context.user_data["state"] = None
        await update.message.reply_text("✅ 操作已取消")
        return

    try:
        msg_id = await db_operations.save_anti_fraud_message(text.strip())
        if msg_id:
            await update.message.reply_text(f"✅ 防诈骗语录已添加 (ID: {msg_id})")
        else:
            await update.message.reply_text("❌ 添加失败")
    except Exception as e:
        logger.error(f"添加防诈骗语录失败: {e}", exc_info=True)
        await update.message.reply_text(f"❌ 添加失败: {e}")

    context.user_data["state"] = None


async def _handle_adding_promotion_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str
) -> None:
    """处理添加公司宣传轮播语录"""
    import db_operations

    if text.strip().lower() == "cancel":
        context.user_data["state"] = None
        await update.message.reply_text("✅ 操作已取消")
        return

    try:
        msg_id = await db_operations.save_promotion_message(text.strip())
        if msg_id:
            await update.message.reply_text(f"✅ 公司宣传轮播语录已添加 (ID: {msg_id})")
        else:
            await update.message.reply_text("❌ 添加失败")
    except Exception as e:
        logger.error(f"添加公司宣传轮播语录失败: {e}", exc_info=True)
        await update.message.reply_text(f"❌ 添加失败: {e}")

    context.user_data["state"] = None


async def route_config_states(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_state: str, text: str
) -> bool:
    """路由配置相关状态"""
    if user_state == "ADDING_GROUP_CONFIG":
        await _handle_adding_group_config(update, context, text)
        return True

    if user_state == "ADDING_ANNOUNCEMENT":
        await _handle_adding_announcement(update, context, text)
        return True

    if user_state == "ADDING_ANTIFRAUD_MESSAGE":
        await _handle_adding_antifraud_message(update, context, text)
        return True

    if user_state == "ADDING_PROMOTION_MESSAGE":
        await _handle_adding_promotion_message(update, context, text)
        return True

    return False


async def route_schedule_states(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_state: str
) -> bool:
    """路由定时播报相关状态"""
    if user_state and user_state.startswith("SCHEDULE_"):
        from handlers.module4_automation.schedule_handlers import \
            handle_schedule_input

        handled = await handle_schedule_input(update, context)
        return handled

    return False
