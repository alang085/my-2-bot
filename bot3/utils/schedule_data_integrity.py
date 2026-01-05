"""数据完整性检查任务

包含数据完整性检查的定时任务功能。
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


async def check_data_integrity(bot):
    """数据完整性检查（定时任务）"""
    try:
        from utils.data_integrity_checker import (auto_fix_common_issues,
                                                  check_orders_consistency)

        logger.info("开始执行数据完整性检查...")

        # 执行一致性检查
        check_result = await check_orders_consistency()

        if check_result.get("status") == "issues_found":
            issues = check_result.get("issues", [])
            logger.warning(f"发现 {len(issues)} 个数据一致性问题")
            for issue in issues:
                logger.warning(f"  - {issue.get('message', '未知问题')}")

            # 尝试自动修复
            fix_result = await auto_fix_common_issues()
            if fix_result.get("status") == "success":
                fixes = fix_result.get("fixes_applied", [])
                if fixes:
                    logger.info(f"已自动修复 {len(fixes)} 个问题")
                    for fix in fixes:
                        logger.info(f"  - {fix}")
        elif check_result.get("status") == "success":
            logger.info("数据完整性检查通过")
        else:
            logger.error(f"数据完整性检查失败: {check_result.get('error')}")

    except Exception as e:
        logger.error(f"数据完整性检查失败: {e}", exc_info=True)


async def setup_data_integrity_check_schedule(bot, sched=None):
    """设置数据完整性检查定时任务（每天凌晨3点执行）"""
    global scheduler
    if sched:
        scheduler = sched

    if scheduler is None:
        scheduler = AsyncIOScheduler()
        scheduler.start()

    try:
        # 移除旧任务（如果存在）
        try:
            scheduler.remove_job("data_integrity_check")
            logger.info("已移除旧的数据完整性检查任务")
        except Exception as e:
            logger.debug(f"移除旧任务时出错（可忽略）: {e}")

        # 添加定时任务（每天凌晨3点执行）
        scheduler.add_job(
            check_data_integrity,
            trigger=CronTrigger(hour=3, minute=0, timezone=BEIJING_TZ),
            args=[bot],
            id="data_integrity_check",
            replace_existing=True,
        )
        logger.info("已设置数据完整性检查任务: 每天 03:00 自动检查")
    except Exception as e:
        logger.error(f"设置数据完整性检查任务失败: {e}", exc_info=True)
