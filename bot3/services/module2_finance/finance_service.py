"""财务服务 - 封装财务相关的业务逻辑"""

import logging
from typing import Dict, Optional, Tuple

import db_operations

logger = logging.getLogger(__name__)


class FinanceService:
    """财务业务服务"""

    @staticmethod
    async def get_financial_summary() -> Dict:
        """获取财务摘要"""
        return await db_operations.get_financial_data()

    @staticmethod
    async def get_income_records(
        start_date: str, end_date: str, income_type: Optional[str] = None
    ) -> list:
        """获取收入记录"""
        return await db_operations.get_income_records(
            start_date, end_date, type=income_type
        )

    @staticmethod
    async def get_expense_records(
        start_date: str, end_date: str, expense_type: Optional[str] = None
    ) -> list:
        """获取支出记录"""
        return await db_operations.get_expense_records(
            start_date, end_date, expense_type
        )

    @staticmethod
    @staticmethod
    async def _validate_funds_adjustment(
        amount: float,
    ) -> Tuple[bool, Optional[str], Optional[float]]:
        """验证资金调整

        Args:
            amount: 调整金额

        Returns:
            (是否有效, 错误消息, 当前余额)
        """
        financial_data = await db_operations.get_financial_data()
        if not financial_data:
            return False, "❌ Failed to get financial data.", None

        current_balance = financial_data.get("liquid_funds", 0.0)
        new_balance = current_balance + amount

        if new_balance < 0:
            return (
                False,
                f"❌ Insufficient funds. Current: {current_balance:.2f}, "
                f"Required: {abs(amount):.2f}",
                None,
            )

        return True, None, current_balance

    @staticmethod
    async def _record_funds_adjustment_operation(
        user_id: Optional[int],
        amount: float,
        current_balance: float,
        new_balance: float,
    ) -> None:
        """记录资金调整操作历史

        Args:
            user_id: 用户ID
            amount: 调整金额
            current_balance: 当前余额
            new_balance: 新余额
        """
        if user_id:
            try:
                await db_operations.record_operation(
                    user_id=user_id,
                    operation_type="funds_adjusted",
                    operation_data={
                        "amount": amount,
                        "old_balance": current_balance,
                        "new_balance": new_balance,
                    },
                    chat_id=None,
                )
            except Exception as e:
                logger.warning(f"记录操作历史失败（不影响主流程）: {e}", exc_info=True)

    async def adjust_funds(
        amount: float, user_id: Optional[int] = None
    ) -> Tuple[bool, Optional[str]]:
        """调整资金

        Args:
            amount: 调整金额（正数为增加，负数为减少）
            user_id: 用户ID（用于记录操作历史）

        Returns:
            (success, error_message)
        """
        try:
            is_valid, error_msg, current_balance = (
                await FinanceService._validate_funds_adjustment(amount)
            )
            if not is_valid:
                return False, error_msg

            await db_operations.update_financial_data("liquid_funds", amount)

            new_balance = current_balance + amount
            await FinanceService._record_funds_adjustment_operation(
                user_id, amount, current_balance, new_balance
            )

            return True, None
        except Exception as e:
            logger.error(f"调整资金失败: {e}", exc_info=True)
            return False, f"❌ Failed to adjust funds. Error: {str(e)}"
