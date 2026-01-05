"""白名单管理命令处理器"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from decorators import admin_required, error_handler, private_chat_only
from services.module6_credit import (add_to_whitelist, is_whitelisted,
                                     list_customers, remove_from_whitelist)
from utils.handler_helpers import send_success_or_error, validate_args

logger = logging.getLogger(__name__)


@error_handler
@admin_required
@private_chat_only
async def add_whitelist_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """添加到白名单"""
    if not await validate_args(update, context, 1, "❌ 用法: /add_whitelist <电话>"):
        return

    phone = context.args[0]
    success, error_msg = await add_to_whitelist(phone)
    await send_success_or_error(
        update, success, f"✅ 已添加到白名单: {phone}", error_msg or "❌ 添加失败"
    )


@error_handler
@admin_required
@private_chat_only
async def remove_whitelist_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """从白名单移除"""
    if not await validate_args(update, context, 1, "❌ 用法: /remove_whitelist <电话>"):
        return

    phone = context.args[0]
    success, error_msg = await remove_from_whitelist(phone)
    await send_success_or_error(
        update, success, f"✅ 已从白名单移除: {phone}", error_msg or "❌ 移除失败"
    )


@error_handler
@admin_required
@private_chat_only
async def list_whitelist_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """查看白名单"""
    customers = await list_customers("white")
    whitelisted = [c for c in customers if await is_whitelisted(c["phone"])]

    if not whitelisted:
        await update.message.reply_text("📋 白名单为空")
        return

    msg = f"📋 白名单（共{len(whitelisted)}个）\n━━━━━━━━━━━━━━━━━━━━\n"
    for i, customer in enumerate(whitelisted[:20], 1):
        msg += f"{i}. {customer['name']} ({customer['phone']})\n"

    if len(whitelisted) > 20:
        msg += f"\n... 还有 {len(whitelisted) - 20} 个未显示"

    await update.message.reply_text(msg)
