"""撤销操作辅助函数

包含撤销操作相关的辅助函数。
"""

# 标准库
import logging
from typing import Dict, Tuple

# 第三方库
from telegram import Update
from telegram.ext import ContextTypes

# 本地模块
import db_operations
from handlers.module5_data.undo_operation_handlers import (
    _undo_expense, _undo_interest, _undo_order_breach_end,
    _undo_order_completed, _undo_order_created, _undo_order_state_change,
    _undo_principal_reduction)
from services.module5_data.undo_service import UndoService
from utils.chat_helpers import is_group_chat
from utils.error_messages import ErrorMessages

logger = logging.getLogger(__name__)


async def _execute_undo_interest(operation_data: Dict) -> Tuple[bool, str, str]:
    """执行利息收入撤销

    Returns:
        (是否成功, 中文消息, 英文消息)
    """
    success = await _undo_interest(operation_data)
    amount = operation_data.get("amount", 0)
    return (
        success,
        f"✅ 已撤销利息收入 {amount:.2f}",
        f"✅ Undone interest income {amount:.2f}",
    )


async def _execute_undo_expense(operation_data: Dict) -> Tuple[bool, str, str]:
    """执行开销撤销

    Returns:
        (是否成功, 中文消息, 英文消息)
    """
    success = await _undo_expense(operation_data)
    amount = operation_data.get("amount", 0)
    expense_type = operation_data.get("type")
    if expense_type == "company":
        return (
            success,
            f"✅ 已撤销公司开销 {amount:.2f}",
            f"✅ Undone company expense {amount:.2f}",
        )
    return (
        success,
        f"✅ 已撤销其他开销 {amount:.2f}",
        f"✅ Undone other expense {amount:.2f}",
    )


async def _execute_undo_order_operations(
    operation_type: str, operation_data: Dict
) -> Tuple[bool, str, str]:
    """执行订单相关操作的撤销

    Returns:
        (是否成功, 中文消息, 英文消息)
    """
    if operation_type == "order_completed":
        success = await _undo_order_completed(operation_data)
        return success, "✅ 已撤销订单完成操作", "✅ Undone order completion"

    elif operation_type == "order_breach_end":
        success = await _undo_order_breach_end(operation_data)
        return success, "✅ 已撤销违约完成操作", "✅ Undone breach order completion"

    elif operation_type == "order_created":
        success = await _undo_order_created(operation_data)
        order_id = operation_data.get("order_id", "N/A")
        return (
            success,
            f"✅ 已撤销订单创建：{order_id}",
            f"✅ Undone order creation: {order_id}",
        )

    elif operation_type == "order_state_change":
        success = await _undo_order_state_change(operation_data)
        old_state = operation_data.get("old_state", "N/A")
        new_state = operation_data.get("new_state", "N/A")
        return (
            success,
            f"✅ 已撤销订单状态变更：{new_state} → {old_state}",
            f"✅ Undone order state change: {new_state} → {old_state}",
        )

    return False, "", ""


async def _execute_undo_principal_reduction(
    operation_data: Dict,
) -> Tuple[bool, str, str]:
    """执行本金减少撤销

    Returns:
        (是否成功, 中文消息, 英文消息)
    """
    success = await _undo_principal_reduction(operation_data)
    amount = operation_data.get("amount", 0)
    return (
        success,
        f"✅ 已撤销本金减少 {amount:.2f}",
        f"✅ Undone principal reduction {amount:.2f}",
    )


def _build_unsupported_undo_message(operation_type: str) -> Tuple[bool, str, str]:
    """构建不支持的操作类型的撤销消息

    Args:
        operation_type: 操作类型

    Returns:
        (是否成功, 中文消息, 英文消息)
    """
    logger.warning(
        f"撤销不支持的操作类型: {operation_type}，仅标记为已撤销，不进行数据回滚"
    )
    undo_message = (
        f"✅ 已标记操作已撤销：{operation_type}（注意：此操作类型不支持数据回滚）"
    )
    undo_message_en = (
        f"✅ Operation marked as undone: {operation_type} "
        f"(Note: Data rollback not supported for this operation type)"
    )
    return True, undo_message, undo_message_en


async def execute_undo_by_type(
    operation_type: str, operation_data: Dict
) -> Tuple[bool, str, str]:
    """根据操作类型执行撤销

    Returns:
        Tuple[是否成功, 中文消息, 英文消息]
    """
    from handlers.module5_data.undo_strategy import \
        execute_undo_by_type_strategy

    return await execute_undo_by_type_strategy(operation_type, operation_data)


def prepare_chat_info(update: Update, is_group: bool, chat_id: int) -> str:
    """准备聊天环境信息"""
    chat_info = ""
    if is_group and update.effective_chat:
        group_name = update.effective_chat.title
        if group_name:
            chat_info = f"群名: {group_name}\n"
        else:
            chat_info = f"群聊 ID: {chat_id}\n"
    else:
        chat_info = f"私聊 (用户ID: {chat_id})\n"
    return chat_info


def prepare_user_info(update: Update, user_id: int) -> Tuple[str, str]:
    """准备用户信息

    Returns:
        Tuple[用户名, 用户全名]
    """
    if update.effective_user:
        user_name = update.effective_user.username or f"用户{user_id}"
        user_full_name = update.effective_user.full_name or user_name
    else:
        user_name = f"用户{user_id}" if user_id else "未知用户"
        user_full_name = user_name
    return user_name, user_full_name


async def verify_consistency(
    operation_type: str, operation_data: Dict
) -> Tuple[bool, list]:
    """验证数据一致性"""
    consistency_errors = []
    try:
        from utils.data_consistency_checker import \
            verify_complete_operation_consistency

        is_consistent, consistency_errors = await verify_complete_operation_consistency(
            operation_type, operation_data
        )
        if not is_consistent:
            logger.warning(
                f"撤销操作后数据一致性验证失败: {consistency_errors}",
                extra={
                    "operation_type": operation_type,
                    "operation_data": operation_data,
                },
            )
    except Exception as e:
        logger.error(f"数据一致性验证过程出错: {e}", exc_info=True)
        consistency_errors.append(f"验证过程出错: {str(e)}")
    return len(consistency_errors) == 0, consistency_errors


async def record_undo_operation_history(params: "UndoHistoryParams"):
    """记录撤销操作历史

    Args:
        params: 撤销操作历史参数
    """
    from handlers.module5_data.undo_history_data import UndoHistoryParams

    update = params.update
    user_id = params.user_id
    operation_id = params.operation_id
    operation_type = params.operation_type
    operation_data = params.operation_data
    undo_message = params.undo_message
    undo_message_en = params.undo_message_en
    is_group = params.is_group
    consistency_errors = params.consistency_errors
    current_chat_id = update.effective_chat.id if update.effective_chat else None
    if not current_chat_id or not user_id:
        return

    # 标记操作为已撤销
    success_mark, error_msg = await UndoService.mark_operation_as_undone(operation_id)
    if not success_mark:
        logger.warning(f"标记操作失败: {error_msg}")

    # 记录撤销操作历史
    success_record, error_msg = await UndoService.record_undo_operation(
        user_id=user_id,
        chat_id=current_chat_id,
        undone_operation_id=operation_id,
        undone_operation_type=operation_type,
    )
    if not success_record:
        logger.warning(f"记录撤销操作失败: {error_msg}")

    # 补充额外的操作数据
    try:
        await db_operations.record_operation(
            user_id=user_id,
            operation_type="operation_undo",
            operation_data={
                "undone_operation_id": operation_id,
                "undone_operation_type": operation_type,
                "undone_operation_data": operation_data,
                "undo_message": undo_message if not is_group else undo_message_en,
                "consistency_errors": (
                    consistency_errors if consistency_errors else None
                ),
            },
            chat_id=current_chat_id,
        )
    except Exception as e:
        logger.error(f"补充操作数据失败: {e}", exc_info=True)
