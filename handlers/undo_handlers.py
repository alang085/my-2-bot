"""撤销操作处理器"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
import db_operations
from utils.stats_helpers import update_all_stats, update_liquid_capital
from utils.date_helpers import get_daily_period_date
from utils.chat_helpers import is_group_chat
from decorators import error_handler, authorized_required
from config import ADMIN_IDS
import asyncio

logger = logging.getLogger(__name__)

# 最大连续撤销次数
MAX_UNDO_COUNT = 3


async def send_admin_notification(context: ContextTypes.DEFAULT_TYPE, message: str):
    """向所有管理员发送通知"""
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=message)
        except Exception as e:
            logger.error(f"向管理员 {admin_id} 发送通知失败: {e}")


@error_handler
@authorized_required
async def undo_last_operation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """撤销上一个操作"""
    user_id = update.effective_user.id if update.effective_user else None
    is_group = is_group_chat(update)
    
    if not user_id:
        if is_group:
            await update.message.reply_text("❌ Unable to get user information")
        else:
            await update.message.reply_text("❌ 无法获取用户信息")
        return

    # 检查连续撤销次数
    undo_count = context.user_data.get('undo_count', 0)
    if undo_count >= MAX_UNDO_COUNT:
        if is_group:
            await update.message.reply_text(
                f"❌ Maximum consecutive undo count reached ({MAX_UNDO_COUNT} times).\n"
                "Please enter correct data again before using undo."
            )
        else:
            await update.message.reply_text(
                f"❌ 已达到最大连续撤销次数（{MAX_UNDO_COUNT}次）。\n"
                "请重新输入正确数据后，再使用撤销功能。"
            )
        return

    # 获取当前聊天环境的 chat_id
    chat_id = update.effective_chat.id if update.effective_chat else None
    if not chat_id:
        if is_group:
            await update.message.reply_text("❌ Unable to get chat environment information")
        else:
            await update.message.reply_text("❌ 无法获取聊天环境信息")
        return
    
    # 获取当前聊天环境中的最后一个操作
    last_operation = await db_operations.get_last_operation(user_id, chat_id)
    if not last_operation:
        # 判断是私聊还是群聊
        is_private = chat_id > 0
        if is_group:
            await update.message.reply_text(
                f"❌ No undoable operation in this group chat.\n\n"
                f"Note: /undo command can only undo the last operation executed in the current chat environment."
            )
        else:
            chat_type = "私聊"
            await update.message.reply_text(
                f"❌ 在当前{chat_type}环境中没有可撤销的操作\n\n"
                f"提示：/undo 命令只能撤销在当前聊天环境（私聊或群聊）中执行的上一个操作。"
            )
        return

    operation_type = last_operation['operation_type']
    operation_data = last_operation['operation_data']
    operation_id = last_operation['id']

    # 获取群名（如果是群聊）
    group_name = None
    if is_group and update.effective_chat:
        group_name = update.effective_chat.title
    
    try:
        # 根据操作类型执行撤销
        success = False
        undo_message = ""
        undo_message_en = ""

        if operation_type == 'interest':
            # 撤销利息收入
            success = await _undo_interest(operation_data)
            amount = operation_data.get('amount', 0)
            undo_message = f"✅ 已撤销利息收入 {amount:.2f}"
            undo_message_en = f"✅ Undone interest income {amount:.2f}"

        elif operation_type == 'principal_reduction':
            # 撤销本金减少
            success = await _undo_principal_reduction(operation_data)
            amount = operation_data.get('amount', 0)
            undo_message = f"✅ 已撤销本金减少 {amount:.2f}"
            undo_message_en = f"✅ Undone principal reduction {amount:.2f}"

        elif operation_type == 'expense':
            # 撤销开销记录
            success = await _undo_expense(operation_data)
            amount = operation_data.get('amount', 0)
            expense_type = operation_data.get('type')
            if expense_type == 'company':
                undo_message = f"✅ 已撤销公司开销 {amount:.2f}"
                undo_message_en = f"✅ Undone company expense {amount:.2f}"
            else:
                undo_message = f"✅ 已撤销其他开销 {amount:.2f}"
                undo_message_en = f"✅ Undone other expense {amount:.2f}"

        elif operation_type == 'order_completed':
            # 撤销订单完成
            success = await _undo_order_completed(operation_data)
            undo_message = f"✅ 已撤销订单完成操作"
            undo_message_en = f"✅ Undone order completion"

        elif operation_type == 'order_breach_end':
            # 撤销违约完成
            success = await _undo_order_breach_end(operation_data)
            undo_message = f"✅ 已撤销违约完成操作"
            undo_message_en = f"✅ Undone breach order completion"

        elif operation_type == 'order_created':
            # 撤销订单创建
            success = await _undo_order_created(operation_data)
            order_id = operation_data.get('order_id', 'N/A')
            undo_message = f"✅ 已撤销订单创建：{order_id}"
            undo_message_en = f"✅ Undone order creation: {order_id}"

        elif operation_type == 'order_state_change':
            # 撤销订单状态变更
            success = await _undo_order_state_change(operation_data)
            old_state = operation_data.get('old_state', 'N/A')
            new_state = operation_data.get('new_state', 'N/A')
            undo_message = f"✅ 已撤销订单状态变更：{new_state} → {old_state}"
            undo_message_en = f"✅ Undone order state change: {new_state} → {old_state}"

        else:
            if is_group:
                await update.message.reply_text(f"❌ Unsupported operation type for undo: {operation_type}")
            else:
                await update.message.reply_text(f"❌ 不支持撤销此类型的操作: {operation_type}")
            return

        if success:
            # 标记操作为已撤销
            await db_operations.mark_operation_undone(operation_id)

            # 增加连续撤销次数
            context.user_data['undo_count'] = undo_count + 1

            # 发送成功消息（群聊使用英语，私聊使用中文）
            if is_group:
                await update.message.reply_text(undo_message_en)
            else:
                await update.message.reply_text(undo_message)

            # 获取用户信息用于通知
            user_name = update.effective_user.username or f"用户{user_id}"
            user_full_name = update.effective_user.full_name or user_name

            # 向管理员发送通知（包含群名）
            chat_info = ""
            if is_group and group_name:
                chat_info = f"群名: {group_name}\n"
            elif is_group:
                chat_info = f"群聊 ID: {chat_id}\n"
            else:
                chat_info = f"私聊 (用户ID: {user_id})\n"
            
            admin_message = (
                f"⚠️ 撤销操作通知\n\n"
                f"用户: {user_full_name} (@{user_name if update.effective_user.username else 'N/A'})\n"
                f"用户ID: {user_id}\n"
                f"{chat_info}"
                f"操作类型: {operation_type}\n"
                f"撤销详情: {undo_message if not is_group else undo_message_en}\n"
                f"连续撤销次数: {undo_count + 1}/{MAX_UNDO_COUNT}\n"
                f"操作时间: {last_operation.get('created_at', 'N/A')}"
            )
            await send_admin_notification(context, admin_message)
        else:
            if is_group:
                await update.message.reply_text("❌ Undo operation failed. Please check data status.")
            else:
                await update.message.reply_text("❌ 撤销操作失败，请检查数据状态")

    except Exception as e:
        logger.error(f"撤销操作时出错: {e}", exc_info=True)
        if is_group:
            await update.message.reply_text(f"❌ Error during undo operation: {str(e)}")
        else:
            await update.message.reply_text(f"❌ 撤销操作时出错: {str(e)}")


async def _undo_interest(operation_data: dict) -> bool:
    """撤销利息收入"""
    try:
        amount = operation_data.get('amount', 0)
        group_id = operation_data.get('group_id')
        date = operation_data.get('date', get_daily_period_date())

        # 1. 减少利息收入
        await update_all_stats('interest', -amount, 0, group_id)

        # 2. 减少流动资金
        await update_liquid_capital(-amount)

        # 3. 删除收入记录（如果有）
        income_id = operation_data.get('income_record_id')
        if income_id:
            # 注意：这里需要添加删除收入记录的函数，暂时跳过
            pass

        return True
    except Exception as e:
        logger.error(f"撤销利息收入失败: {e}")
        return False


async def _undo_principal_reduction(operation_data: dict) -> bool:
    """撤销本金减少"""
    try:
        amount = operation_data.get('amount', 0)
        group_id = operation_data.get('group_id')
        chat_id = operation_data.get('chat_id')
        old_amount = operation_data.get('old_amount')
        order_id = operation_data.get('order_id')

        if not chat_id or not old_amount:
            logger.error("撤销本金减少：缺少必要参数")
            return False

        # 1. 恢复订单金额
        await db_operations.update_order_amount(chat_id, old_amount)

        # 2. 恢复有效金额
        await update_all_stats('valid', amount, 0, group_id)

        # 3. 减少完成金额
        await update_all_stats('completed', -amount, 0, group_id)

        # 4. 减少流动资金
        await update_liquid_capital(-amount)

        return True
    except Exception as e:
        logger.error(f"撤销本金减少失败: {e}")
        return False


async def _undo_expense(operation_data: dict) -> bool:
    """撤销开销记录"""
    try:
        amount = operation_data.get('amount', 0)
        expense_type = operation_data.get('type')
        expense_id = operation_data.get('expense_record_id')
        date = operation_data.get('date', get_daily_period_date())

        if not expense_id:
            logger.error("撤销开销：缺少开销记录ID")
            return False

        # 1. 恢复日结数据
        field = 'company_expenses' if expense_type == 'company' else 'other_expenses'
        await db_operations.update_daily_data(date, field, -amount, None)

        # 2. 恢复流动资金
        await db_operations.update_financial_data('liquid_funds', amount)

        # 3. 恢复日结流量
        await db_operations.update_daily_data(date, 'liquid_flow', amount, None)

        # 4. 删除开销记录
        await db_operations.delete_expense_record(expense_id)

        return True
    except Exception as e:
        logger.error(f"撤销开销失败: {e}")
        return False


async def _undo_order_completed(operation_data: dict) -> bool:
    """撤销订单完成"""
    try:
        chat_id = operation_data.get('chat_id')
        group_id = operation_data.get('group_id')
        amount = operation_data.get('amount', 0)
        old_state = operation_data.get('old_state')  # 完成前的状态

        if not chat_id or not old_state:
            logger.error("撤销订单完成：缺少必要参数")
            return False

        # 1. 恢复订单状态
        await db_operations.update_order_state(chat_id, old_state)

        # 2. 回滚统计：减少完成，恢复有效
        await update_all_stats('valid', amount, 1, group_id)
        await update_all_stats('completed', -amount, -1, group_id)

        # 3. 减少流动资金
        await update_liquid_capital(-amount)

        return True
    except Exception as e:
        logger.error(f"撤销订单完成失败: {e}")
        return False


async def _undo_order_breach_end(operation_data: dict) -> bool:
    """撤销违约完成"""
    try:
        amount = operation_data.get('amount', 0)
        group_id = operation_data.get('group_id')
        chat_id = operation_data.get('chat_id')
        order_id = operation_data.get('order_id')
        date_str = operation_data.get('date', get_daily_period_date())

        if not chat_id or not order_id:
            logger.error("撤销违约完成：缺少必要参数")
            return False

        # 1. 恢复订单状态为breach
        await db_operations.update_order_state(chat_id, 'breach')

        # 2. 减少违约完成统计
        await update_all_stats('breach_end', -amount, -1, group_id)

        # 3. 减少流动资金
        await update_liquid_capital(-amount)

        return True
    except Exception as e:
        logger.error(f"撤销违约完成失败: {e}")
        return False


async def _undo_order_created(operation_data: dict) -> bool:
    """撤销订单创建"""
    try:
        order_id = operation_data.get('order_id')
        chat_id = operation_data.get('chat_id')
        group_id = operation_data.get('group_id')
        amount = operation_data.get('amount', 0)
        initial_state = operation_data.get('initial_state', 'normal')
        is_historical = operation_data.get('is_historical', False)
        customer = operation_data.get('customer')

        if not chat_id or not order_id:
            logger.error("撤销订单创建：缺少必要参数")
            return False

        # 1. 删除订单
        await db_operations.delete_order_by_chat_id(chat_id)

        # 2. 回滚统计
        is_initial_breach = (initial_state == 'breach')
        if is_initial_breach:
            await update_all_stats('breach', -amount, -1, group_id)
        else:
            await update_all_stats('valid', -amount, -1, group_id)

        # 3. 非历史订单需要恢复流动资金和客户统计
        if not is_historical:
            # 恢复流动资金
            await update_liquid_capital(amount)
            
            # 恢复客户统计
            client_field = 'new_clients' if customer == 'A' else 'old_clients'
            await update_all_stats(client_field, -amount, -1, group_id)

        return True
    except Exception as e:
        logger.error(f"撤销订单创建失败: {e}")
        return False


async def _undo_order_state_change(operation_data: dict) -> bool:
    """撤销订单状态变更"""
    try:
        chat_id = operation_data.get('chat_id')
        old_state = operation_data.get('old_state')
        new_state = operation_data.get('new_state')
        group_id = operation_data.get('group_id')
        amount = operation_data.get('amount', 0)

        if not chat_id or not old_state:
            logger.error("撤销订单状态变更：缺少必要参数")
            return False

        # 1. 恢复订单状态
        await db_operations.update_order_state(chat_id, old_state)

        # 2. 回滚统计变更
        # 从new_state回滚到old_state
        if old_state == 'normal' and new_state == 'overdue':
            # 无统计变更，仅状态变化
            pass
        elif old_state == 'normal' and new_state == 'breach':
            # 恢复：breach -> normal (有效)
            await update_all_stats('breach', -amount, -1, group_id)
            await update_all_stats('valid', amount, 1, group_id)
        elif old_state == 'overdue' and new_state == 'breach':
            # 恢复：breach -> overdue (有效)
            await update_all_stats('breach', -amount, -1, group_id)
            await update_all_stats('valid', amount, 1, group_id)
        elif old_state == 'overdue' and new_state == 'normal':
            # 无统计变更，仅状态变化
            pass

        return True
    except Exception as e:
        logger.error(f"撤销订单状态变更失败: {e}")
        return False


def reset_undo_count(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """重置用户的连续撤销次数（在成功执行新操作后调用）"""
    if context and hasattr(context, 'user_data') and context.user_data:
        if 'undo_count' in context.user_data:
            context.user_data['undo_count'] = 0

