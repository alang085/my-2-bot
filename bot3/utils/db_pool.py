"""数据库连接池管理模块

提供数据库连接池功能，复用连接以提高性能，减少连接创建开销。
支持连接健康检查和自动重连机制。
"""

import asyncio
import logging
import os
import sqlite3
from contextlib import asynccontextmanager
from typing import Optional

import aiosqlite

logger = logging.getLogger(__name__)

# 数据库文件路径
DATA_DIR = os.getenv(
    "DATA_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
os.makedirs(DATA_DIR, exist_ok=True)
DB_NAME = os.path.join(DATA_DIR, "loan_bot.db")


class ConnectionPool:
    """SQLite 连接池管理器

    使用 aiosqlite 提供异步连接池功能，支持连接复用和健康检查。
    """

    def __init__(
        self, db_path: str = DB_NAME, pool_size: int = 5, max_overflow: int = 10
    ):
        """
        初始化连接池

        Args:
            db_path: 数据库文件路径
            pool_size: 连接池大小（默认5个连接）
            max_overflow: 最大溢出连接数（默认10个）
        """
        self.db_path = db_path
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self._pool: asyncio.Queue = asyncio.Queue(maxsize=pool_size + max_overflow)
        self._created_connections = 0
        self._lock = asyncio.Lock()
        self._closed = False

    async def initialize(self) -> None:
        """初始化连接池，预创建连接"""
        logger.info(
            f"初始化数据库连接池 (pool_size={self.pool_size}, max_overflow={self.max_overflow})"
        )

        # 预创建连接
        for _ in range(min(self.pool_size, 3)):  # 预创建3个连接
            conn = await self._create_connection()
            await self._pool.put(conn)
            self._created_connections += 1

        logger.info(f"连接池初始化完成，预创建 {self._created_connections} 个连接")

    async def _create_connection(self) -> aiosqlite.Connection:
        """创建新的数据库连接"""
        conn = await aiosqlite.connect(
            self.db_path,
            check_same_thread=False,
            timeout=10.0,  # 10秒超时
        )
        # 设置 row_factory 为 Row，返回字典式结果
        conn.row_factory = aiosqlite.Row
        return conn

    async def _is_connection_healthy(self, conn: aiosqlite.Connection) -> bool:
        """检查连接是否健康"""
        try:
            # 执行简单查询检查连接
            await asyncio.wait_for(conn.execute("SELECT 1"), timeout=1.0)
            return True
        except Exception as e:
            logger.warning(f"连接健康检查失败: {e}")
            return False

    @asynccontextmanager
    async def _get_connection_from_pool(self) -> Optional[aiosqlite.Connection]:
        """从池中获取连接

        Returns:
            数据库连接
        """
        try:
            return await asyncio.wait_for(self._pool.get(), timeout=2.0)
        except asyncio.TimeoutError:
            async with self._lock:
                if self._created_connections < self.pool_size + self.max_overflow:
                    conn = await self._create_connection()
                    self._created_connections += 1
                    logger.debug(f"创建新连接 (总数: {self._created_connections})")
                    return conn
                else:
                    return await self._pool.get()

    async def _ensure_connection_healthy(
        self, conn: Optional[aiosqlite.Connection]
    ) -> Optional[aiosqlite.Connection]:
        """确保连接健康

        Args:
            conn: 数据库连接

        Returns:
            健康的连接
        """
        if conn and not await self._is_connection_healthy(conn):
            logger.warning("连接不健康，创建新连接")
            try:
                await conn.close()
            except Exception:
                pass
            return await self._create_connection()
        return conn

    async def _return_connection_to_pool(
        self, conn: Optional[aiosqlite.Connection]
    ) -> None:
        """归还连接到池中

        Args:
            conn: 数据库连接
        """
        if not conn or self._closed:
            return

        try:
            if await self._is_connection_healthy(conn):
                await self._pool.put(conn)
            else:
                try:
                    await conn.close()
                except Exception:
                    pass
                self._created_connections -= 1
        except Exception as e:
            logger.error(f"归还连接到池时出错: {e}")
            try:
                await conn.close()
            except Exception:
                pass
            self._created_connections -= 1

    async def acquire(self):
        """获取数据库连接（上下文管理器）

        Usage:
            async with pool.acquire() as conn:
                cursor = await conn.execute("SELECT * FROM orders")
                rows = await cursor.fetchall()
        """
        if self._closed:
            raise RuntimeError("连接池已关闭")

        conn: Optional[aiosqlite.Connection] = None

        try:
            conn = await self._get_connection_from_pool()
            conn = await self._ensure_connection_healthy(conn)
            yield conn

        finally:
            await self._return_connection_to_pool(conn)

    async def close(self) -> None:
        """关闭连接池，释放所有连接"""
        if self._closed:
            return

        self._closed = True
        logger.info("正在关闭连接池...")

        # 关闭所有连接
        closed_count = 0
        while not self._pool.empty():
            try:
                conn = await asyncio.wait_for(self._pool.get_nowait(), timeout=0.1)
                await conn.close()
                closed_count += 1
            except (asyncio.TimeoutError, asyncio.QueueEmpty):
                break
            except Exception as e:
                logger.error(f"关闭连接时出错: {e}")

        logger.info(f"连接池已关闭，释放了 {closed_count} 个连接")

    async def get_stats(self) -> dict:
        """获取连接池统计信息"""
        return {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "created_connections": self._created_connections,
            "available_connections": self._pool.qsize(),
            "closed": self._closed,
        }


# 全局连接池实例
_pool: Optional[ConnectionPool] = None
_pool_lock: Optional[asyncio.Lock] = None


def _get_pool_lock() -> asyncio.Lock:
    """获取连接池锁（延迟初始化）"""
    global _pool_lock
    if _pool_lock is None:
        try:
            _pool_lock = asyncio.Lock()
        except RuntimeError:
            # 如果没有事件循环，创建一个新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            _pool_lock = asyncio.Lock()
    return _pool_lock


async def get_pool() -> ConnectionPool:
    """获取全局连接池实例（单例模式）"""
    global _pool

    if _pool is None:
        lock = _get_pool_lock()
        async with lock:
            if _pool is None:
                _pool = ConnectionPool()
                await _pool.initialize()

    return _pool


async def close_pool() -> None:
    """关闭全局连接池"""
    global _pool

    if _pool is not None:
        lock = _get_pool_lock()
        async with lock:
            if _pool is not None:
                await _pool.close()
                _pool = None


# 同步连接池（用于向后兼容）
# 注意：_sync_pool_lock 已移除，因为 get_sync_connection 不使用连接池
# 如果将来需要同步连接池，可以在函数内部延迟初始化锁


def get_sync_connection():
    """获取同步数据库连接（向后兼容）

    注意：此函数用于保持与现有同步代码的兼容性。
    新代码应该使用异步连接池。

    此函数动态读取 init_db.DB_NAME，以支持测试环境修改数据库路径。
    """
    # 动态导入 init_db 以获取最新的 DB_NAME（支持测试环境修改）
    import init_db

    db_path = init_db.DB_NAME

    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn
