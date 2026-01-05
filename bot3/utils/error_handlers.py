"""错误处理工具模块

提供统一的错误处理模式和重试机制。
"""

import asyncio
import logging
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

logger = logging.getLogger(__name__)

# 类型变量
T = TypeVar("T")


class RetryableError(Exception):
    """可重试的错误"""

    pass


class NonRetryableError(Exception):
    """不可重试的错误"""

    pass


async def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
    *args,
    **kwargs,
) -> T:
    """
    带指数退避的重试机制

    Args:
        func: 要重试的函数
        max_retries: 最大重试次数
        initial_delay: 初始延迟（秒）
        backoff_factor: 退避因子
        exceptions: 需要重试的异常类型
        *args: 函数位置参数
        **kwargs: 函数关键字参数

    Returns:
        函数返回值

    Raises:
        最后一次尝试的异常
    """
    delay = initial_delay
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except exceptions as e:
            last_exception = e
            if attempt < max_retries:
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                await asyncio.sleep(delay)
                delay *= backoff_factor
            else:
                logger.error(f"All {max_retries + 1} attempts failed. Last error: {e}")
                raise

    # 理论上不会到达这里，但为了类型检查
    if last_exception:
        raise last_exception
    raise Exception("Unexpected error in retry_with_backoff")


def retry(
    max_retries: int = 3, initial_delay: float = 1.0, backoff_factor: float = 2.0
):
    """
    重试装饰器

    Args:
        max_retries: 最大重试次数
        initial_delay: 初始延迟（秒）
        backoff_factor: 退避因子

    Usage:
        @retry(max_retries=3, initial_delay=1.0)
        async def risky_operation():
            ...
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await retry_with_backoff(
                func,
                max_retries=max_retries,
                initial_delay=initial_delay,
                backoff_factor=backoff_factor,
                *args,
                **kwargs,
            )

        return wrapper

    return decorator


class ErrorHandler:
    """统一错误处理器"""

    @staticmethod
    def handle_database_error(error: Exception, operation: str) -> str:
        """
        处理数据库错误

        Args:
            error: 异常对象
            operation: 操作名称

        Returns:
            用户友好的错误消息
        """
        error_msg = str(error).lower()

        if "locked" in error_msg or "busy" in error_msg:
            return f"❌ 数据库繁忙，请稍后重试 ({operation})"
        elif "no such table" in error_msg:
            return f"❌ 数据库表不存在，请联系管理员 ({operation})"
        elif "foreign key" in error_msg:
            return f"❌ 数据关联错误 ({operation})"
        elif "unique constraint" in error_msg or "duplicate" in error_msg:
            return f"❌ 数据已存在，不能重复 ({operation})"
        else:
            logger.error(f"Database error in {operation}: {error}", exc_info=True)
            return f"❌ 数据库操作失败 ({operation})"

    @staticmethod
    def handle_validation_error(error: Exception, field: str = "") -> str:
        """
        处理验证错误

        Args:
            error: 异常对象
            field: 字段名称

        Returns:
            用户友好的错误消息
        """
        error_msg = str(error)

        if "amount" in error_msg.lower() or "金额" in error_msg:
            return f"❌ 金额格式错误，请输入有效的数字"
        elif "date" in error_msg.lower() or "日期" in error_msg:
            return f"❌ 日期格式错误，请使用 YYYY-MM-DD 格式"
        elif field:
            return f"❌ {field} 验证失败: {error_msg}"
        else:
            return f"❌ 数据验证失败: {error_msg}"

    @staticmethod
    def handle_api_error(error: Exception, api_name: str = "") -> str:
        """
        处理API错误

        Args:
            error: 异常对象
            api_name: API名称

        Returns:
            用户友好的错误消息
        """
        error_msg = str(error).lower()

        if "timeout" in error_msg:
            return f"❌ 请求超时，请稍后重试 ({api_name})"
        elif "rate limit" in error_msg or "too many requests" in error_msg:
            return f"❌ 请求过于频繁，请稍后重试 ({api_name})"
        elif "unauthorized" in error_msg or "forbidden" in error_msg:
            return f"❌ 权限不足 ({api_name})"
        elif "not found" in error_msg:
            return f"❌ 资源不存在 ({api_name})"
        else:
            logger.error(f"API error in {api_name}: {error}", exc_info=True)
            return f"❌ API调用失败 ({api_name})"

    @staticmethod
    def handle_generic_error(error: Exception, context: str = "") -> str:
        """
        处理通用错误

        Args:
            error: 异常对象
            context: 上下文信息

        Returns:
            用户友好的错误消息
        """
        logger.error(f"Error in {context}: {error}", exc_info=True)
        return f"❌ 操作失败: {str(error)}"


# 全局错误处理器实例
error_handler = ErrorHandler()
