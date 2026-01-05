"""自定义异常类

定义统一的错误类型体系，用于错误处理和错误码机制。
"""

from typing import Optional


class BaseAppError(Exception):
    """应用基础异常类

    所有自定义异常的基类，提供统一的错误码和错误消息格式。
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        """
        初始化异常

        Args:
            message: 错误消息
            error_code: 错误码（可选）
            details: 错误详情（可选）
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}

    def __str__(self) -> str:
        """返回错误消息"""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class ValidationError(BaseAppError):
    """输入验证错误"""

    pass


class DatabaseError(BaseAppError):
    """数据库操作错误"""

    pass


class PermissionError(BaseAppError):
    """权限错误"""

    pass


class NotFoundError(BaseAppError):
    """资源未找到错误"""

    pass


class BusinessLogicError(BaseAppError):
    """业务逻辑错误"""

    pass


class RateLimitError(BaseAppError):
    """速率限制错误"""

    pass


class ConfigurationError(BaseAppError):
    """配置错误"""

    pass
