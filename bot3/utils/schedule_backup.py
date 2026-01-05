"""数据库备份任务

包含数据库备份的定时任务功能。
"""

# 标准库
import logging

# 第三方库
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# 北京时区
BEIJING_TZ = pytz.timezone("Asia/Shanghai")

logger = logging.getLogger(__name__)

# 全局调度器（从主模块导入）
scheduler = None


def set_scheduler(sched):
    """设置全局调度器"""
    global scheduler
    scheduler = sched


async def create_database_backup(bot):
    """创建数据库备份（定时任务）"""
    try:
        from utils.backup_manager import (cleanup_old_backups, create_backup,
                                          verify_backup)

        logger.info("开始创建数据库备份...")

        # 创建备份
        backup_path = create_backup()

        # 验证备份
        if verify_backup(backup_path):
            logger.info(f"数据库备份创建成功: {backup_path}")

            # 清理旧备份（只保留最新的10个）
            deleted_count = cleanup_old_backups(keep_count=10)
            if deleted_count > 0:
                logger.info(f"已清理 {deleted_count} 个旧备份")
        else:
            logger.error("数据库备份验证失败")

    except Exception as e:
        logger.error(f"创建数据库备份失败: {e}", exc_info=True)


async def setup_database_backup_schedule(bot, sched=None):
    """设置数据库备份定时任务（每天凌晨2点执行）"""
    global scheduler
    if sched:
        scheduler = sched

    if scheduler is None:
        scheduler = AsyncIOScheduler()
        scheduler.start()

    try:
        # 移除旧任务（如果存在）
        try:
            scheduler.remove_job("database_backup")
            logger.info("已移除旧的数据库备份任务")
        except Exception as e:
            logger.debug(f"移除旧任务时出错（可忽略）: {e}")

        # 添加定时任务（每天凌晨2点执行）
        scheduler.add_job(
            create_database_backup,
            trigger=CronTrigger(hour=2, minute=0, timezone=BEIJING_TZ),
            args=[bot],
            id="database_backup",
            replace_existing=True,
        )
        logger.info("已设置数据库备份任务: 每天 02:00 自动备份")
    except Exception as e:
        logger.error(f"设置数据库备份任务失败: {e}", exc_info=True)
