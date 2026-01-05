"""支付账号服务 - 封装支付账号相关的业务逻辑"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import db_operations

# from db.repositories import PaymentRepository  # 暂未实现

logger = logging.getLogger(__name__)

# 创建 Repository 实例（暂未使用）
# _payment_repository = PaymentRepository()


class PaymentService:
    """支付账号业务服务"""

    @staticmethod
    async def get_all_accounts() -> List[Dict[str, Any]]:
        """获取所有支付账号

        Returns:
            支付账号列表
        """
        # 使用 Repository（逐步迁移）
        # return await _payment_repository.find_all(None, order_by="account_type account_name")
        # 暂时保持使用 db_operations 以保持兼容性
        return await db_operations.get_all_payment_accounts()

    @staticmethod
    async def get_accounts_by_type(account_type: str) -> List[Dict[str, Any]]:
        """获取指定类型的支付账号

        Args:
            account_type: 账号类型（"gcash" 或 "paymaya"）

        Returns:
            支付账号列表
        """
        return await db_operations.get_payment_accounts_by_type(account_type)

    @staticmethod
    async def get_accounts(account_type: str) -> List[Dict[str, Any]]:
        """获取支付账号（兼容旧接口）

        Args:
            account_type: 账号类型

        Returns:
            支付账号列表
        """
        return await db_operations.get_payment_accounts(account_type)

    @staticmethod
    async def update_account(
        account_type: str,
        account_number: Optional[str] = None,
        account_name: Optional[str] = None,
        balance: Optional[float] = None,
    ) -> Tuple[bool, Optional[str]]:
        """更新支付账号信息

        Args:
            account_type: 账号类型
            account_number: 账号号码（可选）
            account_name: 账户名称（可选）
            balance: 余额（可选）

        Returns:
            Tuple[success, error_message]:
                - success: 是否成功
                - error_message: 错误消息（如果失败）
        """
        try:
            success = await db_operations.update_payment_account(
                account_type,
                account_number=account_number,
                account_name=account_name,
                balance=balance,
            )
            if success:
                return True, None
            else:
                return False, "❌ 更新失败"
        except Exception as e:
            logger.error(f"更新支付账号失败: {e}", exc_info=True)
            return False, f"❌ 更新失败: {str(e)}"

    @staticmethod
    async def get_balance_summary_by_date(date_str: str) -> Optional[Dict[str, Any]]:
        """获取指定日期的余额汇总

        Args:
            date_str: 日期字符串（YYYY-MM-DD）

        Returns:
            余额汇总字典，包含 gcash_total, paymaya_total, total, account_details
        """
        return await db_operations.get_balance_summary_by_date(date_str)

    @staticmethod
    async def get_account_by_id(account_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取支付账号

        Args:
            account_id: 账户ID

        Returns:
            支付账号字典，如果不存在则返回 None
        """
        return await db_operations.get_payment_account_by_id(account_id)

    @staticmethod
    async def update_account_by_id(
        account_id: int,
        account_number: Optional[str] = None,
        account_name: Optional[str] = None,
        balance: Optional[float] = None,
    ) -> Tuple[bool, Optional[str]]:
        """根据ID更新支付账号信息

        Args:
            account_id: 账户ID
            account_number: 账号号码（可选）
            account_name: 账户名称（可选）
            balance: 余额（可选）

        Returns:
            Tuple[success, error_message]:
                - success: 是否成功
                - error_message: 错误消息（如果失败）
        """
        try:
            success = await db_operations.update_payment_account_by_id(
                account_id,
                account_number=account_number,
                account_name=account_name,
                balance=balance,
            )
            if success:
                return True, None
            else:
                return False, "❌ 更新失败"
        except Exception as e:
            logger.error(f"更新支付账号失败: {e}", exc_info=True)
            return False, f"❌ 更新失败: {str(e)}"

    @staticmethod
    async def calculate_total_balance(
        accounts: List[Dict[str, Any]],
    ) -> Tuple[float, float, float]:
        """计算总余额

        Args:
            accounts: 账户列表

        Returns:
            Tuple[gcash_total, paymaya_total, total]:
                - gcash_total: GCash 总余额
                - paymaya_total: PayMaya 总余额
                - total: 总余额
        """
        gcash_total = 0.0
        paymaya_total = 0.0

        for account in accounts:
            account_type = account.get("account_type", "")
            balance = account.get("balance", 0) or 0.0

            if account_type == "gcash":
                gcash_total += balance
            elif account_type == "paymaya":
                paymaya_total += balance

        total = gcash_total + paymaya_total
        return gcash_total, paymaya_total, total
