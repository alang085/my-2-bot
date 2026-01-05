"""用户组映射命令处理器"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from db.module1_user.users import (get_all_user_group_mappings,
                                   remove_user_group_id, set_user_group_id)
from db.module2_finance.finance import get_grouped_data
from decorators import admin_required, error_handler, private_chat_only
from utils.handler_helpers import (parse_user_id_from_args, send_error_message,
                                   validate_args_count)

logger = logging.getLogger(__name__)


@error_handler
@admin_required
@private_chat_only
async def set_user_group_id_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """设置用户有权限查看的归属ID（管理员命令）"""
    is_valid, error_msg = validate_args_count(
        context, 2, "/set_user_group_id <用户ID> <归属ID>"
    )
    if not is_valid:
        await send_error_message(update, error_msg)
        return

    user_id, error_msg = parse_user_id_from_args(context)
    if error_msg:
        await send_error_message(update, error_msg)
        return

    group_id = context.args[1].upper()

    # 验证归属ID是否存在
    grouped_data = await get_grouped_data(group_id)
    if not grouped_data:
        await send_error_message(update, f"❌ 归属ID {group_id} 不存在")
        return

    if await set_user_group_id(user_id, group_id):
        await update.message.reply_text(
            f"✅ 已设置用户 {user_id} 的归属ID权限为 {group_id}"
        )
    else:
        await send_error_message(update, "❌ 设置失败")


@error_handler
@admin_required
@private_chat_only
async def remove_user_group_id_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """移除用户的归属ID权限（管理员命令）"""
    user_id, error_msg = parse_user_id_from_args(context)
    if error_msg:
        await update.message.reply_text("用法: /remove_user_group_id <用户ID>")
        return

    if await remove_user_group_id(user_id):
        await update.message.reply_text(f"✅ 已移除用户 {user_id} 的归属ID权限")
    else:
        await update.message.reply_text("⚠️ 移除失败或用户不存在")


@error_handler
@admin_required
@private_chat_only
async def list_user_group_mappings(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """列出所有用户归属ID映射（管理员命令）"""
    mappings = await get_all_user_group_mappings()
    if not mappings:
        await update.message.reply_text("📋 暂无用户归属ID映射")
        return

    message = "📋 用户归属ID映射列表:\n\n"
    for mapping in mappings:
        message += (
            f"👤 用户ID: `{mapping['user_id']}` → 归属ID: `{mapping['group_id']}`\n"
        )

    await update.message.reply_text(message, parse_mode="Markdown")
