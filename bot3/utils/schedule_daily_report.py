"""日切报表任务

包含日切报表的生成和发送功能。
"""

# 标准库
import logging
from datetime import datetime, timedelta

# 第三方库
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# 本地模块
import db_operations
from config import ADMIN_IDS

# 北京时区
BEIJING_TZ = pytz.timezone("Asia/Shanghai")

logger = logging.getLogger(__name__)

# 全局调度器（从主模块导入）
scheduler = None


def set_scheduler(sched):
    """设置全局调度器"""
    global scheduler
    scheduler = sched


async def send_daily_report(bot):
    """发送日切报表Excel文件给所有管理员和授权员工（业务员）（每天生成两个Excel：订单总表和每日变化数据）"""
    from utils.schedule_daily_report_cleanup import cleanup_temp_files
    from utils.schedule_daily_report_date import get_report_date
    from utils.schedule_daily_report_error import send_error_notification
    from utils.schedule_daily_report_excel import generate_excel_files
    from utils.schedule_daily_report_recipients import get_all_recipients
    from utils.schedule_daily_report_send import send_excel_files_to_recipients

    logger.info("=" * 60)
    logger.info("开始执行每日报表生成任务")
    logger.info("=" * 60)
    try:
        # 获取日切日期
        report_date = get_report_date()
        logger.info(f"开始生成每日Excel报表 ({report_date})")

        # 生成Excel文件
        orders_excel_path, changes_excel_path = await generate_excel_files(report_date)

        # 获取所有接收人
        all_recipients = await get_all_recipients()

        # 发送Excel文件
        success_count, fail_count = await send_excel_files_to_recipients(
            bot, all_recipients, orders_excel_path, changes_excel_path, report_date
        )

        # 清理临时文件
        cleanup_temp_files([orders_excel_path, changes_excel_path])

        logger.info(f"每日Excel报表发送完成: 成功 {success_count}, 失败 {fail_count}")
        logger.info("=" * 60)
        logger.info("每日报表生成任务执行完成")
        logger.info("=" * 60)
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"发送每日Excel报表失败: {e}", exc_info=True)
        logger.error("=" * 60)
        # 发送错误通知给管理员
        await send_error_notification(bot, e)


async def setup_daily_report(bot, sched=None):
    """设置日切报表自动发送任务（每天23:05执行）"""
    global scheduler
    if sched:
        scheduler = sched

    if scheduler is None:
        scheduler = AsyncIOScheduler()
        scheduler.start()

    # 添加日切报表任务
    try:
        scheduler.add_job(
            send_daily_report,
            trigger=CronTrigger(hour=23, minute=5, timezone=BEIJING_TZ),
            args=[bot],
            id="daily_report",
            replace_existing=True,
        )
        logger.info("已设置日切报表任务: 每天 23:05 自动发送")
    except Exception as e:
        logger.error(f"设置日切报表任务失败: {e}", exc_info=True)
