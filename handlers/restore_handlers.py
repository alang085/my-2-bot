"""数据还原处理器"""

import logging
from datetime import datetime
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

import db_operations
from config import ADMIN_IDS
from decorators import admin_required, error_handler, private_chat_only
from handlers.undo_handlers import (
    _undo_expense,
    _undo_interest,
    _undo_order_breach_end,
    _undo_order_completed,
    _undo_order_created,
    _undo_order_state_change,
    _undo_principal_reduction,
)
from utils.date_helpers import get_daily_period_date

logger = logging.getLogger(__name__)


@error_handler
@private_chat_only
@admin_required
async def restore_daily_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """还原指定日期的数据（仅管理员）"""
    try:
        # 解析日期参数
        args = context.args if context.args else []
        date = None

        if args:
            date_str = args[0]
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
                date = date_str
            except ValueError:
                await update.message.reply_text(
                    "❌ 日期格式错误\n"
                    "正确格式: /restore_daily_data 2025-01-15\n"
                    "或: /restore_daily_data (使用今天)\n\n"
                    "⚠️ 警告：此操作将还原该日期的所有数据，请谨慎使用！"
                )
                return
        else:
            date = get_daily_period_date()

        # 获取该日期的所有操作记录（按时间倒序，从最新到最旧）
        operations = await db_operations.get_operations_by_date(date)

        if not operations:
            await update.message.reply_text(f"📋 操作记录 ({date})\n\n" "暂无操作记录，无需还原")
            return

        # 过滤出未撤销的操作
        valid_operations = [op for op in operations if op.get("is_undone", 0) == 0]

        if not valid_operations:
            await update.message.reply_text(
                f"📋 操作记录 ({date})\n\n" "所有操作都已被撤销，无需还原"
            )
            return

        # 显示确认信息
        operation_count = len(valid_operations)
        message = (
            f"⚠️ 确认还原数据\n\n"
            f"日期: {date}\n"
            f"操作数: {operation_count} 条\n\n"
            f"此操作将按时间倒序撤销该日期的所有操作，还原到该日期开始前的状态。\n\n"
            f"⚠️ 警告：此操作不可恢复！"
        )

        keyboard = [
            [
                InlineKeyboardButton("✅ 确认还原", callback_data=f"confirm_restore_{date}"),
                InlineKeyboardButton("❌ 取消", callback_data="cancel_restore"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message, reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"还原数据失败: {e}", exc_info=True)
        await update.message.reply_text(f"❌ 还原数据失败: {str(e)}")


async def execute_restore_daily_data(date: str) -> dict:
    """执行还原指定日期的数据

    Returns:
        {
            'success': bool,
            'total': int,
            'success_count': int,
            'fail_count': int,
            'errors': list
        }
    """
    try:
        # 获取该日期的所有操作记录（按时间倒序，从最新到最旧）
        operations = await db_operations.get_operations_by_date(date)

        # 过滤出未撤销的操作，并按时间倒序排列（最新的先还原）
        valid_operations = [op for op in operations if op.get("is_undone", 0) == 0]

        # 按时间倒序排序（最新的在前）
        valid_operations.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        if not valid_operations:
            return {"success": True, "total": 0, "success_count": 0, "fail_count": 0, "errors": []}

        total = len(valid_operations)
        success_count = 0
        fail_count = 0
        errors = []

        # 按时间倒序执行撤销操作
        for op in valid_operations:
            operation_type = op.get("operation_type")
            operation_data = op.get("operation_data", {})
            operation_id = op.get("id")

            try:
                success = False

                if operation_type == "interest":
                    success = await _undo_interest(operation_data)
                elif operation_type == "principal_reduction":
                    success = await _undo_principal_reduction(operation_data)
                elif operation_type == "expense":
                    success = await _undo_expense(operation_data)
                elif operation_type == "order_completed":
                    success = await _undo_order_completed(operation_data)
                elif operation_type == "order_breach_end":
                    success = await _undo_order_breach_end(operation_data)
                elif operation_type == "order_created":
                    success = await _undo_order_created(operation_data)
                elif operation_type == "order_state_change":
                    success = await _undo_order_state_change(operation_data)
                else:
                    logger.warning(f"未知的操作类型: {operation_type}")
                    errors.append(f"未知操作类型: {operation_type}")
                    fail_count += 1
                    continue

                if success:
                    # 标记操作为已撤销
                    await db_operations.mark_operation_undone(operation_id)
                    success_count += 1
                else:
                    fail_count += 1
                    errors.append(f"操作 {operation_id} ({operation_type}) 还原失败")

            except Exception as e:
                fail_count += 1
                error_msg = f"操作 {operation_id} ({operation_type}) 还原异常: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg, exc_info=True)

        return {
            "success": fail_count == 0,
            "total": total,
            "success_count": success_count,
            "fail_count": fail_count,
            "errors": errors[:10],  # 只返回前10个错误
        }

    except Exception as e:
        logger.error(f"执行还原数据失败: {e}", exc_info=True)
        return {
            "success": False,
            "total": 0,
            "success_count": 0,
            "fail_count": 0,
            "errors": [str(e)],
        }
