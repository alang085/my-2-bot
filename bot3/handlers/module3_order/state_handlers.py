"""订单状态处理相关命令"""

import logging
from typing import Any

from telegram import Update
from telegram.ext import ContextTypes

from decorators import authorized_required, error_handler, group_chat_only
from services.module3_order.order_service import OrderService
from utils.chat_helpers import is_group_chat
from utils.handler_helpers import (get_and_validate_order, get_chat_info,
                                   get_user_id, send_success_message)

logger = logging.getLogger(__name__)


@error_handler
@authorized_required
@group_chat_only
async def set_normal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """转为正常状态"""
    chat_id, reply_func = get_chat_info(update)
    if not chat_id or not reply_func:
        return

    # 获取并验证订单（使用统一的辅助函数）
    order_model, state_model, _, error_msg = await get_and_validate_order(
        chat_id, allowed_states=("overdue",)
    )
    if error_msg:
        await reply_func(error_msg)
        return

    # 使用OrderService更改订单状态
    user_id = get_user_id(update)
    success, error_msg, operation_data = await OrderService.change_order_state(
        chat_id=chat_id,
        new_state="normal",
        allowed_old_states=("overdue",),
        user_id=user_id,
    )

    if not success:
        await reply_func(error_msg)
        return

    # 重置撤销计数
    if user_id and context:
        from handlers.module5_data.undo_handlers import reset_undo_count

        reset_undo_count(context, user_id)

    message = send_success_message(
        update,
        f"✅ Status Updated: normal\nOrder ID: {order_model.order_id}",
        f"✅ Status Updated: normal\nOrder ID: {order_model.order_id}\nState: normal",
    )
    await reply_func(message)


@error_handler
@authorized_required
@group_chat_only
async def set_overdue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """转为逾期状态"""
    chat_id, reply_func = get_chat_info(update)
    if not chat_id or not reply_func:
        return

    # 获取并验证订单（使用统一的辅助函数）
    order_model, state_model, _, error_msg = await get_and_validate_order(
        chat_id, allowed_states=("normal",)
    )
    if error_msg:
        await reply_func(error_msg)
        return

    # 使用OrderService更改订单状态
    user_id = get_user_id(update)
    success, error_msg, operation_data = await OrderService.change_order_state(
        chat_id=chat_id,
        new_state="overdue",
        allowed_old_states=("normal",),
        user_id=user_id,
    )

    if not success:
        await reply_func(error_msg)
        return

    # 重置撤销计数
    if user_id and context:
        from handlers.module5_data.undo_handlers import reset_undo_count

        reset_undo_count(context, user_id)

    message = send_success_message(
        update,
        f"✅ Status Updated: overdue\nOrder ID: {order_model.order_id}",
        f"✅ Status Updated: overdue\nOrder ID: {order_model.order_id}\nState: overdue",
    )
    await reply_func(message)


@error_handler
@authorized_required
@group_chat_only
async def set_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """标记订单为完成

    数据一致性保证：
    1. 先更新订单状态
    2. 记录收入明细（源数据）
    3. 更新统计数据（valid, completed, liquid_funds）
    4. 如果任何步骤失败，记录错误并提示用户修复
    """
    chat_id, reply_func = get_chat_info(update)
    if not chat_id or not reply_func:
        return

    # 使用OrderService完成订单
    user_id = get_user_id(update)
    success, error_msg, operation_data = await OrderService.complete_order(
        chat_id, user_id
    )

    if not success:
        await reply_func(error_msg)
        return

    # 重置撤销计数
    if user_id and context:
        from handlers.module5_data.undo_handlers import reset_undo_count

        reset_undo_count(context, user_id)

    # 获取订单信息用于显示
    import db_operations

    order = await db_operations.get_order_by_chat_id(chat_id)
    if not order:
        await reply_func("❌ Order not found after completion.")
        return

    amount = operation_data.get("amount", order.get("amount", 0.0))
    order_id = operation_data.get("order_id", order.get("order_id", ""))

    # 成功消息
    message = send_success_message(
        update,
        f"✅ Order Completed\nAmount: {amount:.2f}",
        f"✅ Order Completed!\nOrder ID: {order_id}\nAmount: {amount:.2f}",
    )
    await reply_func(message)


@error_handler
@authorized_required
@group_chat_only
async def set_breach(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """标记为违约

    数据一致性保证：
    1. 更新订单状态
    2. 更新统计数据（从 valid 转移到 breach）
    3. 如果任何步骤失败，记录错误并回滚
    """
    chat_id, reply_func = get_chat_info(update)
    if not chat_id or not reply_func:
        return

    # 使用OrderService更改订单状态
    user_id = get_user_id(update)
    success, error_msg, operation_data = await OrderService.change_order_state(
        chat_id=chat_id,
        new_state="breach",
        allowed_old_states=("normal", "overdue"),
        user_id=user_id,
    )

    if not success:
        await reply_func(error_msg)
        return

    # 重置撤销计数
    if user_id and context:
        from handlers.module5_data.undo_handlers import reset_undo_count

        reset_undo_count(context, user_id)

    # 获取订单信息用于显示
    import db_operations

    order = await db_operations.get_order_by_chat_id(chat_id)
    if not order:
        await reply_func("❌ Order not found after state change.")
        return

    amount = operation_data.get("amount", order.get("amount", 0.0))

    # 成功消息
    if is_group_chat(update):
        await reply_func(f"✅ Marked as Breach\nAmount: {amount:.2f}")
    else:
        await reply_func(
            f"✅ Order Marked as Breach!\n"
            f"Order ID: {order['order_id']}\n"
            f"Amount: {amount:.2f}"
        )


@error_handler
@authorized_required
@group_chat_only
async def _handle_breach_end_with_amount(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    reply_func,
    amount_str: str,
) -> bool:
    """处理提供了金额参数的违约订单完成，返回是否成功"""
    try:
        from utils.models import validate_amount

        amount_validated = validate_amount(float(amount_str))
    except ValueError as e:
        await reply_func(f"❌ {str(e)}")
        return False
    except Exception:
        await reply_func("❌ Invalid amount format.")
        return False

    user_id = get_user_id(update)
    success, error_msg, operation_data = await OrderService.complete_breach_order(
        chat_id, amount_validated, user_id
    )

    if not success:
        await reply_func(error_msg)
        return False

    if user_id and context:
        from handlers.module5_data.undo_handlers import reset_undo_count

        reset_undo_count(context, user_id)

    import db_operations

    order = await db_operations.get_order_by_chat_id(chat_id)
    if not order:
        await reply_func("❌ Order not found after completion.")
        return False

    order_id = operation_data.get("order_id", order.get("order_id", ""))
    message = send_success_message(
        update,
        f"✅ Breach Order Ended\nAmount: {amount_validated:.2f}",
        f"✅ Breach Order Ended\nAmount: {amount_validated:.2f}\nOrder ID: {order_id}",
    )
    await reply_func(message)
    return True


async def _request_breach_end_amount(
    update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, reply_func
) -> None:
    """请求用户输入违约订单完成金额"""
    if is_group_chat(update):
        if update.callback_query:
            prompt_msg = await context.bot.send_message(
                chat_id=chat_id,
                text="Please enter the final amount for this breach order (e.g., 5000).\n"
                "This amount will be recorded as liquid capital inflow.",
            )
        else:
            prompt_msg = await reply_func(
                "Please enter the final amount for this breach order (e.g., 5000).\n"
                "This amount will be recorded as liquid capital inflow."
            )
        if prompt_msg:
            context.user_data["breach_end_prompt_msg_id"] = prompt_msg.message_id
    else:
        await reply_func("Please enter the final amount for breach order:")

    context.user_data["state"] = "WAITING_BREACH_END_AMOUNT"
    context.user_data["breach_end_chat_id"] = chat_id


async def set_breach_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """违约订单完成 - 请求金额

    数据一致性保证：
    1. 更新订单状态
    2. 记录收入明细（源数据）
    3. 更新统计数据（breach_end, liquid_funds）
    4. 如果任何步骤失败，记录错误并回滚
    """
    chat_id, reply_func = get_chat_info(update)
    if not chat_id or not reply_func:
        return

    args = context.args if update.message else None
    order_model, state_model, _, error_msg = await get_and_validate_order(
        chat_id, allowed_states=("breach",)
    )
    if error_msg:
        await reply_func(error_msg)
        return

    if args and len(args) > 0:
        if await _handle_breach_end_with_amount(
            update, context, chat_id, reply_func, args[0]
        ):
            return

    await _request_breach_end_amount(update, context, chat_id, reply_func)
