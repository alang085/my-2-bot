"""增量报表合并回调处理器"""

# 标准库
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

# 本地模块
import db_operations
from config import ADMIN_IDS
from utils.incremental_report_generator import get_or_create_baseline_date, prepare_incremental_data
from utils.incremental_report_merger import (
    calculate_incremental_stats,
    merge_incremental_report_to_global,
)

logger = logging.getLogger(__name__)


async def handle_incremental_merge_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理增量报表合并回调"""
    query = update.callback_query
    if not query:
        return

    data = query.data
    user_id = update.effective_user.id if update.effective_user else None

    # 检查权限（仅管理员）
    if not user_id or user_id not in ADMIN_IDS:
        await query.answer("❌ 仅管理员可以合并增量报表", show_alert=True)
        return

    # 解析回调数据：merge_incremental_YYYY-MM-DD 或 merge_incremental_confirm_YYYY-MM-DD
    if data.startswith("merge_incremental_confirm_"):
        # 确认合并
        merge_date = data.replace("merge_incremental_confirm_", "")
        await _confirm_merge(update, context, merge_date)
    elif data.startswith("merge_incremental_cancel_"):
        # 取消合并
        merge_date = data.replace("merge_incremental_cancel_", "")
        await query.answer("❌ 已取消合并")
        await query.edit_message_reply_markup(reply_markup=None)
    elif data.startswith("merge_incremental_"):
        # 首次点击合并按钮
        merge_date = data.replace("merge_incremental_", "")
        await _handle_merge_request(update, context, merge_date)
    else:
        await query.answer("❌ 未知操作", show_alert=True)


async def _handle_merge_request(
    update: Update, context: ContextTypes.DEFAULT_TYPE, merge_date: str
):
    """处理合并请求"""
    query = update.callback_query

    try:
        # 检查是否已经合并过
        merge_record = await db_operations.get_merge_record(merge_date)

        if merge_record:
            # 已经合并过，提示用户确认
            await query.answer()

            # 显示确认对话框
            confirm_text = (
                f"⚠️ 警告：{merge_date} 的增量报表已经合并过！\n\n"
                f"上次合并时间: {merge_record.get('merged_at', '未知')}\n"
                f"上次合并数据:\n"
                f"  - 订单数: {merge_record.get('orders_count', 0)}\n"
                f"  - 订单金额: {merge_record.get('total_amount', 0):,.2f}\n"
                f"  - 利息: {merge_record.get('total_interest', 0):,.2f}\n"
                f"  - 开销: {merge_record.get('total_expenses', 0):,.2f}\n\n"
                f"⚠️ 再次合并会导致数据重复累加！\n"
                f"确定要继续合并吗？"
            )

            keyboard = [
                [
                    InlineKeyboardButton(
                        "✅ 确认合并", callback_data=f"merge_incremental_confirm_{merge_date}"
                    ),
                    InlineKeyboardButton(
                        "❌ 取消", callback_data=f"merge_incremental_cancel_{merge_date}"
                    ),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            try:
                if query.message:
                    await query.message.reply_text(confirm_text, reply_markup=reply_markup)
                else:
                    await query.answer("需要确认合并操作", show_alert=True)
            except Exception as e:
                logger.error(f"发送确认消息失败: {e}", exc_info=True)
                await query.answer("需要确认合并操作", show_alert=True)
        else:
            # 未合并过，直接合并
            await _execute_merge(update, context, merge_date)
    except Exception as e:
        logger.error(f"处理合并请求失败: {e}", exc_info=True)
        await query.answer(f"❌ 处理失败: {str(e)}", show_alert=True)


async def _confirm_merge(update: Update, context: ContextTypes.DEFAULT_TYPE, merge_date: str):
    """确认合并"""
    query = update.callback_query
    await query.answer()
    await _execute_merge(update, context, merge_date)


async def _execute_merge(update: Update, context: ContextTypes.DEFAULT_TYPE, merge_date: str):
    """执行合并操作"""
    query = update.callback_query
    user_id = update.effective_user.id if update.effective_user else None

    try:
        # 显示处理中
        await query.message.reply_text("⏳ 正在合并增量报表到全局数据...")

        # 获取基准日期
        baseline_date = await get_or_create_baseline_date()

        # 获取上次合并日期（如果存在）
        last_merge_date = None
        merge_records = await db_operations.get_all_merge_records()
        if merge_records:
            # 获取最新的合并日期
            sorted_records = sorted(
                merge_records, key=lambda x: x.get("merged_at", ""), reverse=True
            )
            last_merge_date = sorted_records[0].get("merge_date")

        # 确定合并的起始日期（从上次合并日期+1天开始，或从基准日期开始）
        if last_merge_date:
            from datetime import datetime, timedelta

            last_date = datetime.strptime(last_merge_date, "%Y-%m-%d")
            start_date = (last_date + timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            start_date = baseline_date

        # 准备增量数据（从上次合并日期+1天到当前合并日期）
        incremental_data = await prepare_incremental_data(start_date, merge_date)
        orders_data = incremental_data.get("orders", [])
        expense_records = incremental_data.get("expenses", [])

        if not orders_data and not expense_records:
            try:
                if query.message:
                    await query.message.reply_text(f"✅ {merge_date} 无增量数据需要合并")
                else:
                    await query.answer(f"✅ {merge_date} 无增量数据", show_alert=True)
            except Exception as e:
                logger.error(f"发送无增量数据提示失败: {e}", exc_info=True)
                await query.answer(f"✅ {merge_date} 无增量数据", show_alert=True)
            return

        # 计算统计信息
        stats = await calculate_incremental_stats(orders_data, expense_records)

        # 合并到全局数据
        result = await merge_incremental_report_to_global(orders_data, expense_records)

        if result["success"]:
            # 保存合并记录
            total_expenses = stats["company_expenses"] + stats["other_expenses"]
            await db_operations.save_merge_record(
                merge_date=merge_date,
                baseline_date=baseline_date,
                orders_count=len(orders_data),
                total_amount=stats["new_orders_amount"],
                total_interest=stats["interest"],
                total_expenses=total_expenses,
                merged_by=user_id,
            )

            # 更新按钮状态
            keyboard = [
                [InlineKeyboardButton("✅ 已合并", callback_data=f"merge_incremental_{merge_date}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            try:
                await query.message.edit_reply_markup(reply_markup=reply_markup)
            except Exception:
                pass  # 如果消息已编辑过，忽略错误

            # 发送合并结果
            message = f"✅ 增量报表已合并到全局数据\n\n"
            message += f"合并日期: {merge_date}\n"
            message += f"合并范围: {start_date} 至 {merge_date}\n"
            message += f"基准日期: {baseline_date}\n\n"
            message += f"📦 订单统计:\n"
            message += f"  - 订单数: {stats['new_orders_count']}\n"
            message += f"  - 订单金额: {stats['new_orders_amount']:,.2f}\n"
            message += (
                f"  - 新客户: {stats['new_clients_count']}个, {stats['new_clients_amount']:,.2f}\n"
            )
            message += f"  - 老客户: {stats['old_clients_count']}个, {stats['old_clients_amount']:,.2f}\n\n"
            message += f"💰 收入统计:\n"
            message += f"  - 利息: {stats['interest']:,.2f}\n"
            message += f"  - 归还本金: {stats['principal_reduction']:,.2f}\n"
            message += f"  - 完成订单: {stats['completed_orders_count']}个, {stats['completed_amount']:,.2f}\n"
            message += f"  - 违约完成: {stats['breach_end_orders_count']}个, {stats['breach_end_amount']:,.2f}\n\n"
            message += f"💸 开销统计:\n"
            message += f"  - 公司开销: {stats['company_expenses']:,.2f}\n"
            message += f"  - 其他开销: {stats['other_expenses']:,.2f}\n"
            message += f"  - 总开销: {total_expenses:,.2f}\n"

            try:
                if query.message:
                    await query.message.reply_text(message)
                else:
                    await query.answer("✅ 合并成功", show_alert=True)
            except Exception as e:
                logger.error(f"发送合并成功消息失败: {e}", exc_info=True)
                await query.answer("✅ 合并成功", show_alert=True)
        else:
            try:
                if query.message:
                    await query.message.reply_text(
                        f"❌ 合并失败: {result.get('message', '未知错误')}"
                    )
                else:
                    await query.answer(
                        f"❌ 合并失败: {result.get('message', '未知错误')}", show_alert=True
                    )
            except Exception as e:
                logger.error(f"发送合并失败消息失败: {e}", exc_info=True)
                await query.answer("❌ 合并失败", show_alert=True)
    except Exception as e:
        logger.error(f"执行合并失败: {e}", exc_info=True)
        try:
            if query.message:
                await query.message.reply_text(f"❌ 合并失败: {str(e)}")
            else:
                await query.answer(f"❌ 合并失败: {str(e)}", show_alert=True)
        except Exception as e2:
            logger.error(f"发送合并失败消息失败: {e2}", exc_info=True)
            await query.answer("❌ 合并失败", show_alert=True)
