"""缓存工具模块

提供简单的内存缓存机制，用于缓存频繁查询的数据。
"""

import logging
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar

logger = logging.getLogger(__name__)

# 类型变量
T = TypeVar("T")

# 全局缓存存储
_cache: Dict[str, Dict[str, Any]] = {}


class CacheManager:
    """缓存管理器"""

    def __init__(self, default_ttl: int = 300):
        """
        初始化缓存管理器

        Args:
            default_ttl: 默认缓存过期时间（秒），默认5分钟
        """
        self.default_ttl = default_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，如果不存在或已过期则返回None
        """
        if key not in self._cache:
            return None

        entry = self._cache[key]
        if time.time() > entry["expires_at"]:
            # 缓存已过期，删除
            del self._cache[key]
            return None

        return entry["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），如果为None则使用默认值
        """
        ttl = ttl or self.default_ttl
        self._cache[key] = {
            "value": value,
            "expires_at": time.time() + ttl,
            "created_at": time.time(),
        }

    def delete(self, key: str) -> None:
        """
        删除缓存

        Args:
            key: 缓存键
        """
        if key in self._cache:
            del self._cache[key]

    def clear(self) -> None:
        """清空所有缓存"""
        self._cache.clear()

    def invalidate_pattern(self, pattern: str) -> None:
        """
        按模式删除缓存（支持前缀匹配）

        Args:
            pattern: 缓存键前缀
        """
        keys_to_delete = [key for key in self._cache.keys() if key.startswith(pattern)]
        for key in keys_to_delete:
            del self._cache[key]

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            缓存统计信息字典
        """
        total_size = len(self._cache)
        expired_count = sum(
            1 for entry in self._cache.values() if time.time() > entry["expires_at"]
        )

        return {
            "total_entries": total_size,
            "expired_entries": expired_count,
            "active_entries": total_size - expired_count,
        }


# 全局缓存管理器实例
_default_cache = CacheManager(default_ttl=300)


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    缓存装饰器

    Args:
        ttl: 缓存过期时间（秒），默认5分钟
        key_prefix: 缓存键前缀

    Usage:
        @cached(ttl=600, key_prefix="order_")
        async def get_order(chat_id: int):
            ...
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # 生成缓存键
            cache_key = f"{key_prefix}{func.__name__}"
            if args:
                cache_key += f"_{hash(args)}"
            if kwargs:
                cache_key += f"_{hash(tuple(sorted(kwargs.items())))}"

            # 尝试从缓存获取
            cached_value = _default_cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_value

            # 缓存未命中，执行函数
            logger.debug(f"Cache miss: {cache_key}")
            result = await func(*args, **kwargs)

            # 将结果存入缓存
            _default_cache.set(cache_key, result, ttl)
            return result

        return wrapper

    return decorator


def invalidate_cache(pattern: str) -> None:
    """
    使缓存失效

    Args:
        pattern: 缓存键前缀模式
    """
    _default_cache.invalidate_pattern(pattern)


def clear_cache() -> None:
    """清空所有缓存"""
    _default_cache.clear()


def get_cache_stats() -> Dict[str, Any]:
    """
    获取缓存统计信息

    Returns:
        缓存统计信息字典
    """
    return _default_cache.get_stats()
