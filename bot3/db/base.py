"""
数据库操作基础模块

提供数据库连接、装饰器等基础功能。
"""

# 标准库
import asyncio
import logging
import os
from functools import wraps

# 日志
logger = logging.getLogger(__name__)

# 数据库文件路径
DATA_DIR = os.getenv(
    "DATA_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
os.makedirs(DATA_DIR, exist_ok=True)
DB_NAME = os.path.join(DATA_DIR, "loan_bot.db")


def get_connection():
    """获取数据库连接（同步，向后兼容）

    注意：新代码应该使用异步连接池 (utils.db_pool.get_pool())
    此函数保留用于向后兼容。
    """
    from utils.db_pool import get_sync_connection

    return get_sync_connection()


def db_transaction(func):
    """数据库事务装饰器"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_running_loop()

        def sync_work():
            conn = get_connection()
            cursor = conn.cursor()
            try:
                result = func(conn, cursor, *args, **kwargs)
                if result is not False:
                    conn.commit()
                return result
            except ValueError as e:
                # ValueError是验证错误，应该向上传播，让调用者处理
                conn.rollback()
                logger.error(f"Validation error in {func.__name__}: {e}")
                raise
            except Exception as e:
                conn.rollback()
                logger.error(f"Database error in {func.__name__}: {e}", exc_info=True)
                return False
            finally:
                conn.close()

        return await loop.run_in_executor(None, sync_work)

    return wrapper


def db_query(func):
    """数据库查询装饰器"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_running_loop()

        def sync_work():
            conn = get_connection()
            cursor = conn.cursor()
            try:
                return func(conn, cursor, *args, **kwargs)
            except Exception as e:
                logger.error(
                    f"Database query error in {func.__name__}: {e}", exc_info=True
                )
                raise e
            finally:
                conn.close()

        return await loop.run_in_executor(None, sync_work)

    return wrapper


# ========== 异步数据库操作函数（用于模块6兼容） ==========


async def execute_query(
    query: str,
    params: tuple = (),
    fetch_one: bool = False,
    fetch_all: bool = False,
    use_cache: bool = True,
):
    """执行数据库查询（异步，用于模块6兼容）

    Args:
        query: SQL查询语句
        params: 查询参数
        fetch_one: 是否只获取一条记录
        fetch_all: 是否获取所有记录
        use_cache: 是否使用缓存（仅对SELECT查询有效）

    Returns:
        查询结果
    """

    # 使用同步方式（通过装饰器模式）
    def sync_work():
        conn = get_connection()
        cursor = conn.cursor()
        # 设置row_factory为字典
        cursor.row_factory = lambda cursor, row: dict(
            zip([col[0] for col in cursor.description], row)
        )
        try:
            cursor.execute(query, params)
            if fetch_one:
                row = cursor.fetchone()
                return dict(row) if row else None
            elif fetch_all:
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            else:
                return None
        finally:
            conn.close()

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, sync_work)


async def execute_transaction(query: str, params: tuple = ()) -> bool:
    """执行数据库事务操作（异步，用于模块6兼容）

    Args:
        query: SQL语句
        params: 查询参数

    Returns:
        是否成功
    """

    def sync_work():
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"数据库事务执行失败: {e}", exc_info=True)
            return False
        finally:
            conn.close()

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, sync_work)
