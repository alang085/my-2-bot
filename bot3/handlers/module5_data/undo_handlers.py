"""撤销操作处理器（主路由）

包含撤销操作的主路由函数。
"""

# 标准库
import logging
from typing import Dict, Optional, Tuple

# 第三方库
from telegram import Update
from telegram.ext import ContextTypes

# 本地模块
from decorators import authorized_required, error_handler
from handlers.module5_data.undo_data import (ExecuteUndoParams,
                                             FailedUndoParams,
                                             SuccessfulUndoParams,
                                             UndoResultParams)
from handlers.module5_data.undo_handlers_execution import (
    handle_failed_undo, handle_successful_undo, handle_undo_exception)
from handlers.module5_data.undo_handlers_validation import (
    check_undo_count_limit, get_and_validate_last_operation,
    validate_user_and_context)
from handlers.module5_data.undo_helpers import execute_undo_by_type

logger = logging.getLogger(__name__)


def reset_undo_count(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """重置用户的连续撤销次数（在成功执行新操作后调用）"""
    if context and hasattr(context, "user_data") and context.user_data:
        if "undo_count" in context.user_data:
            context.user_data["undo_count"] = 0


async def _validate_undo_request(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> tuple[bool, Optional[int], Optional[bool], Optional[int], Optional[int]]:
    """验证撤销请求

    Args:
        update: Telegram更新对象
        context: 上下文对象

    Returns:
        (是否有效, 用户ID, 是否群组, 聊天ID, 撤销次数)
    """
    user_id, is_group, chat_id = await validate_user_and_context(update, context)
    if not user_id or not chat_id:
        return False, None, None, None, None

    exceeded, undo_count = await check_undo_count_limit(update, context, is_group)
    if exceeded:
        return False, None, None, None, None

    return True, user_id, is_group, chat_id, undo_count


async def _get_last_operation_for_undo(
    update: Update, user_id: int, chat_id: int, is_group: bool
) -> Optional[Dict]:
    """获取最后一个操作用于撤销

    Args:
        update: Telegram更新对象
        user_id: 用户ID
        chat_id: 聊天ID
        is_group: 是否群组

    Returns:
        最后一个操作，如果不存在则返回None
    """
    return await get_and_validate_last_operation(update, user_id, chat_id, is_group)


async def _handle_successful_undo_flow(params: SuccessfulUndoParams) -> None:
    """处理成功撤销流程

    Args:
        params: 成功撤销参数
    """
    await handle_successful_undo(params)


async def _handle_failed_undo_flow(params: "FailedUndoParams") -> None:
    """处理失败撤销流程

    Args:
        params: 失败撤销参数
    """
    from handlers.module5_data.undo_data import FailedUndoParams

    failed_params = FailedUndoParams(
        update=params.update,
        context=params.context,
        user_id=params.user_id,
        is_group=params.is_group,
        operation_id=params.operation_id,
        operation_type=params.operation_type,
        undo_count=params.undo_count,
        last_operation=params.last_operation,
    )
    await handle_failed_undo(failed_params)


async def _route_undo_result(params: UndoResultParams) -> None:
    """路由撤销结果到相应的处理流程

    Args:
        params: 撤销结果参数
    """
    if params.success:
        successful_params = SuccessfulUndoParams(
            update=params.update,
            context=params.context,
            user_id=params.user_id,
            is_group=params.is_group,
            operation_id=params.operation_id,
            operation_type=params.operation_type,
            operation_data=params.operation_data,
            undo_message=params.undo_message,
            undo_message_en=params.undo_message_en,
            undo_count=params.undo_count,
            last_operation=params.last_operation,
        )
        await _route_successful_undo(successful_params)
    else:
        failed_params = FailedUndoParams(
            update=params.update,
            context=params.context,
            user_id=params.user_id,
            is_group=params.is_group,
            operation_id=params.operation_id,
            operation_type=params.operation_type,
            undo_count=params.undo_count,
            last_operation=params.last_operation,
        )
        await _route_failed_undo(failed_params)


async def _route_successful_undo(params: SuccessfulUndoParams) -> None:
    """路由成功的撤销操作

    Args:
        params: 成功撤销参数
    """
    await _handle_successful_undo_flow(params)


async def _route_failed_undo(params: FailedUndoParams) -> None:
    """路由失败的撤销操作

    Args:
        params: 失败撤销参数
    """
    await _handle_failed_undo_flow(params)


async def _execute_undo_by_type_and_route(params: ExecuteUndoParams) -> None:
    """执行撤销操作并路由到相应的处理流程

    Args:
        params: 执行撤销操作参数
    """
    success, undo_message, undo_message_en = await execute_undo_by_type(
        params.operation_type, params.operation_data
    )

    undo_result_params = UndoResultParams(
        update=params.update,
        context=params.context,
        user_id=params.user_id,
        is_group=params.is_group,
        operation_id=params.operation_id,
        operation_type=params.operation_type,
        operation_data=params.operation_data,
        undo_message=undo_message,
        undo_message_en=undo_message_en,
        undo_count=params.undo_count,
        last_operation=params.last_operation,
        success=success,
    )
    await _route_undo_result(undo_result_params)


async def _execute_undo_operation(params: ExecuteUndoParams) -> None:
    """执行撤销操作

    Args:
        params: 执行撤销操作参数
    """
    await _execute_undo_by_type_and_route(params)


@error_handler
@authorized_required
async def undo_last_operation(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """撤销上一个操作"""
    is_valid, user_id, is_group, chat_id, undo_count = await _validate_undo_request(
        update, context
    )
    if not is_valid:
        return

    last_operation = await _get_last_operation_for_undo(
        update, user_id, chat_id, is_group
    )
    if not last_operation:
        return

    operation_type = last_operation["operation_type"]
    operation_data = last_operation["operation_data"]
    operation_id = last_operation["id"]

    try:
        execute_params = ExecuteUndoParams(
            update=update,
            context=context,
            user_id=user_id,
            is_group=is_group,
            chat_id=chat_id,
            operation_type=operation_type,
            operation_data=operation_data,
            operation_id=operation_id,
            undo_count=undo_count,
            last_operation=last_operation,
        )
        await _execute_undo_operation(execute_params)
    except Exception as e:
        await handle_undo_exception(update, context, user_id, is_group, chat_id, e)
