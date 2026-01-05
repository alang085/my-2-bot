"""黑名单管理命令处理器"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from decorators import admin_required, error_handler, private_chat_only
from services.module6_credit import (add_to_blacklist, is_blacklisted,
                                     list_customers, remove_from_blacklist)
from utils.handler_helpers import send_success_or_error, validate_args

logger = logging.getLogger(__name__)


@error_handler
@admin_required
@private_chat_only
async def add_blacklist_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """添加到黑名单"""
    if not await validate_args(update, context, 1, "❌ 用法: /add_blacklist <电话>"):
        return

    phone = context.args[0]
    success, error_msg = await add_to_blacklist(phone)
    await send_success_or_error(
        update, success, f"✅ 已添加到黑名单: {phone}", error_msg or "❌ 添加失败"
    )


@error_handler
@admin_required
@private_chat_only
async def remove_blacklist_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """从黑名单移除"""
    if not await validate_args(update, context, 1, "❌ 用法: /remove_blacklist <电话>"):
        return

    phone = context.args[0]
    success, error_msg = await remove_from_blacklist(phone)
    await send_success_or_error(
        update, success, f"✅ 已从黑名单移除: {phone}", error_msg or "❌ 移除失败"
    )


@error_handler
@admin_required
@private_chat_only
async def list_blacklist_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """查看黑名单"""
    customers = await list_customers("black")
    blacklisted = [c for c in customers if await is_blacklisted(c["phone"])]

    if not blacklisted:
        await update.message.reply_text("📋 黑名单为空")
        return

    msg = f"📋 黑名单（共{len(blacklisted)}个）\n━━━━━━━━━━━━━━━━━━━━\n"
    for i, customer in enumerate(blacklisted[:20], 1):
        msg += f"{i}. {customer['name']} ({customer['phone']})\n"

    if len(blacklisted) > 20:
        msg += f"\n... 还有 {len(blacklisted) - 20} 个未显示"

    await update.message.reply_text(msg)
