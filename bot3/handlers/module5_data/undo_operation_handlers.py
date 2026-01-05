"""撤销操作处理函数

包含各种撤销操作的具体实现。
"""

# 标准库
import logging
from typing import Dict, Optional, Tuple

# 本地模块
import db_operations
from utils.date_helpers import get_daily_period_date
from utils.stats_helpers import update_all_stats, update_liquid_capital

logger = logging.getLogger(__name__)


async def _undo_interest(operation_data: dict) -> bool:
    """撤销利息收入（标记为已撤销，不删除记录）"""
    try:
        amount = operation_data.get("amount", 0)
        group_id = operation_data.get("group_id")
        operation_data.get("date", get_daily_period_date())

        # 1. 减少利息收入
        await update_all_stats("interest", -amount, 0, group_id)

        # 2. 减少流动资金
        await update_liquid_capital(-amount)

        # 3. 标记收入记录为已撤销（不删除，保留历史记录）
        income_id = operation_data.get("income_record_id")
        if income_id:
            success = await db_operations.mark_income_undone(income_id)
            if not success:
                logger.warning(
                    f"标记收入记录 {income_id} 为已撤销失败，但统计数据已回滚"
                )
        else:
            logger.warning("撤销利息收入：缺少收入记录ID，无法标记记录为已撤销")

        return True
    except Exception as e:
        logger.error(f"撤销利息收入失败: {e}", exc_info=True)
        return False


async def _undo_principal_reduction(operation_data: dict) -> bool:
    """撤销本金减少（必须锁定到本群）"""
    try:
        amount = operation_data.get("amount", 0)
        group_id = operation_data.get("group_id")
        chat_id = operation_data.get("chat_id")
        old_amount = operation_data.get("old_amount")
        operation_data.get("order_id")

        if not chat_id or not old_amount:
            logger.error("撤销本金减少：缺少必要参数")
            return False

        # 验证订单确实属于指定的 chat_id（必须锁定到本群）
        order = await db_operations.get_order_by_chat_id(chat_id)
        if not order:
            logger.warning(f"撤销本金减少：订单不存在 (chat_id: {chat_id})")
            return False

        # 1. 恢复订单金额
        await db_operations.update_order_amount(chat_id, old_amount)

        # 2. 恢复有效金额
        await update_all_stats("valid", amount, 0, group_id)

        # 3. 减少完成金额
        await update_all_stats("completed", -amount, 0, group_id)

        # 4. 减少流动资金
        await update_liquid_capital(-amount)

        return True
    except Exception as e:
        logger.error(f"撤销本金减少失败: {e}")
        return False


async def _undo_expense(operation_data: dict) -> bool:
    """撤销开销记录"""
    try:
        amount = operation_data.get("amount", 0)
        expense_type = operation_data.get("type")
        expense_id = operation_data.get("expense_record_id")
        date = operation_data.get("date", get_daily_period_date())

        if not expense_id:
            logger.error("撤销开销：缺少开销记录ID")
            return False

        # 1. 恢复日结数据
        field = "company_expenses" if expense_type == "company" else "other_expenses"
        await db_operations.update_daily_data(date, field, -amount, None)

        # 2. 恢复流动资金
        await db_operations.update_financial_data("liquid_funds", amount)

        # 3. 恢复日结流量
        await db_operations.update_daily_data(date, "liquid_flow", amount, None)

        # 4. 删除开销记录
        await db_operations.delete_expense_record(expense_id)

        return True
    except Exception as e:
        logger.error(f"撤销开销失败: {e}")
        return False


async def _validate_completed_undo_params(
    operation_data: dict,
) -> Tuple[bool, Optional[Dict], Optional[str], Optional[str], Optional[float]]:
    """验证撤销订单完成的参数

    Args:
        operation_data: 操作数据

    Returns:
        (是否有效, 订单数据, 旧状态, 完成时的归属ID, 金额)
    """
    chat_id = operation_data.get("chat_id")
    operation_group_id = operation_data.get("group_id")
    amount = operation_data.get("amount", 0)
    old_state = operation_data.get("old_state")

    if not chat_id or not old_state:
        logger.error("撤销订单完成：缺少必要参数")
        return False, None, None, None, None

    order = await db_operations.get_order_by_chat_id_including_archived(chat_id)
    if not order:
        logger.warning(f"撤销订单完成：订单不存在 (chat_id: {chat_id})")
        return False, None, None, None, None

    return True, order, old_state, operation_group_id, amount


async def _rollback_completed_order_statistics(
    amount: float, operation_group_id: Optional[str], current_group_id: Optional[str]
) -> None:
    """回滚订单完成统计

    Args:
        amount: 金额
        operation_group_id: 完成时的归属ID
        current_group_id: 当前归属ID
    """
    if current_group_id != operation_group_id:
        logger.info(
            "撤销订单完成：归属ID已变更 "
            f"(完成时: {operation_group_id}, 当前: {current_group_id})"
        )
        await update_all_stats("completed", -amount, -1, operation_group_id)
        await update_all_stats("valid", amount, 1, current_group_id)
    else:
        await update_all_stats("valid", amount, 1, current_group_id)
        await update_all_stats("completed", -amount, -1, current_group_id)


async def _undo_order_completed(operation_data: dict) -> bool:
    """撤销订单完成（必须锁定到本群）"""
    try:
        (
            is_valid,
            order,
            old_state,
            operation_group_id,
            amount,
        ) = await _validate_completed_undo_params(operation_data)
        if not is_valid:
            return False

        chat_id = operation_data.get("chat_id")
        current_group_id = order.get("group_id")

        await db_operations.update_order_state(chat_id, old_state)
        await _rollback_completed_order_statistics(
            amount, operation_group_id, current_group_id
        )
        await update_liquid_capital(-amount)

        income_id = operation_data.get("income_record_id")
        if income_id:
            success = await db_operations.mark_income_undone(income_id)
            if not success:
                logger.warning(
                    f"标记收入记录 {income_id} 为已撤销失败，但统计数据已回滚"
                )
        else:
            logger.warning("撤销订单完成：缺少收入记录ID，无法标记记录为已撤销")

        return True
    except Exception as e:
        logger.error(f"撤销订单完成失败: {e}", exc_info=True)
        return False


async def _validate_breach_end_undo_params(
    operation_data: dict, chat_id: int, order_id: str
) -> Tuple[bool, Optional[Dict]]:
    """验证撤销违约完成的参数

    Args:
        operation_data: 操作数据
        chat_id: 聊天ID
        order_id: 订单ID

    Returns:
        (是否有效, 订单数据)
    """
    if not chat_id or not order_id:
        logger.error("撤销违约完成：缺少必要参数")
        return False, None

    order = await db_operations.get_order_by_chat_id_including_archived(chat_id)
    if not order:
        logger.warning(
            f"撤销违约完成：订单不存在 (chat_id: {chat_id}, order_id: {order_id})"
        )
        return False, None

    if order.get("order_id") != order_id:
        logger.error(
            f"撤销违约完成：订单ID不匹配 (期望: {order_id}, 实际: {order.get('order_id')})"
        )
        return False, None

    return True, order


async def _rollback_breach_end_statistics(
    amount: float, operation_group_id: str, current_group_id: str
) -> None:
    """回滚违约完成统计

    Args:
        amount: 金额
        operation_group_id: 完成时的归属ID
        current_group_id: 当前归属ID
    """
    if current_group_id != operation_group_id:
        logger.info(
            "撤销违约完成：归属ID已变更 "
            f"(完成时: {operation_group_id}, 当前: {current_group_id})"
        )
        await update_all_stats("breach_end", -amount, -1, operation_group_id)
        await update_all_stats("breach", amount, 1, current_group_id)
    else:
        await update_all_stats("breach", amount, 1, current_group_id)
        await update_all_stats("breach_end", -amount, -1, current_group_id)


async def _mark_income_record_undone(income_id: Optional[int]) -> None:
    """标记收入记录为已撤销

    Args:
        income_id: 收入记录ID
    """
    if income_id:
        success = await db_operations.mark_income_undone(income_id)
        if not success:
            logger.warning(f"标记收入记录 {income_id} 为已撤销失败，但统计数据已回滚")
    else:
        logger.warning("撤销违约完成：缺少收入记录ID，无法标记记录为已撤销")


async def _undo_order_breach_end(operation_data: dict) -> bool:
    """撤销违约完成（必须锁定到本群）"""
    try:
        amount = operation_data.get("amount", 0)
        operation_group_id = operation_data.get("group_id")
        chat_id = operation_data.get("chat_id")
        order_id = operation_data.get("order_id")

        is_valid, order = await _validate_breach_end_undo_params(
            operation_data, chat_id, order_id
        )
        if not is_valid:
            return False

        current_group_id = order.get("group_id")

        await db_operations.update_order_state(chat_id, "breach")
        await _rollback_breach_end_statistics(
            amount, operation_group_id, current_group_id
        )
        await update_liquid_capital(-amount)

        income_id = operation_data.get("income_record_id")
        await _mark_income_record_undone(income_id)

        return True
    except Exception as e:
        logger.error(f"撤销违约完成失败: {e}", exc_info=True)
        return False


async def _validate_order_created_undo_params(
    operation_data: dict,
) -> Tuple[bool, Optional[Dict]]:
    """验证撤销订单创建的参数

    Args:
        operation_data: 操作数据

    Returns:
        (是否有效, 订单数据)
    """
    order_id = operation_data.get("order_id")
    chat_id = operation_data.get("chat_id")

    if not chat_id or not order_id:
        logger.error("撤销订单创建：缺少必要参数")
        return False, None

    order = await db_operations.get_order_by_chat_id(chat_id)
    if not order:
        logger.warning(
            f"撤销订单创建：订单不存在或已被删除 (chat_id: {chat_id}, order_id: {order_id})"
        )
        return False, None

    if order.get("order_id") != order_id:
        logger.error(
            f"撤销订单创建：订单ID不匹配 (期望: {order_id}, 实际: {order.get('order_id')})"
        )
        return False, None

    return True, order


async def _rollback_order_created_statistics(
    initial_state: str, amount: float, group_id: str
) -> None:
    """回滚订单创建的统计

    Args:
        initial_state: 初始状态
        amount: 金额
        group_id: 归属ID
    """
    is_initial_breach = initial_state == "breach"
    if is_initial_breach:
        await update_all_stats("breach", -amount, -1, group_id)
    else:
        await update_all_stats("valid", -amount, -1, group_id)


async def _restore_non_historical_order_data(
    amount: float, customer: Optional[str], group_id: str
) -> None:
    """恢复非历史订单的数据

    Args:
        amount: 金额
        customer: 客户类型
        group_id: 归属ID
    """
    await update_liquid_capital(amount)

    if customer:
        client_field = "new_clients" if customer == "A" else "old_clients"
        await update_all_stats(client_field, -amount, -1, group_id)


async def _undo_order_created(operation_data: dict) -> bool:
    """撤销订单创建（必须锁定到本群）"""
    try:
        is_valid, order = await _validate_order_created_undo_params(operation_data)
        if not is_valid:
            return False

        chat_id = operation_data.get("chat_id")
        group_id = operation_data.get("group_id")
        amount = operation_data.get("amount", 0)
        initial_state = operation_data.get("initial_state", "normal")
        is_historical = operation_data.get("is_historical", False)
        customer = operation_data.get("customer")

        await db_operations.delete_order_by_chat_id(chat_id)
        await _rollback_order_created_statistics(initial_state, amount, group_id)

        if not is_historical:
            await _restore_non_historical_order_data(amount, customer, group_id)

        return True
    except Exception as e:
        logger.error(f"撤销订单创建失败: {e}")
        return False


async def _undo_order_state_change(operation_data: dict) -> bool:
    """撤销订单状态变更（必须锁定到本群）"""
    try:
        chat_id = operation_data.get("chat_id")
        old_state = operation_data.get("old_state")
        new_state = operation_data.get("new_state")
        group_id = operation_data.get("group_id")
        amount = operation_data.get("amount", 0)

        if not chat_id or not old_state:
            logger.error("撤销订单状态变更：缺少必要参数")
            return False

        # 验证订单确实属于指定的 chat_id（必须锁定到本群）
        order = await db_operations.get_order_by_chat_id(chat_id)
        if not order:
            logger.warning(f"撤销订单状态变更：订单不存在 (chat_id: {chat_id})")
            return False

        # 1. 恢复订单状态
        await db_operations.update_order_state(chat_id, old_state)

        # 2. 回滚统计变更
        # 从new_state回滚到old_state
        if old_state == "normal" and new_state == "breach":
            # 恢复：breach -> normal (有效)
            await update_all_stats("breach", -amount, -1, group_id)
            await update_all_stats("valid", amount, 1, group_id)
        elif old_state == "overdue" and new_state == "breach":
            # 恢复：breach -> overdue (有效)
            await update_all_stats("breach", -amount, -1, group_id)
            await update_all_stats("valid", amount, 1, group_id)

        return True
    except Exception as e:
        logger.error(f"撤销订单状态变更失败: {e}")
        return False
