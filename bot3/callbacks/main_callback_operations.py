"""主回调操作记录处理模块

包含操作记录相关的回调处理逻辑。
"""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from handlers.module5_data.daily_operations_handlers import (format_operation_detail,
                                                show_daily_operations_summary)
from handlers.data_access import (get_operations_by_date_for_callback,
                                  record_operation_for_callback)
from handlers.module5_data.restore_handlers import execute_restore_daily_data

logger = logging.getLogger(__name__)


async def handle_show_all_operations(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query, data: str
) -> None:
    """显示完整操作记录"""
    date = data.replace("show_all_operations_", "")
    await query.answer("正在加载完整记录...")

    try:
        operations = await get_operations_by_date_for_callback(date)

        if not operations:
            await query.edit_message_text(f"📋 完整操作记录 ({date})\n\n暂无操作记录")
            return

        # 分段发送完整记录
        max_length = 4000
        current_message = f"📋 完整操作记录 ({date})\n"
        current_message += "═══════════════════════════════════════\n"
        current_message += f"总操作数: {len(operations)}\n\n"

        message_parts = [current_message]
        current_part = ""

        for i, op in enumerate(operations, 1):
            op_detail = f"{i}. {format_operation_detail(op)}\n"

            if len(current_part + op_detail) > max_length:
                message_parts.append(current_part)
                current_part = op_detail
            else:
                current_part += op_detail

        if current_part:
            message_parts.append(current_part)

        # 发送第一部分（带按钮）
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔄 还原当天数据", callback_data=f"restore_daily_data_{date}"
                )
            ],
            [
                InlineKeyboardButton(
                    "📊 查看汇总", callback_data=f"daily_ops_summary_{date}"
                )
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            await query.edit_message_text(message_parts[0], reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"编辑消息失败: {e}", exc_info=True)
            await query.answer("显示失败", show_alert=True)
            return

        # 发送其余部分
        for part in message_parts[1:]:
            try:
                await query.message.reply_text(part)
            except Exception as e:
                logger.error(f"发送消息部分失败: {e}", exc_info=True)

    except Exception as e:
        logger.error(f"显示完整操作记录失败: {e}", exc_info=True)
        await query.answer(f"显示失败: {str(e)[:50]}", show_alert=True)


async def handle_restore_daily_data(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query, data: str
) -> None:
    """还原当天数据（显示确认）"""
    date = data.replace("restore_daily_data_", "")
    await query.answer()

    try:
        operations = await get_operations_by_date_for_callback(date)
        valid_operations = [op for op in operations if op.get("is_undone", 0) == 0]

        if not valid_operations:
            await query.edit_message_text(
                f"📋 操作记录 ({date})\n\n" "所有操作都已被撤销，无需还原"
            )
            return

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
                InlineKeyboardButton(
                    "✅ 确认还原", callback_data=f"confirm_restore_{date}"
                ),
                InlineKeyboardButton("❌ 取消", callback_data="cancel_restore"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            await query.edit_message_text(message, reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"编辑消息失败: {e}", exc_info=True)
            await query.answer("显示失败", show_alert=True)

    except Exception as e:
        logger.error(f"准备还原数据失败: {e}", exc_info=True)
        await query.answer(f"准备失败: {str(e)[:50]}", show_alert=True)


async def handle_confirm_restore(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query, data: str
) -> None:
    """确认还原数据"""
    date = data.replace("confirm_restore_", "")
    await query.answer("正在还原数据，请稍候...")

    try:
        result = await execute_restore_daily_data(date)

        # 记录操作历史
        user_id = query.from_user.id if query.from_user else None
        current_chat_id = query.message.chat.id if query.message else None
        if current_chat_id and user_id:
            await record_operation_for_callback(
                user_id=user_id,
                operation_type="daily_data_restored",
                operation_data={
                    "date": date,
                    "total": result.get("total", 0),
                    "success_count": result.get("success_count", 0),
                    "fail_count": result.get("fail_count", 0),
                },
                chat_id=current_chat_id,
            )

        if result["success"]:
            message = (
                f"✅ 数据还原完成\n\n"
                f"日期: {date}\n"
                f"总操作数: {result['total']}\n"
                f"成功还原: {result['success_count']}\n"
                f"失败: {result['fail_count']}\n\n"
                f"所有操作已标记为已撤销"
            )
        else:
            message = (
                f"⚠️ 数据还原部分完成\n\n"
                f"日期: {date}\n"
                f"总操作数: {result['total']}\n"
                f"成功还原: {result['success_count']}\n"
                f"失败: {result['fail_count']}\n\n"
            )

            if result["errors"]:
                message += "错误信息:\n"
                for error in result["errors"][:5]:
                    message += f"  - {error}\n"
                if len(result["errors"]) > 5:
                    message += f"  ... 还有 {len(result['errors']) - 5} 个错误\n"

        try:
            await query.edit_message_text(message)
        except Exception as e:
            logger.error(f"编辑消息失败: {e}", exc_info=True)
            await query.answer("还原完成，但显示失败", show_alert=True)

    except Exception as e:
        logger.error(f"还原数据失败: {e}", exc_info=True)
        await query.answer(f"还原失败: {str(e)[:50]}", show_alert=True)


async def handle_cancel_restore(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """取消还原操作"""
    await query.answer("已取消")
    await query.edit_message_text("❌ 还原操作已取消")


async def handle_daily_ops_summary(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query, data: str
) -> None:
    """查看操作汇总"""
    date = data.replace("daily_ops_summary_", "")
    await query.answer("正在加载汇总...")

    try:
        # 临时设置context.args来传递日期
        context.args = [date]
        await show_daily_operations_summary(update, context)
        await query.delete_message()
    except Exception as e:
        logger.error(f"显示汇总失败: {e}", exc_info=True)
        await query.answer(f"显示失败: {str(e)[:50]}", show_alert=True)
