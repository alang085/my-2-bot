"""数据还原处理器"""

import logging
from typing import List, Optional, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

import db_operations
from decorators import admin_required, error_handler, private_chat_only
from handlers.module5_data.undo_operation_handlers import (
    _undo_expense, _undo_interest, _undo_order_breach_end,
    _undo_order_completed, _undo_order_created, _undo_order_state_change,
    _undo_principal_reduction)
from utils.date_helpers import get_daily_period_date

logger = logging.getLogger(__name__)


@error_handler
@admin_required
@private_chat_only
async def _parse_restore_date(
    context: ContextTypes.DEFAULT_TYPE,
) -> Tuple[str, Optional[str]]:
    """解析还原日期参数

    Args:
        context: 上下文对象

    Returns:
        (日期, 错误消息)
    """
    from utils.handler_helpers import parse_date_from_args

    if context.args and len(context.args) > 0:
        start_date, end_date, error_msg = parse_date_from_args(
            context, 0, allow_range=False
        )
        if error_msg:
            return "", error_msg
        return start_date, None
    else:
        return get_daily_period_date(), None


async def _validate_restore_operations(update: Update, date: str) -> Tuple[bool, List]:
    """验证还原操作

    Args:
        update: Telegram更新对象
        date: 日期

    Returns:
        (是否有效, 有效操作列表)
    """
    operations = await db_operations.get_operations_by_date(date)

    if not operations:
        await update.message.reply_text(
            f"📋 操作记录 ({date})\n\n" "暂无操作记录，无需还原"
        )
        return False, []

    valid_operations = [op for op in operations if op.get("is_undone", 0) == 0]

    if not valid_operations:
        await update.message.reply_text(
            f"📋 操作记录 ({date})\n\n" "所有操作都已被撤销，无需还原"
        )
        return False, []

    return True, valid_operations


def _build_restore_confirmation_message(date: str, operation_count: int) -> str:
    """构建还原确认消息

    Args:
        date: 日期
        operation_count: 操作数量

    Returns:
        消息文本
    """
    return (
        f"⚠️ 确认还原数据\n\n"
        f"日期: {date}\n"
        f"操作数: {operation_count} 条\n\n"
        f"此操作将按时间倒序撤销该日期的所有操作，还原到该日期开始前的状态。\n\n"
        f"⚠️ 警告：此操作不可恢复！"
    )


def _build_restore_confirmation_keyboard(date: str) -> InlineKeyboardMarkup:
    """构建还原确认键盘

    Args:
        date: 日期

    Returns:
        内联键盘
    """
    keyboard = [
        [
            InlineKeyboardButton(
                "✅ 确认还原", callback_data=f"confirm_restore_{date}"
            ),
            InlineKeyboardButton("❌ 取消", callback_data="cancel_restore"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def restore_daily_data(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """还原指定日期的数据（仅管理员）"""
    try:
        from utils.handler_helpers import send_error_message

        date, error_msg = await _parse_restore_date(context)
        if error_msg:
            await send_error_message(
                update,
                "❌ 日期格式错误\n"
                "正确格式: /restore_daily_data 2025-01-15\n"
                "或: /restore_daily_data (使用今天)\n\n"
                "⚠️ 警告：此操作将还原该日期的所有数据，请谨慎使用！",
            )
            return

        is_valid, valid_operations = await _validate_restore_operations(update, date)
        if not is_valid:
            return

        message = _build_restore_confirmation_message(date, len(valid_operations))
        reply_markup = _build_restore_confirmation_keyboard(date)
        await update.message.reply_text(message, reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"还原数据失败: {e}", exc_info=True)
        await update.message.reply_text(f"❌ 还原数据失败: {str(e)}")


async def _get_valid_operations(date: str) -> list:
    """获取并过滤有效的操作记录"""
    operations = await db_operations.get_operations_by_date(date)
    valid_operations = [op for op in operations if op.get("is_undone", 0) == 0]
    valid_operations.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return valid_operations


async def _execute_undo_operation(op: dict) -> tuple[bool, Optional[str]]:
    """执行单个撤销操作，返回(是否成功, 错误消息)"""
    operation_type = op.get("operation_type")
    operation_data = op.get("operation_data", {})

    undo_map = {
        "interest": _undo_interest,
        "principal_reduction": _undo_principal_reduction,
        "expense": _undo_expense,
        "order_completed": _undo_order_completed,
        "order_breach_end": _undo_order_breach_end,
        "order_created": _undo_order_created,
        "order_state_change": _undo_order_state_change,
    }

    undo_func = undo_map.get(operation_type)
    if not undo_func:
        return False, f"未知操作类型: {operation_type}"

    try:
        success = await undo_func(operation_data)
        if success:
            await db_operations.mark_operation_undone(op.get("id"))
            return True, None
        return False, f"操作 {op.get('id')} ({operation_type}) 还原失败"
    except Exception as e:
        error_msg = f"操作 {op.get('id')} ({operation_type}) 还原异常: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg


async def _execute_restore_operations(valid_operations: list) -> dict:
    """执行还原操作并返回结果"""
    total = len(valid_operations)
    success_count = 0
    fail_count = 0
    errors = []

    for op in valid_operations:
        success, error_msg = await _execute_undo_operation(op)
        if success:
            success_count += 1
        else:
            fail_count += 1
            if error_msg:
                errors.append(error_msg)

    from constants import MAX_DISPLAY_ITEMS

    return {
        "success": fail_count == 0,
        "total": total,
        "success_count": success_count,
        "fail_count": fail_count,
        "errors": errors[:MAX_DISPLAY_ITEMS],
    }


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
        valid_operations = await _get_valid_operations(date)

        if not valid_operations:
            return {
                "success": True,
                "total": 0,
                "success_count": 0,
                "fail_count": 0,
                "errors": [],
            }

        return await _execute_restore_operations(valid_operations)

    except Exception as e:
        logger.error(f"执行还原数据失败: {e}", exc_info=True)
        return {
            "success": False,
            "total": 0,
            "success_count": 0,
            "fail_count": 0,
            "errors": [str(e)],
        }
