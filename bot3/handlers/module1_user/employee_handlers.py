"""员工管理命令处理器"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from db.module1_user.users import (add_authorized_user, get_authorized_users,
                                   remove_authorized_user)
from decorators import admin_required, error_handler, private_chat_only
from utils.handler_helpers import parse_user_id_from_args

logger = logging.getLogger(__name__)


@error_handler
@admin_required
@private_chat_only
async def add_employee(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """添加员工（授权用户）"""
    user_id, error_msg = parse_user_id_from_args(context)
    if error_msg:
        await update.message.reply_text("用法: /add_employee <用户ID>")
        return

    if await add_authorized_user(user_id):
        await update.message.reply_text(f"✅ 已添加员工: {user_id}")
    else:
        await update.message.reply_text("⚠️ 添加失败或用户已存在")


@error_handler
@admin_required
@private_chat_only
async def remove_employee(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """移除员工（授权用户）"""
    user_id, error_msg = parse_user_id_from_args(context)
    if error_msg:
        await update.message.reply_text("用法: /remove_employee <用户ID>")
        return

    if await remove_authorized_user(user_id):
        await update.message.reply_text(f"✅ 已移除员工: {user_id}")
    else:
        await update.message.reply_text("⚠️ 移除失败或用户不存在")


@error_handler
@admin_required
@private_chat_only
async def list_employees(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """列出所有员工"""
    users = await get_authorized_users()
    if not users:
        await update.message.reply_text("📋 暂无授权员工")
        return

    message = "📋 授权员工列表:\n\n"
    for uid in users:
        message += f"👤 `{uid}`\n"

    await update.message.reply_text(message, parse_mode="Markdown")
