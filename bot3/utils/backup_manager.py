"""数据库备份管理模块

提供自动数据库备份、备份验证和快速恢复功能。
"""

import logging
import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# 数据库文件路径
DATA_DIR = os.getenv(
    "DATA_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
os.makedirs(DATA_DIR, exist_ok=True)
DB_NAME = os.path.join(DATA_DIR, "loan_bot.db")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)


def create_backup(backup_name: Optional[str] = None) -> str:
    """创建数据库备份

    Args:
        backup_name: 备份文件名（可选），如果不提供则自动生成

    Returns:
        备份文件路径

    Raises:
        FileNotFoundError: 如果数据库文件不存在
        IOError: 如果备份失败
    """
    if not os.path.exists(DB_NAME):
        raise FileNotFoundError(f"数据库文件不存在: {DB_NAME}")

    if backup_name is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"loan_bot_backup_{timestamp}.db"

    backup_path = os.path.join(BACKUP_DIR, backup_name)

    try:
        # 使用 SQLite 的备份 API 创建备份
        source_conn = sqlite3.connect(DB_NAME)
        backup_conn = sqlite3.connect(backup_path)

        source_conn.backup(backup_conn)

        backup_conn.close()
        source_conn.close()

        logger.info(f"数据库备份已创建: {backup_path}")
        return backup_path

    except Exception as e:
        logger.error(f"创建数据库备份失败: {e}", exc_info=True)
        raise IOError(f"备份失败: {e}")


def verify_backup(backup_path: str) -> bool:
    """验证备份文件是否有效

    Args:
        backup_path: 备份文件路径

    Returns:
        如果备份有效返回 True，否则返回 False
    """
    if not os.path.exists(backup_path):
        logger.error(f"备份文件不存在: {backup_path}")
        return False

    try:
        # 尝试打开备份文件并执行简单查询
        conn = sqlite3.connect(backup_path)
        cursor = conn.cursor()

        # 检查关键表是否存在
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='orders'"
        )
        if not cursor.fetchone():
            logger.error("备份文件缺少关键表")
            conn.close()
            return False

        # 执行简单查询验证数据库完整性
        cursor.execute("SELECT COUNT(*) FROM orders LIMIT 1")
        cursor.fetchone()

        conn.close()
        logger.info(f"备份文件验证成功: {backup_path}")
        return True

    except Exception as e:
        logger.error(f"验证备份文件失败: {e}", exc_info=True)
        return False


def restore_backup(backup_path: str, create_backup_before_restore: bool = True) -> bool:
    """从备份恢复数据库

    Args:
        backup_path: 备份文件路径
        create_backup_before_restore: 是否在恢复前创建当前数据库的备份

    Returns:
        如果恢复成功返回 True，否则返回 False
    """
    if not os.path.exists(backup_path):
        logger.error(f"备份文件不存在: {backup_path}")
        return False

    # 验证备份文件
    if not verify_backup(backup_path):
        logger.error("备份文件验证失败，无法恢复")
        return False

    try:
        # 在恢复前创建当前数据库的备份（如果启用）
        if create_backup_before_restore and os.path.exists(DB_NAME):
            try:
                create_backup(
                    backup_name=f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                )
                logger.info("已创建恢复前的备份")
            except Exception as e:
                logger.warning(f"创建恢复前备份失败: {e}")

        # 关闭可能存在的数据库连接
        # 注意：在实际使用中，需要确保没有其他进程正在使用数据库

        # 复制备份文件到数据库位置
        shutil.copy2(backup_path, DB_NAME)

        # 验证恢复后的数据库
        if verify_backup(DB_NAME):
            logger.info(f"数据库已从备份恢复: {backup_path}")
            return True
        else:
            logger.error("恢复后的数据库验证失败")
            return False

    except Exception as e:
        logger.error(f"恢复数据库失败: {e}", exc_info=True)
        return False


def list_backups() -> list[dict]:
    """列出所有备份文件

    Returns:
        备份文件信息列表，每个元素包含：
        - name: 文件名
        - path: 完整路径
        - size: 文件大小（字节）
        - created_at: 创建时间（从文件名推断）
    """
    backups = []

    if not os.path.exists(BACKUP_DIR):
        return backups

    for filename in os.listdir(BACKUP_DIR):
        if filename.endswith(".db") and "backup" in filename.lower():
            file_path = os.path.join(BACKUP_DIR, filename)
            file_stat = os.stat(file_path)

            # 尝试从文件名提取时间戳
            created_at = None
            try:
                if "_" in filename:
                    timestamp_str = filename.split("_")[-1].replace(".db", "")
                    created_at = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            except Exception:
                pass

            backups.append(
                {
                    "name": filename,
                    "path": file_path,
                    "size": file_stat.st_size,
                    "created_at": created_at,
                    "modified_at": datetime.fromtimestamp(file_stat.st_mtime),
                }
            )

    # 按创建时间排序（最新的在前）
    backups.sort(key=lambda x: x["created_at"] or datetime.min, reverse=True)

    return backups


def cleanup_old_backups(keep_count: int = 10) -> int:
    """清理旧备份，只保留最新的 N 个

    Args:
        keep_count: 保留的备份数量

    Returns:
        删除的备份数量
    """
    backups = list_backups()

    if len(backups) <= keep_count:
        return 0

    # 删除多余的备份
    deleted_count = 0
    for backup in backups[keep_count:]:
        try:
            os.remove(backup["path"])
            logger.info(f"已删除旧备份: {backup['name']}")
            deleted_count += 1
        except Exception as e:
            logger.error(f"删除备份失败 {backup['name']}: {e}")

    return deleted_count
