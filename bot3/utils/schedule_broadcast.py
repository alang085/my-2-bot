"""定时播报任务

包含定时播报的发送和设置功能。
"""

# 标准库
import logging

# 第三方库
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# 本地模块
import db_operations

# 北京时区
BEIJING_TZ = pytz.timezone("Asia/Shanghai")

logger = logging.getLogger(__name__)

# 全局调度器（从主模块导入）
scheduler = None


def set_scheduler(sched):
    """设置全局调度器"""
    global scheduler
    scheduler = sched


async def send_scheduled_broadcast(bot, broadcast):
    """发送定时播报"""
    try:
        chat_id = broadcast["chat_id"]
        message = broadcast["message"]

        if not chat_id:
            logger.warning(f"播报 {broadcast['slot']} 没有设置chat_id，跳过发送")
            return

        await bot.send_message(chat_id=chat_id, text=message)
        logger.info(f"定时播报 {broadcast['slot']} 已发送到群组 {chat_id}")
    except Exception as e:
        logger.error(f"发送定时播报 {broadcast['slot']} 失败: {e}", exc_info=True)


async def setup_scheduled_broadcasts(bot, sched=None):
    """设置定时播报任务"""
    global scheduler
    if sched:
        scheduler = sched

    if scheduler is None:
        scheduler = AsyncIOScheduler()
        scheduler.start()

    # 只清除播报任务（不清除日切报表任务）
    for job in scheduler.get_jobs():
        if job.id.startswith("broadcast_"):
            scheduler.remove_job(job.id)

    # 获取所有激活的定时播报
    broadcasts = await db_operations.get_active_scheduled_broadcasts()

    for broadcast in broadcasts:
        try:
            time_str = broadcast["time"]
            # 解析时间 (HH:MM 或 HH)
            time_parts = time_str.split(":")
            hour = int(time_parts[0])
            minute = int(time_parts[1]) if len(time_parts) > 1 else 0

            # 创建定时任务（每天执行）
            job_id = f"broadcast_{broadcast['slot']}"

            scheduler.add_job(
                send_scheduled_broadcast,
                trigger=CronTrigger(hour=hour, minute=minute, timezone=BEIJING_TZ),
                args=[bot, broadcast],
                id=job_id,
                replace_existing=True,
            )

            logger.info(
                f"已设置定时播报 {broadcast['slot']}: 每天 {time_str} "
                f"发送到群组 {broadcast['chat_id']}"
            )
        except Exception as e:
            logger.error(f"设置定时播报 {broadcast['slot']} 失败: {e}", exc_info=True)


async def reload_scheduled_broadcasts(bot, sched=None):
    """重新加载定时播报任务"""
    await setup_scheduled_broadcasts(bot, sched)
