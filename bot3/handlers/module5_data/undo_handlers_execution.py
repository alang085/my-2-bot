"""撤销操作处理器 - 执行模块

包含撤销操作的执行逻辑。
"""

import logging
from typing import List, Tuple

from telegram import Update
from telegram.ext import ContextTypes

from handlers.module5_data.undo_data import (CompleteUndoSuccessParams,
                                             FailedUndoParams)
from handlers.module5_data.undo_handlers_notification import (
    build_exception_admin_message, build_failure_admin_message,
    build_success_admin_message, get_username, send_admin_notification)
from handlers.module5_data.undo_helpers import (execute_undo_by_type,
                                                prepare_chat_info,
                                                prepare_user_info,
                                                record_undo_operation_history,
                                                verify_consistency)
from handlers.module5_data.undo_history_data import UndoHistoryParams
from handlers.module5_data.undo_notification_data import (
    AdminNotificationParams, ExceptionAdminNotificationParams,
    FailureAdminNotificationParams)
from handlers.module5_data.undo_verification_data import UndoVerificationParams
from utils.error_messages import ErrorMessages

logger = logging.getLogger(__name__)


async def _verify_undo_consistency(
    operation_type: str, operation_data: dict
) -> List[str]:
    """验证撤销操作的数据一致性

    Returns:
        一致性错误列表
    """
    _, consistency_errors = await verify_consistency(operation_type, operation_data)
    return consistency_errors


async def _record_undo_history(params: "UndoHistoryParams") -> None:
    """记录撤销操作历史

    Args:
        params: 撤销历史参数
    """
    from handlers.module5_data.undo_history_data import UndoHistoryParams

    await record_undo_operation_history(params)


async def _send_undo_success_message(
    update: Update, is_group: bool, undo_message: str, undo_message_en: str
) -> None:
    """发送撤销成功消息"""
    if is_group:
        await update.message.reply_text(undo_message_en)
    else:
        await update.message.reply_text(undo_message)


async def _send_undo_admin_notification(
    params: "SendUndoAdminNotificationParams",
) -> None:
    """向管理员发送撤销成功通知

    Args:
        params: 发送撤销管理员通知参数
    """
    from handlers.module5_data.undo_notification_data import (
        AdminNotificationParams, SendUndoAdminNotificationParams)

    consistency_status = "✅ 数据一致性验证通过"
    if params.consistency_errors:
        consistency_status = f"⚠️ 数据一致性验证发现问题:\n" + "\n".join(
            f"  - {error}" for error in params.consistency_errors
        )

    user_name, user_full_name = prepare_user_info(params.update, params.user_id)
    chat_id = params.update.effective_chat.id if params.update.effective_chat else None
    chat_info = prepare_chat_info(params.update, params.is_group, chat_id)
    username = get_username(params.update)

    notification_params = AdminNotificationParams(
        user_full_name=user_full_name,
        username=username,
        user_id=params.user_id,
        chat_info=chat_info,
        operation_type=params.operation_type,
        undo_message=params.undo_message,
        undo_message_en=params.undo_message_en,
        is_group=params.is_group,
        undo_count=params.undo_count,
        created_at=params.last_operation.get("created_at", "N/A"),
        consistency_status=consistency_status,
    )
    admin_message = build_success_admin_message(notification_params)
    await send_admin_notification(params.context, admin_message)


async def _process_undo_verification_and_history(
    params: UndoVerificationParams,
) -> List[str]:
    """处理撤销验证和记录历史

    Args:
        params: 撤销验证参数

    Returns:
        一致性错误列表
    """
    consistency_errors = await _verify_undo_consistency(
        params.operation_type, params.operation_data
    )
    history_params = UndoHistoryParams(
        update=params.update,
        user_id=params.user_id,
        operation_id=params.operation_id,
        operation_type=params.operation_type,
        operation_data=params.operation_data,
        undo_message=params.undo_message,
        undo_message_en=params.undo_message_en,
        is_group=params.is_group,
        consistency_errors=consistency_errors,
    )
    await _record_undo_history(history_params)
    return consistency_errors


async def _complete_undo_success_flow(params: CompleteUndoSuccessParams) -> None:
    """完成撤销成功流程

    Args:
        params: 完成撤销成功流程参数
    """
    params.context.user_data["undo_count"] = params.undo_count + 1
    await _send_undo_success_message(
        params.update, params.is_group, params.undo_message, params.undo_message_en
    )
    from handlers.module5_data.undo_notification_data import \
        SendUndoAdminNotificationParams

    notification_params = SendUndoAdminNotificationParams(
        update=params.update,
        context=params.context,
        user_id=params.user_id,
        is_group=params.is_group,
        operation_type=params.operation_type,
        undo_message=params.undo_message,
        undo_message_en=params.undo_message_en,
        undo_count=params.undo_count,
        last_operation=params.last_operation,
        consistency_errors=params.consistency_errors,
    )
    await _send_undo_admin_notification(notification_params)


async def handle_successful_undo(params: "SuccessfulUndoParams") -> None:
    """处理成功撤销

    Args:
        params: 成功撤销参数
    """
    from handlers.module5_data.undo_data import SuccessfulUndoParams

    verification_params = UndoVerificationParams(
        update=params.update,
        user_id=params.user_id,
        operation_id=params.operation_id,
        operation_type=params.operation_type,
        operation_data=params.operation_data,
        undo_message=params.undo_message,
        undo_message_en=params.undo_message_en,
        is_group=params.is_group,
    )
    consistency_errors = await _process_undo_verification_and_history(
        verification_params
    )
    complete_params = CompleteUndoSuccessParams(
        update=params.update,
        context=params.context,
        user_id=params.user_id,
        is_group=params.is_group,
        operation_type=params.operation_type,
        undo_message=params.undo_message,
        undo_message_en=params.undo_message_en,
        undo_count=params.undo_count,
        last_operation=params.last_operation,
        consistency_errors=consistency_errors,
    )
    await _complete_undo_success_flow(complete_params)


async def handle_failed_undo(failed_params: FailedUndoParams) -> None:
    """处理失败撤销

    Args:
        failed_params: 失败撤销参数
    """
    # 撤销失败，向用户发送错误消息
    if failed_params.is_group:
        await failed_params.update.message.reply_text(
            "❌ Undo operation failed. Please check data status."
        )
    else:
        await failed_params.update.message.reply_text(
            ErrorMessages.operation_failed("撤销操作", "请检查数据状态")
        )

    # 向管理员发送失败通知（包含详细错误信息）
    user_name, user_full_name = prepare_user_info(
        failed_params.update, failed_params.user_id
    )
    chat_id = (
        failed_params.update.effective_chat.id
        if failed_params.update.effective_chat
        else None
    )
    chat_info = prepare_chat_info(failed_params.update, failed_params.is_group, chat_id)
    username = get_username(failed_params.update)

    notification_params = FailureAdminNotificationParams(
        user_full_name=user_full_name,
        username=username,
        user_id=failed_params.user_id,
        chat_info=chat_info,
        operation_type=failed_params.operation_type,
        operation_id=failed_params.operation_id,
        created_at=failed_params.last_operation.get("created_at", "N/A"),
        undo_count=failed_params.undo_count,
    )
    admin_message = build_failure_admin_message(notification_params)
    await send_admin_notification(failed_params.context, admin_message)


async def handle_undo_exception(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    is_group: bool,
    chat_id: int,
    error: Exception,
) -> None:
    """处理撤销异常

    Args:
        update: Telegram更新对象
        context: 上下文对象
        user_id: 用户ID
        is_group: 是否为群聊
        chat_id: 聊天ID
        error: 异常对象
    """
    logger.error(f"撤销操作时出错: {error}", exc_info=True)

    # 向用户发送错误消息
    if is_group:
        await update.message.reply_text(
            ErrorMessages.operation_failed("撤销操作", str(error))
        )
    else:
        await update.message.reply_text(f"❌ 撤销操作时出错: {str(error)}")

    # 向管理员发送异常通知（包含详细错误信息）
    user_name, user_full_name = prepare_user_info(update, user_id)
    user_id_str = str(user_id) if user_id else "未知"
    chat_info = prepare_chat_info(update, is_group, chat_id)
    username = get_username(update)

    params = ExceptionAdminNotificationParams(
        user_full_name=user_full_name,
        username=username,
        user_id_str=user_id_str,
        chat_info=chat_info,
        error=error,
    )
    admin_message = build_exception_admin_message(params)
    await send_admin_notification(context, admin_message)
