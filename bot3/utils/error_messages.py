"""统一错误消息模块

提供统一的错误消息格式，提高用户体验一致性。
"""

from typing import Optional


class ErrorMessages:
    """统一错误消息类"""

    @staticmethod
    def order_not_found(chat_id: Optional[int] = None) -> str:
        """
        订单未找到错误消息

        Args:
            chat_id: 群组ID（可选）

        Returns:
            错误消息字符串
        """
        if chat_id:
            return f"❌ 未找到订单（群组ID: {chat_id}）"
        return "❌ 未找到订单"

    @staticmethod
    def insufficient_funds(current: float, required: float) -> str:
        """
        资金不足错误消息

        Args:
            current: 当前余额
            required: 需要金额

        Returns:
            错误消息字符串
        """
        missing = required - current
        return (
            f"❌ 资金不足\n"
            f"当前余额: {current:,.2f}\n"
            f"需要金额: {required:,.2f}\n"
            f"缺少: {missing:,.2f}"
        )

    @staticmethod
    def database_error(operation: str) -> str:
        """
        数据库操作错误消息

        Args:
            operation: 操作名称

        Returns:
            错误消息字符串
        """
        return f"❌ 数据库操作失败: {operation}"

    @staticmethod
    def invalid_amount_format() -> str:
        """金额格式错误消息"""
        return "❌ 金额格式错误，请输入有效的数字（例如: +1000 或 +1000b）"

    @staticmethod
    def invalid_amount() -> str:
        """无效金额错误消息"""
        return "❌ 无效金额格式"

    @staticmethod
    def no_active_order() -> str:
        """没有活跃订单错误消息"""
        return "❌ 此群组没有活跃订单"

    @staticmethod
    def processing_error() -> str:
        """处理请求错误消息"""
        return "❌ 处理请求时出错"

    @staticmethod
    def income_record_failed(error: Optional[str] = None) -> str:
        """
        记录收入明细失败错误消息

        Args:
            error: 错误详情（可选）

        Returns:
            错误消息字符串
        """
        base_msg = "❌ 记录收入明细失败，请稍后重试或联系管理员"
        if error:
            return f"{base_msg}。错误: {error}"
        return base_msg

    @staticmethod
    def statistics_update_failed(error: Optional[str] = None) -> str:
        """
        统计数据更新失败错误消息

        Args:
            error: 错误详情（可选）

        Returns:
            错误消息字符串
        """
        base_msg = (
            "❌ 更新统计失败，但收入明细已记录。请使用 /fix_statistics 修复统计数据"
        )
        if error:
            return f"{base_msg}。错误: {error}"
        return base_msg

    @staticmethod
    def validation_error(field: str, message: Optional[str] = None) -> str:
        """
        验证错误消息

        Args:
            field: 字段名称
            message: 错误详情（可选）

        Returns:
            错误消息字符串
        """
        base_msg = f"❌ {field} 验证失败"
        if message:
            return f"{base_msg}: {message}"
        return base_msg

    @staticmethod
    def permission_denied() -> str:
        """权限不足错误消息"""
        return "❌ 权限不足，此操作需要管理员权限"

    @staticmethod
    def operation_failed(operation: str, reason: Optional[str] = None) -> str:
        """
        操作失败错误消息

        Args:
            operation: 操作名称
            reason: 失败原因（可选）

        Returns:
            错误消息字符串
        """
        base_msg = f"❌ {operation} 失败"
        if reason:
            return f"{base_msg}: {reason}"
        return base_msg

    @staticmethod
    def state_transition_invalid(old_state: str, new_state: str) -> str:
        """
        状态转换无效错误消息

        Args:
            old_state: 旧状态
            new_state: 新状态

        Returns:
            错误消息字符串
        """
        return f"❌ 状态转换无效: {old_state} -> {new_state}"

    @staticmethod
    def order_already_exists(chat_id: Optional[int] = None) -> str:
        """
        订单已存在错误消息

        Args:
            chat_id: 群组ID（可选）

        Returns:
            错误消息字符串
        """
        if chat_id:
            return f"❌ 此群组已有订单（群组ID: {chat_id}）"
        return "❌ 此群组已有订单"

    @staticmethod
    def order_update_failed() -> str:
        """订单更新失败错误消息"""
        return "❌ 订单更新失败"

    @staticmethod
    def order_creation_failed(reason: Optional[str] = None) -> str:
        """
        订单创建失败错误消息

        Args:
            reason: 失败原因（可选）

        Returns:
            错误消息字符串
        """
        base_msg = "❌ 订单创建失败"
        if reason:
            return f"{base_msg}: {reason}"
        return base_msg

    @staticmethod
    def invalid_date_format() -> str:
        """日期格式错误消息"""
        return "❌ 日期格式错误，请使用 YYYY-MM-DD 格式"

    @staticmethod
    def invalid_user_id() -> str:
        """无效用户ID错误消息"""
        return "❌ 无效的用户ID"

    @staticmethod
    def missing_required_field(field: str) -> str:
        """
        缺少必需字段错误消息

        Args:
            field: 字段名称

        Returns:
            错误消息字符串
        """
        return f"❌ 缺少必需字段: {field}"
