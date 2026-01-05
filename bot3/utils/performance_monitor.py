"""性能监控工具模块

提供性能监控和统计功能。
"""

import asyncio
import logging
import time
from collections import defaultdict
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar

logger = logging.getLogger(__name__)

# 类型变量
T = TypeVar("T")

# 性能统计存储
_performance_stats: Dict[str, List[float]] = defaultdict(list)
_performance_counters: Dict[str, int] = defaultdict(int)


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        self.stats: Dict[str, List[float]] = defaultdict(list)
        self.counters: Dict[str, int] = defaultdict(int)
        self.errors: Dict[str, int] = defaultdict(int)

    def record_timing(self, operation: str, duration: float) -> None:
        """
        记录操作耗时

        Args:
            operation: 操作名称
            duration: 耗时（秒）
        """
        self.stats[operation].append(duration)
        if len(self.stats[operation]) > 1000:  # 限制存储数量
            self.stats[operation] = self.stats[operation][-1000:]

    def increment_counter(self, operation: str, count: int = 1) -> None:
        """
        增加计数器

        Args:
            operation: 操作名称
            count: 增加数量
        """
        self.counters[operation] += count

    def record_error(self, operation: str) -> None:
        """
        记录错误

        Args:
            operation: 操作名称
        """
        self.errors[operation] += 1

    def get_stats(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """
        获取统计信息

        Args:
            operation: 操作名称，如果为None则返回所有操作的统计

        Returns:
            统计信息字典
        """
        if operation:
            timings = self.stats.get(operation, [])
            if not timings:
                return {
                    "operation": operation,
                    "count": 0,
                    "avg_time": 0.0,
                    "min_time": 0.0,
                    "max_time": 0.0,
                    "total_time": 0.0,
                    "errors": self.errors.get(operation, 0),
                }

            return {
                "operation": operation,
                "count": len(timings),
                "avg_time": sum(timings) / len(timings),
                "min_time": min(timings),
                "max_time": max(timings),
                "total_time": sum(timings),
                "errors": self.errors.get(operation, 0),
            }
        else:
            # 返回所有操作的统计
            result = {}
            for op in set(list(self.stats.keys()) + list(self.counters.keys())):
                result[op] = self.get_stats(op)
            return result

    def reset(self, operation: Optional[str] = None) -> None:
        """
        重置统计信息

        Args:
            operation: 操作名称，如果为None则重置所有统计
        """
        if operation:
            self.stats.pop(operation, None)
            self.counters.pop(operation, None)
            self.errors.pop(operation, None)
        else:
            self.stats.clear()
            self.counters.clear()
            self.errors.clear()


# 全局性能监控器实例
_performance_monitor = PerformanceMonitor()


def _record_successful_operation(
    op_name: str, duration: float, duration_ms: float, threshold_ms: float
) -> None:
    """记录成功操作的性能

    Args:
        op_name: 操作名称
        duration: 持续时间（秒）
        duration_ms: 持续时间（毫秒）
        threshold_ms: 性能阈值（毫秒）
    """
    _performance_monitor.record_timing(op_name, duration)
    _performance_monitor.increment_counter(op_name)

    if duration_ms > threshold_ms:
        logger.warning(
            f"慢操作警告: {op_name} 耗时 {duration_ms:.2f}ms (阈值: {threshold_ms:.2f}ms)"
        )


def _record_failed_operation(
    op_name: str, duration: float, duration_ms: float, threshold_ms: float
) -> None:
    """记录失败操作的性能

    Args:
        op_name: 操作名称
        duration: 持续时间（秒）
        duration_ms: 持续时间（毫秒）
        threshold_ms: 性能阈值（毫秒）
    """
    _performance_monitor.record_timing(op_name, duration)
    _performance_monitor.record_error(op_name)

    if duration_ms > threshold_ms:
        logger.warning(
            f"慢操作警告（出错）: {op_name} 耗时 {duration_ms:.2f}ms (阈值: {threshold_ms:.2f}ms)"
        )


def monitor_performance(
    operation_name: Optional[str] = None, threshold_ms: float = 1000.0
):
    """
    性能监控装饰器

    Args:
        operation_name: 操作名称，如果为None则使用函数名
        threshold_ms: 性能阈值（毫秒），超过此值会记录警告

    Usage:
        @monitor_performance("get_order", threshold_ms=500)
        async def get_order(chat_id: int):
            ...
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        op_name = operation_name or func.__name__

        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                duration = time.perf_counter() - start_time
                duration_ms = duration * 1000

                _record_successful_operation(
                    op_name, duration, duration_ms, threshold_ms
                )
                return result
            except Exception as e:
                duration = time.perf_counter() - start_time
                duration_ms = duration * 1000

                _record_failed_operation(op_name, duration, duration_ms, threshold_ms)
                raise

        return wrapper

    return decorator


def get_performance_stats(operation: Optional[str] = None) -> Dict[str, Any]:
    """
    获取性能统计信息

    Args:
        operation: 操作名称，如果为None则返回所有操作的统计

    Returns:
        统计信息字典
    """
    return _performance_monitor.get_stats(operation)


def reset_performance_stats(operation: Optional[str] = None) -> None:
    """
    重置性能统计信息

    Args:
        operation: 操作名称，如果为None则重置所有统计
    """
    _performance_monitor.reset(operation)


def log_performance_summary() -> None:
    """记录性能摘要日志"""
    stats = _performance_monitor.get_stats()
    if not stats:
        logger.info("No performance statistics available")
        return

    logger.info("=" * 60)
    logger.info("Performance Summary")
    logger.info("=" * 60)

    slow_operations = []
    for operation, data in sorted(stats.items()):
        if data["count"] > 0:
            avg_ms = data["avg_time"] * 1000
            max_ms = data["max_time"] * 1000

            logger.info(
                f"{operation}: "
                f"count={data['count']}, "
                f"avg={avg_ms:.2f}ms, "
                f"min={data['min_time']*1000:.2f}ms, "
                f"max={max_ms:.2f}ms, "
                f"errors={data['errors']}"
            )

            # 识别慢操作（平均耗时超过500ms或最大耗时超过1000ms）
            if avg_ms > 500 or max_ms > 1000:
                slow_operations.append((operation, avg_ms, max_ms))

    if slow_operations:
        logger.warning("=" * 60)
        logger.warning("慢操作警告:")
        for op, avg, max_time in slow_operations:
            logger.warning(f"  {op}: 平均={avg:.2f}ms, 最大={max_time:.2f}ms")
        logger.warning("=" * 60)

    logger.info("=" * 60)
