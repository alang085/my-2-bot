"""订单状态相关工具函数

包含订单状态转换的验证和处理功能。
"""

# 标准库
import logging
from typing import Any, Dict, Tuple

# 第三方库
from telegram import Update
from telegram.ext import ContextTypes

# 本地模块
import db_operations
from utils.chat_helpers import reply_in_group
from utils.date_helpers import get_daily_period_date
from utils.order_date import (_parse_current_order_date,
                              _update_order_date_and_weekday)
from utils.order_parsing import get_state_from_title, parse_order_from_title
from utils.stats_helpers import update_all_stats, update_liquid_capital

logger = logging.getLogger(__name__)


def _validate_state_transition(
    current_state: str, target_state: str, order_id: str
) -> bool:
    """验证状态转换是否合法

    Args:
        current_state: 当前状态
        target_state: 目标状态
        order_id: 订单ID（用于日志）

    Returns:
        是否允许转换
    """
    # 归档状态（end、breach_end）完全不可更改，但此函数只会在非归档状态时被调用
    # 这里额外检查以防万一
    if current_state in ["end", "breach_end"]:
        logger.info(
            f"订单 {order_id} 当前状态为 {current_state}（归档状态），禁止任何状态变更"
        )
        return False

    is_current_valid = current_state in ["normal", "overdue"]
    is_target_valid = target_state in ["normal", "overdue"]
    is_current_breach = current_state == "breach"
    is_target_end = target_state == "end"
    is_target_breach_end = target_state == "breach_end"

    # 禁止违约状态反向变更为正常/逾期
    if is_current_breach and is_target_valid:
        logger.info(f"订单 {order_id} 当前状态为违约，禁止反向变更为 {target_state}")
        return False

    # 检查完成状态的转换规则
    if is_target_end:
        # 只能从 normal 或 overdue 转换到 end
        if not is_current_valid:
            logger.info(
                f"订单 {order_id} 当前状态为 {current_state}，"
                f"不能直接变更为 end（只能从 normal/overdue 转换）"
            )
            return False

    if is_target_breach_end:
        # 禁止通过群名自动将 breach 变更为 breach_end（只能通过命令手动完成）
        logger.info(
            f"订单 {order_id} 禁止通过群名自动变更为 breach_end（只能通过命令手动完成）"
        )
        return False

    return True


async def _handle_valid_to_breach_transition(
    update: Update, target_state: str, group_id: str, amount: float
) -> bool:
    """处理 Valid -> Breach 状态转换

    Args:
        update: Telegram 更新对象
        target_state: 目标状态
        group_id: 归属ID
        amount: 订单金额

    Returns:
        是否成功处理
    """
    await update_all_stats("valid", -amount, -1, group_id)
    await update_all_stats("breach", amount, 1, group_id)
    await reply_in_group(
        update, f"🔄 State Changed: {target_state} (Auto)\nStats moved to Breach."
    )
    return True


async def _record_income_for_completion(
    update: Update, order: Dict[str, Any], group_id: str, amount: float
) -> bool:
    """记录订单完成的收入明细

    Args:
        update: Telegram 更新对象
        order: 订单字典
        group_id: 归属ID
        amount: 订单金额

    Returns:
        是否成功记录
    """
    user_id = update.effective_user.id if update.effective_user else 0
    date = get_daily_period_date()

    try:
        await db_operations.record_income(
            date=date,
            type="completed",
            amount=amount,
            group_id=group_id,
            order_id=order.get("order_id", "unknown"),
            order_date=order["date"],
            customer=order["customer"],
            weekday_group=order["weekday_group"],
            note="订单完成（自动）",
            created_by=user_id,
        )
        return True
    except Exception as e:
        logger.error(f"记录订单完成收入明细失败（自动完成）: {e}", exc_info=True)
        await reply_in_group(
            update,
            f"❌ Failed to record income details. "
            f"Order state updated but income not recorded. Error: {str(e)}",
        )
        return False


async def _update_stats_for_completion(
    update: Update, target_state: str, group_id: str, amount: float
) -> bool:
    """更新订单完成的统计数据

    Args:
        update: Telegram 更新对象
        target_state: 目标状态
        group_id: 归属ID
        amount: 订单金额

    Returns:
        是否成功更新
    """
    try:
        await update_all_stats("valid", -amount, -1, group_id)
        await update_all_stats("completed", amount, 1, group_id)
        await update_liquid_capital(amount)
        await reply_in_group(
            update,
            f"✅ Order Completed: {target_state} (Auto)\nStats moved to Completed.",
        )
        return True
    except Exception as e:
        logger.error(f"更新订单完成统计数据失败（自动完成）: {e}", exc_info=True)
        await reply_in_group(
            update,
            f"❌ Statistics update failed, but income record saved. "
            f"Use /fix_statistics to repair. Error: {str(e)}",
        )
        return False


async def _handle_valid_to_end_transition(
    update: Update,
    target_state: str,
    order: Dict[str, Any],
    group_id: str,
    amount: float,
) -> bool:
    """处理 Valid -> End 状态转换

    Args:
        update: Telegram 更新对象
        target_state: 目标状态
        order: 订单字典
        group_id: 归属ID
        amount: 订单金额

    Returns:
        是否成功处理
    """
    if not await _record_income_for_completion(update, order, group_id, amount):
        return False
    return await _update_stats_for_completion(update, target_state, group_id, amount)


async def _handle_state_transition_stats(
    update: Update,
    current_state: str,
    target_state: str,
    order: Dict[str, Any],
    group_id: str,
    amount: float,
) -> bool:
    """处理状态转换时的统计数据迁移

    Args:
        update: Telegram 更新对象
        current_state: 当前状态
        target_state: 目标状态
        order: 订单字典
        group_id: 归属ID
        amount: 订单金额

    Returns:
        是否成功处理
    """
    is_current_valid = current_state in ["normal", "overdue"]
    is_target_breach = target_state == "breach"
    is_target_end = target_state == "end"

    if is_current_valid and is_target_breach:
        return await _handle_valid_to_breach_transition(
            update, target_state, group_id, amount
        )
    if is_current_valid and is_target_end:
        return await _handle_valid_to_end_transition(
            update, target_state, order, group_id, amount
        )
    # Normal <-> Overdue (都在 Valid 池中，仅状态变更)
    await reply_in_group(update, f"🔄 State Changed: {target_state} (Auto)")
    return True


def _build_base_operation_data(
    chat_id: int,
    order_id: str,
    current_state: str,
    target_state: str,
    group_id: str,
    amount: float,
) -> Dict[str, Any]:
    """构建基础操作数据

    Args:
        chat_id: 聊天ID
        order_id: 订单ID
        current_state: 当前状态
        target_state: 目标状态
        group_id: 归属ID
        amount: 订单金额

    Returns:
        基础操作数据字典
    """
    return {
        "chat_id": chat_id,
        "order_id": order_id,
        "old_state": current_state,
        "new_state": target_state,
        "group_id": group_id,
        "amount": amount,
        "trigger": "auto_from_title",
    }


def _determine_operation_type_and_data(
    target_state: str, operation_data: Dict[str, Any], amount: float
) -> Tuple[str, Dict[str, Any]]:
    """确定操作类型和数据

    Args:
        target_state: 目标状态
        operation_data: 操作数据字典
        amount: 订单金额

    Returns:
        (操作类型, 操作数据)
    """
    if target_state == "end":
        operation_data["date"] = get_daily_period_date()
        return "order_completed", operation_data
    elif target_state == "breach_end":
        operation_data["date"] = get_daily_period_date()
        operation_data["amount"] = amount
        return "order_breach_end", operation_data
    else:
        return "order_state_change", operation_data


async def _record_state_change_operation(
    update: Update,
    chat_id: int,
    order_id: str,
    current_state: str,
    target_state: str,
    group_id: str,
    amount: float,
) -> None:
    """记录状态变更操作历史

    Args:
        update: Telegram 更新对象
        chat_id: 聊天ID
        order_id: 订单ID
        current_state: 当前状态
        target_state: 目标状态
        group_id: 归属ID
        amount: 订单金额
    """
    user_id = update.effective_user.id if update.effective_user else 0

    try:
        operation_data = _build_base_operation_data(
            chat_id, order_id, current_state, target_state, group_id, amount
        )
        operation_type, operation_data = _determine_operation_type_and_data(
            target_state, operation_data, amount
        )

        await db_operations.record_operation(
            user_id=user_id,
            operation_type=operation_type,
            operation_data=operation_data,
            chat_id=chat_id,
        )

        logger.info(
            f"已记录自动状态变更操作历史: order_id={order_id}, "
            f"{current_state} -> {target_state}, user_id={user_id}"
        )

    except Exception as e:
        logger.error(f"记录自动状态变更操作历史失败: {e}", exc_info=True)


async def update_order_state_from_title(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    order: Dict[str, Any],
    title: str,
) -> None:
    """根据群名变更自动更新订单状态和日期信息

    此函数会在群名变更时自动执行以下操作：
    1. 解析群名中的日期信息
    2. 如果日期与订单当前日期不一致，自动更新订单日期和星期分组
    3. 根据群名中的状态标记更新订单状态

    Args:
        update: Telegram 更新对象
        context: 上下文对象
        order: 订单字典，包含订单的所有信息
        title: 新的群名，用于解析订单信息和状态

    Note:
        - 已完成订单（end, breach_end）不会更新
        - 如果群名无法解析，只更新状态（如果状态标记存在）
        - 日期更新会同时更新 weekday_group 字段
    """
    from utils.order_state_date import update_order_date_if_needed
    from utils.order_state_transition import handle_state_transition
    from utils.order_state_validation import (should_skip_state_update,
                                              validate_order_for_state_update)

    # 验证订单是否可以更新
    is_valid, order_id = validate_order_for_state_update(order)
    if not is_valid or not order_id:
        return

    current_state = order.get("state")
    chat_id = order.get("chat_id")

    # 1. 更新订单日期和星期分组（如果需要）
    await update_order_date_if_needed(order, title, order_id)

    # 2. 处理状态变更
    target_state = get_state_from_title(title)
    if should_skip_state_update(current_state, target_state):
        return

    await handle_state_transition(
        update, context, order, current_state, title, order_id
    )
