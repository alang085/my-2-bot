"""金额操作服务 - 封装金额相关的业务逻辑"""

import logging
from typing import Any, Dict, Optional, Tuple

import db_operations
from utils.date_helpers import get_daily_period_date
from utils.models import OrderModel, validate_amount
from utils.stats_helpers import update_all_stats, update_liquid_capital

logger = logging.getLogger(__name__)


class AmountService:
    """金额操作业务服务"""

    @staticmethod
    async def _validate_principal_reduction(
        order: Dict[str, Any], amount: float
    ) -> Tuple[bool, Optional[str], Optional[Any], Optional[float]]:
        """验证本金减少请求

        Returns:
            (success, error_msg, order_model, amount_validated)
        """
        from services.module3_order.principal_validation import \
            validate_order_and_amount_for_reduction

        return await validate_order_and_amount_for_reduction(order, amount)

    @staticmethod
    async def _execute_principal_reduction(
        order_model: Any,
        old_amount: float,
        new_amount: float,
        amount_validated: float,
        group_id: str,
        date: str,
        user_id: Optional[int],
    ) -> Tuple[bool, Optional[str], Optional[int]]:
        """执行本金减少操作

        Returns:
            (success, error_msg, income_record_id)
        """
        from services.module3_order.principal_record import \
            record_principal_reduction_income
        from services.module3_order.principal_update import \
            update_order_and_statistics

        success, error_msg = await update_order_and_statistics(
            order_model, old_amount, new_amount, amount_validated, group_id
        )
        if not success:
            return False, error_msg, None

        income_record_id = await record_principal_reduction_income(
            order_model, amount_validated, new_amount, date, group_id, user_id
        )

        return True, None, income_record_id

    @staticmethod
    def _build_principal_reduction_operation_data(
        order_model: Any,
        amount_validated: float,
        old_amount: float,
        new_amount: float,
        group_id: str,
        date: str,
        income_record_id: Optional[int],
    ) -> Dict[str, Any]:
        """构建本金减少操作数据

        Returns:
            操作数据字典
        """
        return {
            "amount": amount_validated,
            "old_amount": old_amount,
            "new_amount": new_amount,
            "group_id": group_id,
            "chat_id": order_model.chat_id,
            "order_id": order_model.order_id,
            "date": date,
            "income_record_id": income_record_id,
        }

    @staticmethod
    @staticmethod
    async def _prepare_principal_reduction_data(
        order_model: Any, amount_validated: float
    ) -> Tuple[float, float, str, str]:
        """准备本金减少数据

        Args:
            order_model: 订单模型
            amount_validated: 验证后的金额

        Returns:
            (旧金额, 新金额, 归属ID, 日期)
        """
        old_amount = order_model.amount
        new_amount = old_amount - amount_validated
        group_id = order_model.group_id
        date = get_daily_period_date()
        return old_amount, new_amount, group_id, date

    @staticmethod
    async def _execute_and_build_principal_reduction_result(
        order_model: Any,
        amount_validated: float,
        old_amount: float,
        new_amount: float,
        group_id: str,
        date: str,
        user_id: Optional[int],
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """执行本金减少并构建结果

        Args:
            order_model: 订单模型
            amount_validated: 验证后的金额
            old_amount: 旧金额
            new_amount: 新金额
            group_id: 归属ID
            date: 日期
            user_id: 用户ID

        Returns:
            (是否成功, 错误消息, 操作数据)
        """
        success, error_msg, income_record_id = (
            await AmountService._execute_principal_reduction(
                order_model,
                old_amount,
                new_amount,
                amount_validated,
                group_id,
                date,
                user_id,
            )
        )
        if not success:
            return False, error_msg, None

        operation_data = AmountService._build_principal_reduction_operation_data(
            order_model,
            amount_validated,
            old_amount,
            new_amount,
            group_id,
            date,
            income_record_id,
        )

        return True, None, operation_data

    async def process_principal_reduction(
        order: Dict[str, Any],
        amount: float,
        user_id: Optional[int] = None,
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """处理本金减少

        数据一致性保证：
        1. 验证订单状态和金额
        2. 更新订单金额
        3. 更新统计数据（valid, completed, liquid_funds）
        4. 记录收入明细
        5. 如果任何步骤失败，记录错误并回滚

        Args:
            order: 订单字典
            amount: 减少的金额
            user_id: 用户ID（用于记录操作历史）

        Returns:
            Tuple[success, error_message, operation_data]:
                - success: 是否成功
                - error_message: 错误消息（如果失败）
                - operation_data: 操作数据（用于记录历史）
        """
        try:
            success, error_msg, order_model, amount_validated = (
                await AmountService._validate_principal_reduction(order, amount)
            )
            if not success:
                return False, error_msg, None

            old_amount, new_amount, group_id, date = (
                await AmountService._prepare_principal_reduction_data(
                    order_model, amount_validated
                )
            )

            return await AmountService._execute_and_build_principal_reduction_result(
                order_model,
                amount_validated,
                old_amount,
                new_amount,
                group_id,
                date,
                user_id,
            )

        except Exception as e:
            logger.error(f"处理本金减少时出错: {e}", exc_info=True)
            return False, "❌ Error processing request.", None

    @staticmethod
    async def _validate_interest_input(
        order: Dict[str, Any], amount: float
    ) -> Tuple[bool, Optional[str], Optional[Any], Optional[float]]:
        """验证利息输入

        Returns:
            (success, error_msg, order_model, amount_validated)
        """
        from services.module3_order.interest_validation import \
            validate_order_and_amount

        return await validate_order_and_amount(order, amount)

    @staticmethod
    async def _execute_interest_processing(
        order_model: Any,
        amount_validated: float,
        prepared_data: dict,
        user_id: Optional[int],
    ) -> Tuple[bool, Optional[str], Optional[int]]:
        """执行利息处理操作

        Returns:
            (success, error_msg, income_record_id)
        """
        from services.module3_order.interest_record import record_income_detail
        from services.module3_order.interest_update import \
            update_interest_statistics

        group_id = prepared_data["group_id"]
        date = prepared_data["date"]
        note = prepared_data["note"]

        success, error_msg, income_record_id = await record_income_detail(
            order_model, amount_validated, date, group_id, note, user_id
        )
        if not success:
            return False, error_msg, None

        success, error_msg = await update_interest_statistics(
            amount_validated, group_id, order_model
        )
        if not success:
            return False, error_msg, None

        return True, None, income_record_id

    @staticmethod
    async def _update_interest_credit_system(
        order_model: Any, amount_validated: float, prepared_data: dict
    ) -> None:
        """更新利息信用系统"""
        from services.module3_order.interest_credit import update_credit_system

        order_state = prepared_data["order_state"]
        customer_id = prepared_data["customer_id"]
        await update_credit_system(
            order_state, customer_id, order_model, amount_validated
        )

    @staticmethod
    def _build_interest_operation_data(
        order_model: Any,
        amount_validated: float,
        prepared_data: dict,
        income_record_id: Optional[int],
    ) -> Dict[str, Any]:
        """构建利息操作数据

        Returns:
            操作数据字典
        """
        from services.module3_order.interest_history import \
            prepare_operation_data

        group_id = prepared_data["group_id"]
        date = prepared_data["date"]
        return prepare_operation_data(
            amount_validated, group_id, order_model, date, income_record_id
        )

    @staticmethod
    @staticmethod
    async def _validate_and_prepare_interest(
        order: Dict[str, Any], amount: float
    ) -> Tuple[bool, Optional[str], Optional[Any], Optional[float], Optional[Dict]]:
        """验证并准备利息数据

        Args:
            order: 订单字典
            amount: 利息金额

        Returns:
            (是否成功, 错误消息, 订单模型, 验证后的金额, 准备的数据)
        """
        from services.module3_order.interest_prepare import \
            prepare_interest_data

        success, error_msg, order_model, amount_validated = (
            await AmountService._validate_interest_input(order, amount)
        )
        if not success:
            return False, error_msg, None, None, None

        prepared_data = await prepare_interest_data(order_model, amount_validated)
        return True, None, order_model, amount_validated, prepared_data

    @staticmethod
    async def _process_interest_execution(
        order_model: Any,
        amount_validated: float,
        prepared_data: Dict,
        user_id: Optional[int],
    ) -> Tuple[bool, Optional[str], Optional[int]]:
        """执行利息处理

        Args:
            order_model: 订单模型
            amount_validated: 验证后的金额
            prepared_data: 准备的数据
            user_id: 用户ID

        Returns:
            (是否成功, 错误消息, 收入记录ID)
        """
        return await AmountService._execute_interest_processing(
            order_model, amount_validated, prepared_data, user_id
        )

    async def process_interest(
        order: Dict[str, Any],
        amount: float,
        user_id: Optional[int] = None,
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """处理利息收入（支持订单完成后的补利息）

        数据一致性保证：
        1. 验证金额有效性
        2. 记录收入明细（源数据）
        3. 更新统计数据（interest, liquid_funds）
        4. 如果任何步骤失败，记录错误并提示用户修复

        Args:
            order: 订单字典
            amount: 利息金额
            user_id: 用户ID（用于记录操作历史）

        Returns:
            Tuple[success, error_message, operation_data]:
                - success: 是否成功
                - error_message: 错误消息（如果失败）
                - operation_data: 操作数据（用于记录历史）
        """
        try:
            success, error_msg, order_model, amount_validated, prepared_data = (
                await AmountService._validate_and_prepare_interest(order, amount)
            )
            if not success:
                return False, error_msg, None

            success, error_msg, income_record_id = (
                await AmountService._process_interest_execution(
                    order_model, amount_validated, prepared_data, user_id
                )
            )
            if not success:
                return False, error_msg, None

            await AmountService._update_interest_credit_system(
                order_model, amount_validated, prepared_data
            )

            operation_data = AmountService._build_interest_operation_data(
                order_model, amount_validated, prepared_data, income_record_id
            )

            return True, None, operation_data

        except Exception as e:
            logger.error(f"处理利息收入时出错: {e}", exc_info=True)
            return False, "❌ Error processing request.", None

    @staticmethod
    async def _record_interest_income_without_order(
        amount_validated: float, date: str, user_id: Optional[int]
    ) -> Tuple[bool, Optional[str]]:
        """记录无关联订单的利息收入明细

        Returns:
            (success, error_msg)
        """
        try:
            await db_operations.record_income(
                date=date,
                type="interest",
                amount=amount_validated,
                group_id=None,
                order_id=None,
                order_date=None,
                customer=None,
                weekday_group=None,
                note="利息收入（无关联订单）",
                created_by=user_id,
            )
            return True, None
        except Exception as e:
            logger.error(f"记录利息收入明细失败: {e}", exc_info=True)
            return False, f"❌ Failed to record income details. Error: {str(e)}"

    @staticmethod
    async def _update_interest_statistics_without_order(
        amount_validated: float,
    ) -> Tuple[bool, Optional[str]]:
        """更新无关联订单的利息统计数据

        Returns:
            (success, error_msg)
        """
        try:
            await update_all_stats("interest", amount_validated, 0, None)
            await update_liquid_capital(amount_validated)
            return True, None
        except Exception as e:
            logger.error(f"更新利息收入统计数据失败: {e}", exc_info=True)
            return False, f"❌ Statistics update failed. Error: {str(e)}"

    @staticmethod
    def _build_interest_operation_data(
        amount_validated: float, date: str
    ) -> Dict[str, Any]:
        """构建利息操作数据

        Returns:
            操作数据字典
        """
        return {
            "amount": amount_validated,
            "group_id": None,
            "order_id": None,
            "date": date,
        }

    @staticmethod
    async def process_interest_without_order(
        amount: float,
        user_id: Optional[int] = None,
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """处理无关联订单的利息收入

        Args:
            amount: 利息金额
            user_id: 用户ID（用于记录操作历史）

        Returns:
            Tuple[success, error_message, operation_data]:
                - success: 是否成功
                - error_message: 错误消息（如果失败）
                - operation_data: 操作数据（用于记录历史）
        """
        try:
            try:
                amount_validated = validate_amount(amount)
            except ValueError as e:
                return False, f"❌ Failed: {str(e)}", None

            date = get_daily_period_date()

            success, error_msg = (
                await AmountService._record_interest_income_without_order(
                    amount_validated, date, user_id
                )
            )
            if not success:
                return False, error_msg, None

            success, error_msg = (
                await AmountService._update_interest_statistics_without_order(
                    amount_validated
                )
            )
            if not success:
                return False, error_msg, None

            operation_data = AmountService._build_interest_operation_data(
                amount_validated, date
            )
            return True, None, operation_data

        except Exception as e:
            logger.error(f"处理无关联订单利息收入时出错: {e}", exc_info=True)
            return False, "❌ Error processing request.", None
