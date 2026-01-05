"""订单服务 - 封装订单相关的业务逻辑"""

import logging
from typing import Any, Dict, Optional, Tuple

import db_operations
from utils.date_helpers import get_daily_period_date
from utils.error_handlers import ErrorHandler, retry
from utils.models import validate_amount, validate_order, validate_order_state
from utils.performance_monitor import monitor_performance
from utils.stats_helpers import update_all_stats, update_liquid_capital

logger = logging.getLogger(__name__)


class OrderService:
    """订单业务服务"""

    @staticmethod
    @monitor_performance("change_order_state")
    @retry(max_retries=2, initial_delay=0.5)
    @staticmethod
    async def _validate_and_update_state(
        chat_id: int, new_state: str, allowed_old_states: Tuple[str, ...]
    ) -> Tuple[
        bool,
        Optional[str],
        Optional[Any],
        Optional[str],
        Optional[str],
        Optional[float],
    ]:
        """验证订单并更新状态

        Args:
            chat_id: 群组ID
            new_state: 新状态
            allowed_old_states: 允许的旧状态列表

        Returns:
            (success, error_msg, order_model, old_state, group_id, amount)
        """
        from services.module3_order.state_update import update_order_state_safe
        from services.module3_order.state_validate import \
            validate_order_state_change

        is_valid, error_msg, order_model, old_state, amount = (
            await validate_order_state_change(chat_id, allowed_old_states)
        )
        if not is_valid:
            return False, error_msg, None, None, None, None

        success, error_msg = await update_order_state_safe(chat_id, new_state)
        if not success:
            return False, error_msg, None, None, None, None

        return True, None, order_model, old_state, order_model.group_id, amount

    @staticmethod
    async def _update_statistics_and_record(
        chat_id: int,
        order_model: Any,
        old_state: str,
        new_state: str,
        amount: float,
        group_id: str,
        user_id: Optional[int],
    ) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """更新统计数据并记录操作历史

        Args:
            chat_id: 群组ID
            order_model: 订单模型
            old_state: 旧状态
            new_state: 新状态
            amount: 订单金额
            group_id: 归属ID
            user_id: 用户ID

        Returns:
            (success, error_msg, operation_data)
        """
        from services.module3_order.state_record import \
            record_order_state_change_operation
        from services.module3_order.state_statistics import \
            update_statistics_for_state_change
        from services.module3_order.state_update import \
            rollback_order_state_safe

        success, error_msg = await update_statistics_for_state_change(
            new_state, amount, group_id
        )
        if not success:
            await rollback_order_state_safe(chat_id, old_state)
            return (
                False,
                f"❌ Statistics update failed. Order state rolled back. Error: {error_msg}",
                None,
            )

        operation_data = {
            "chat_id": chat_id,
            "order_id": order_model.order_id,
            "old_state": old_state,
            "new_state": new_state,
            "group_id": group_id,
            "amount": amount,
        }
        await record_order_state_change_operation(user_id, operation_data, chat_id)

        return True, None, operation_data

    async def change_order_state(
        chat_id: int,
        new_state: str,
        allowed_old_states: Tuple[str, ...],
        user_id: Optional[int] = None,
    ) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """更改订单状态（基础方法）

        Args:
            chat_id: 群组ID
            new_state: 新状态
            allowed_old_states: 允许的旧状态列表
            user_id: 用户ID（用于记录操作历史）

        Returns:
            (success, error_message, operation_data)
            - success: 是否成功
            - error_message: 错误消息（如果失败）
            - operation_data: 操作数据（用于记录历史）
        """
        success, error_msg, order_model, old_state, group_id, amount = (
            await OrderService._validate_and_update_state(
                chat_id, new_state, allowed_old_states
            )
        )
        if not success:
            return False, error_msg, None

        return await OrderService._update_statistics_and_record(
            chat_id, order_model, old_state, new_state, amount, group_id, user_id
        )

    @staticmethod
    async def _validate_order_for_completion(
        chat_id: int,
    ) -> Tuple[
        bool,
        Optional[str],
        Optional[Any],
        Optional[str],
        Optional[str],
        Optional[float],
    ]:
        """验证订单是否可以完成

        Returns:
            (success, error_msg, order_model, old_state, group_id, amount)
        """
        from services.module3_order.complete_validate import \
            validate_order_for_completion

        return await validate_order_for_completion(chat_id)

    @staticmethod
    async def _execute_order_completion(
        chat_id: int,
        order_model: Any,
        amount: float,
        group_id: str,
        user_id: Optional[int],
    ) -> Tuple[bool, Optional[str], Optional[int]]:
        """执行订单完成操作

        Returns:
            (success, error_msg, income_record_id)
        """
        from services.module3_order.complete_record import \
            record_income_for_completion
        from services.module3_order.complete_update import (
            update_order_state_for_completion,
            update_statistics_for_completion)

        success, error_msg = await update_order_state_for_completion(chat_id)
        if not success:
            return False, error_msg, None

        success, error_msg, income_record_id, _ = await record_income_for_completion(
            order_model, amount, group_id, user_id
        )
        if not success:
            return False, error_msg, None

        success, error_msg = await update_statistics_for_completion(amount, group_id)
        return True, error_msg, income_record_id

    @staticmethod
    async def _record_completion_history(params: "CompletionHistoryParams") -> None:
        """记录订单完成操作历史

        Args:
            params: 订单完成历史参数
        """
        from services.module3_order.complete_record import \
            record_operation_history

        await record_operation_history(params)

    @staticmethod
    def _build_completion_operation_data(
        chat_id: int,
        order_model: Any,
        group_id: str,
        amount: float,
        old_state: str,
        date_str: str,
        income_record_id: Optional[int],
    ) -> Dict:
        """构建订单完成操作数据

        Returns:
            操作数据字典
        """
        return {
            "chat_id": chat_id,
            "order_id": order_model.order_id,
            "group_id": group_id,
            "amount": amount,
            "old_state": old_state,
            "date": date_str,
            "income_record_id": income_record_id,
        }

    @staticmethod
    async def complete_order(
        chat_id: int, user_id: Optional[int] = None
    ) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """完成订单（end状态）

        数据一致性保证：
        1. 更新订单状态
        2. 记录收入明细（源数据）
        3. 更新统计数据（valid, completed, liquid_funds）
        4. 如果任何步骤失败，记录错误并回滚

        Returns:
            (success, error_message, operation_data)
        """
        from utils.date_helpers import get_daily_period_date

        success, error_msg, order_model, old_state, group_id, amount = (
            await OrderService._validate_order_for_completion(chat_id)
        )
        if not success:
            return False, error_msg, None

        date_str = get_daily_period_date()

        success, error_msg, income_record_id = (
            await OrderService._execute_order_completion(
                chat_id, order_model, amount, group_id, user_id
            )
        )
        if not success:
            return False, error_msg, None

        from services.module3_order.order_completion_data import \
            CompletionHistoryParams

        completion_params = CompletionHistoryParams(
            user_id=user_id,
            chat_id=chat_id,
            order_model=order_model,
            group_id=group_id,
            amount=amount,
            old_state=old_state,
            date_str=date_str,
            income_record_id=income_record_id,
        )
        await OrderService._record_completion_history(completion_params)

        operation_data = OrderService._build_completion_operation_data(
            chat_id,
            order_model,
            group_id,
            amount,
            old_state,
            date_str,
            income_record_id,
        )

        return True, error_msg, operation_data

    @staticmethod
    async def _validate_breach_order(
        chat_id: int, amount: float
    ) -> Tuple[bool, Optional[str], Optional[Any], Optional[float]]:
        """验证违约订单完成请求

        Returns:
            (is_valid, error_msg, order_model, amount_validated)
        """
        from services.module3_order.breach_validate import \
            validate_breach_order_completion

        is_valid, error_msg, order_model, amount_validated = (
            await validate_breach_order_completion(chat_id, amount)
        )
        return is_valid, error_msg, order_model, amount_validated

    @staticmethod
    async def _execute_breach_order_completion(
        chat_id: int,
        order_model: Any,
        amount_validated: float,
        group_id: str,
        user_id: Optional[int],
    ) -> Tuple[Optional[int], Optional[str]]:
        """执行违约订单完成操作

        Returns:
            (income_record_id, error_msg)
        """
        from services.module3_order.breach_update import (
            record_breach_end_income, rollback_order_state,
            update_order_state_to_breach_end)

        success, error_msg = await update_order_state_to_breach_end(chat_id)
        if not success:
            return None, error_msg

        income_record_id, error_msg = await record_breach_end_income(
            order_model, amount_validated, user_id
        )
        if income_record_id is None:
            await rollback_order_state(chat_id, "breach")
            return (
                None,
                f"❌ Failed to record income details. Order state rolled back. Error: {error_msg}",
            )

        return income_record_id, None

    @staticmethod
    async def _update_breach_order_statistics(
        amount_validated: float, group_id: str, chat_id: int, order_model: Any
    ) -> Tuple[bool, Optional[str]]:
        """更新违约订单统计数据

        Returns:
            (success, error_msg)
        """
        from services.module3_order.breach_statistics import \
            update_breach_end_statistics

        success, error_msg = await update_breach_end_statistics(
            amount_validated, group_id
        )
        if not success:
            error_info = {
                "operation": "order_breach_end",
                "chat_id": chat_id,
                "order_id": order_model.order_id,
                "amount": amount_validated,
                "error": error_msg,
            }
            logger.error(f"数据不一致风险: {error_info}")
            return (
                False,
                (
                    f"❌ Statistics update failed, but order state and income record saved. "
                    f"Use /fix_statistics to repair. Error: {error_msg}"
                ),
            )
        return True, None

    @staticmethod
    async def complete_breach_order(
        chat_id: int, amount: float, user_id: Optional[int] = None
    ) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """完成违约订单（breach_end状态）

        数据一致性保证：
        1. 更新订单状态
        2. 记录收入明细（源数据）
        3. 更新统计数据（breach_end, liquid_funds）
        4. 如果任何步骤失败，记录错误并回滚

        Returns:
            (success, error_message, operation_data)
        """
        from services.module3_order.breach_record import \
            record_breach_end_operation
        from utils.date_helpers import get_daily_period_date

        is_valid, error_msg, order_model, amount_validated = (
            await OrderService._validate_breach_order(chat_id, amount)
        )
        if not is_valid:
            return False, error_msg, None

        group_id = order_model.group_id
        date_str = get_daily_period_date()

        income_record_id, error_msg = (
            await OrderService._execute_breach_order_completion(
                chat_id, order_model, amount_validated, group_id, user_id
            )
        )
        if income_record_id is None:
            return False, error_msg, None

        success, error_msg = await OrderService._update_breach_order_statistics(
            amount_validated, group_id, chat_id, order_model
        )
        if not success:
            return False, error_msg, None

        operation_data = {
            "chat_id": chat_id,
            "order_id": order_model.order_id,
            "group_id": group_id,
            "amount": amount_validated,
            "date": date_str,
            "income_record_id": income_record_id,
        }
        await record_breach_end_operation(user_id, operation_data, chat_id)

        return True, None, operation_data
