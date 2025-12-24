"""每日操作记录处理器"""

import logging
from datetime import datetime
from typing import Optional

import pytz
from telegram import Update
from telegram.ext import ContextTypes

import db_operations
from config import ADMIN_IDS
from decorators import admin_required, error_handler, private_chat_only
from utils.date_helpers import datetime_str_to_beijing_str, get_daily_period_date

logger = logging.getLogger(__name__)

# 操作类型的中文名称映射
OPERATION_TYPE_NAMES = {
    "order_created": "订单创建",
    "order_state_change": "订单状态变更",
    "order_completed": "订单完成",
    "order_breach_end": "违约完成",
    "interest": "利息收入",
    "principal_reduction": "本金减少",
    "expense": "开销记录",
    "funds_adjustment": "资金调整",
    "operation_undo": "撤销操作",
    "attribution_created": "创建归属ID",
    "employee_added": "添加员工",
    "employee_removed": "移除员工",
    "user_permission_set": "设置用户权限",
    "user_permission_removed": "移除用户权限",
    "weekday_groups_updated": "更新星期分组",
    "statistics_fixed": "修复统计数据",
    "operation_deleted": "删除操作记录",
    "daily_data_restored": "还原当天数据",
    "payment_account_balance_updated": "更新支付账号余额",
    "payment_account_updated": "更新支付账号信息",
    "other": "其他操作",
}


def format_operation_type(op_type: str) -> str:
    """格式化操作类型名称"""
    return OPERATION_TYPE_NAMES.get(op_type, op_type)


def format_operation_detail(operation: dict) -> str:
    """格式化单个操作的详细信息"""
    op_type = operation.get("operation_type", "unknown")
    op_data = operation.get("operation_data", {})
    created_at = operation.get("created_at", "")

    # 操作记录的 created_at 在存储时已经是北京时间字符串（无时区信息）
    # 直接使用，不需要再次转换，避免时区转换错误
    time_str = "无时间"
    if created_at:
        # 数据库存储的格式是 'YYYY-MM-DD HH:MM:SS'（已经是北京时间）
        # 直接使用，不进行时区转换
        if len(created_at) >= 19:
            time_str = created_at[:19]  # 取前19个字符（YYYY-MM-DD HH:MM:SS）
        elif " " in created_at:
            # 如果格式不完整，尝试提取日期和时间部分
            parts = created_at.split(" ")
            if len(parts) >= 2:
                time_str = f"{parts[0]} {parts[1][:8]}" if len(parts[1]) >= 8 else created_at
            else:
                time_str = created_at
        else:
            time_str = created_at

    detail = f"⏰ {time_str} | {format_operation_type(op_type)}"

    # 根据操作类型添加详细信息
    if op_type == "order_created":
        order_id = op_data.get("order_id", "N/A")
        amount = op_data.get("amount", 0)
        detail += f"\n   订单号: {order_id} | 金额: {amount:,.2f}"
    elif op_type == "order_state_change":
        old_state = op_data.get("old_state", "N/A")
        new_state = op_data.get("new_state", "N/A")
        detail += f"\n   {old_state} → {new_state}"
    elif op_type == "order_completed":
        amount = op_data.get("amount", 0)
        detail += f"\n   金额: {amount:,.2f}"
    elif op_type == "order_breach_end":
        amount = op_data.get("amount", 0)
        detail += f"\n   金额: {amount:,.2f}"
    elif op_type == "interest":
        amount = op_data.get("amount", 0)
        detail += f"\n   金额: {amount:,.2f}"
    elif op_type == "principal_reduction":
        amount = op_data.get("amount", 0)
        old_amount = op_data.get("old_amount", 0)
        new_amount = op_data.get("new_amount", 0)
        detail += f"\n   减少: {amount:,.2f} | {old_amount:,.2f} → {new_amount:,.2f}"
    elif op_type == "expense":
        amount = op_data.get("amount", 0)
        expense_type = op_data.get("type", "unknown")
        note = op_data.get("note", "")
        detail += f"\n   类型: {expense_type} | 金额: {amount:,.2f}"
        if note:
            detail += f"\n   备注: {note[:30]}"
    elif op_type == "operation_undo":
        undone_operation_id = op_data.get("undone_operation_id")
        undone_operation_type = op_data.get("undone_operation_type", "unknown")
        detail += f"\n   撤销的操作ID: {undone_operation_id} | 类型: {format_operation_type(undone_operation_type)}"
    elif op_type == "funds_adjustment":
        amount = op_data.get("amount", 0)
        adjustment_type = "增加" if amount > 0 else "减少"
        new_balance = op_data.get("new_balance", 0)
        note = op_data.get("note", "")
        detail += (
            f"\n   类型: {adjustment_type} | 金额: {abs(amount):,.2f} | 新余额: {new_balance:,.2f}"
        )
        if note:
            detail += f"\n   备注: {note[:30]}"
    elif op_type == "attribution_created":
        group_id = op_data.get("group_id", "N/A")
        detail += f"\n   归属ID: {group_id}"
    elif op_type == "employee_added":
        employee_id = op_data.get("employee_id")
        detail += f"\n   员工ID: {employee_id}"
    elif op_type == "employee_removed":
        employee_id = op_data.get("employee_id")
        detail += f"\n   员工ID: {employee_id}"
    elif op_type == "user_permission_set":
        user_id = op_data.get("user_id")
        group_id = op_data.get("group_id", "N/A")
        detail += f"\n   用户ID: {user_id} | 归属ID: {group_id}"
    elif op_type == "user_permission_removed":
        user_id = op_data.get("user_id")
        detail += f"\n   用户ID: {user_id}"
    elif op_type == "weekday_groups_updated":
        updated_count = op_data.get("updated_count", 0)
        skipped_count = op_data.get("skipped_count", 0)
        error_count = op_data.get("error_count", 0)
        detail += f"\n   已更新: {updated_count} | 跳过: {skipped_count} | 错误: {error_count}"
    elif op_type == "statistics_fixed":
        fixed_groups = op_data.get("fixed_groups", [])
        fixed_count = op_data.get("fixed_count", 0)
        detail += f"\n   修复的归属ID: {', '.join(fixed_groups[:5])}{'...' if len(fixed_groups) > 5 else ''} | 修复数量: {fixed_count}"
    elif op_type == "operation_deleted":
        operation_id = op_data.get("deleted_operation_id")
        deleted_operation_type = op_data.get("deleted_operation_type", "unknown")
        detail += f"\n   操作记录ID: {operation_id} | 类型: {format_operation_type(deleted_operation_type)}"
    elif op_type == "daily_data_restored":
        date = op_data.get("date", "N/A")
        total = op_data.get("total", 0)
        success_count = op_data.get("success_count", 0)
        fail_count = op_data.get("fail_count", 0)
        detail += f"\n   日期: {date} | 总数: {total} | 成功: {success_count} | 失败: {fail_count}"
    elif op_type == "payment_account_balance_updated":
        account_type = op_data.get("account_type", "unknown")
        old_balance = op_data.get("old_balance", 0)
        new_balance = op_data.get("new_balance", 0)
        account_id = op_data.get("account_id")
        if account_id:
            detail += f"\n   账户ID: {account_id} | 类型: {account_type} | {old_balance:,.2f} → {new_balance:,.2f}"
        else:
            detail += f"\n   类型: {account_type} | {old_balance:,.2f} → {new_balance:,.2f}"
    elif op_type == "payment_account_updated":
        account_type = op_data.get("account_type", "unknown")
        account_number = op_data.get("account_number", "N/A")
        account_name = op_data.get("account_name", "N/A")
        detail += f"\n   类型: {account_type} | 账号: {account_number} | 名称: {account_name[:20]}"

    if operation.get("is_undone", 0) == 1:
        detail += " [已撤销]"

    return detail


@error_handler
@private_chat_only
@admin_required
async def show_daily_operations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看指定日期的操作历史（仅管理员）"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    try:
        # 解析日期参数
        args = context.args if context.args else []
        date = None
        show_all = False

        if args:
            # 检查是否有 "all" 参数
            if "all" in [arg.lower() for arg in args]:
                show_all = True
                # 从参数中提取日期
                date_args = [arg for arg in args if arg.lower() != "all"]
                if date_args:
                    date_str = date_args[0]
                    try:
                        datetime.strptime(date_str, "%Y-%m-%d")
                        date = date_str
                    except ValueError:
                        await update.message.reply_text(
                            "❌ 日期格式错误\n"
                            "正确格式: /daily_operations 2025-01-15 [all]\n"
                            "或: /daily_operations [all] (使用今天)"
                        )
                        return
                else:
                    date = get_daily_period_date()
            else:
                date_str = args[0]
                try:
                    datetime.strptime(date_str, "%Y-%m-%d")
                    date = date_str
                except ValueError:
                    await update.message.reply_text(
                        "❌ 日期格式错误\n"
                        "正确格式: /daily_operations 2025-01-15 [all]\n"
                        "或: /daily_operations [all] (使用今天)"
                    )
                    return
        else:
            date = get_daily_period_date()

        # 获取操作历史
        operations = await db_operations.get_operations_by_date(date)

        if not operations:
            await update.message.reply_text(f"📋 操作记录 ({date})\n\n" "暂无操作记录")
            return

        # 如果请求显示全部，或者操作数少于50条，显示完整列表
        if show_all or len(operations) <= 50:
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

            # 发送所有部分
            for i, part in enumerate(message_parts, 1):
                if i == 1:
                    # 第一段添加按钮
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
                    await update.message.reply_text(part, reply_markup=reply_markup)
                else:
                    await update.message.reply_text(part)
        else:
            # 显示前50条，提供查看全部的选项
            message = f"📋 操作记录 ({date})\n"
            message += "═══════════════════════════════════════\n"
            message += f"总操作数: {len(operations)}\n"
            message += f"显示前 50 条（共 {len(operations)} 条）\n\n"

            for i, op in enumerate(operations[:50], 1):
                message += f"{i}. {format_operation_detail(op)}\n"

            message += f"\n... 还有 {len(operations) - 50} 条操作未显示"

            keyboard = [
                [
                    InlineKeyboardButton(
                        "📋 显示完整记录", callback_data=f"show_all_operations_{date}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔄 还原当天数据", callback_data=f"restore_daily_data_{date}"
                    )
                ],
                [InlineKeyboardButton("📊 查看汇总", callback_data=f"daily_ops_summary_{date}")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"查看操作记录失败: {e}", exc_info=True)
        await update.message.reply_text(f"❌ 查看操作记录失败: {str(e)}")


@error_handler
@private_chat_only
@admin_required
async def show_daily_operations_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看指定日期的操作汇总（仅管理员）"""
    try:
        # 解析日期参数
        args = context.args if context.args else []
        date = None

        if args:
            date_str = args[0]
            try:
                # 验证日期格式
                datetime.strptime(date_str, "%Y-%m-%d")
                date = date_str
            except ValueError:
                await update.message.reply_text(
                    "❌ 日期格式错误\n"
                    "正确格式: /daily_operations_summary 2025-01-15\n"
                    "或: /daily_operations_summary (使用今天)"
                )
                return
        else:
            date = get_daily_period_date()

        # 获取汇总统计
        summary = await db_operations.get_daily_operations_summary(date)

        if not summary or summary.get("total_count", 0) == 0:
            await update.message.reply_text(f"📊 操作汇总 ({date})\n\n" "暂无操作记录")
            return

        # 格式化消息
        message = f"📊 操作汇总 ({date})\n"
        message += "═══════════════════════════════════════\n"
        message += f"总操作数: {summary['total_count']}\n"
        message += f"有效操作: {summary['valid_count']}\n"
        message += f"已撤销: {summary['undone_count']}\n\n"

        # 按操作类型统计
        if summary.get("by_type"):
            message += "📋 按操作类型:\n"
            for op_type, count in sorted(
                summary["by_type"].items(), key=lambda x: x[1], reverse=True
            ):
                message += f"  {format_operation_type(op_type)}: {count} 次\n"
            message += "\n"

        # 按用户统计
        if summary.get("by_user"):
            message += "👥 按用户:\n"
            # 只显示前10个用户
            user_stats = sorted(summary["by_user"].items(), key=lambda x: x[1], reverse=True)[:10]
            for user_id, count in user_stats:
                message += f"  用户 {user_id}: {count} 次\n"
            if len(summary["by_user"]) > 10:
                message += f"  ... 还有 {len(summary['by_user']) - 10} 个用户\n"

        await update.message.reply_text(message)

    except Exception as e:
        logger.error(f"查看操作汇总失败: {e}", exc_info=True)
        await update.message.reply_text(f"❌ 查看操作汇总失败: {str(e)}")
