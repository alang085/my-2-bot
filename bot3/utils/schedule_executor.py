"""定时播报执行器（向后兼容层）

此文件保留用于向后兼容，实际功能已拆分到：
- schedule_message_helpers.py - 消息辅助函数
- schedule_broadcast.py - 定时播报任务
- schedule_daily_report.py - 日切报表任务
- schedule_work_messages.py - 开工收工消息任务
- schedule_operations_summary.py - 每日操作汇总任务
- schedule_promotion.py - 公司宣传消息任务
- schedule_data_integrity.py - 数据完整性检查任务
- schedule_backup.py - 数据库备份任务
"""

# 标准库
import logging

# 第三方库
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# 本地模块
from utils.schedule_backup import create_database_backup
from utils.schedule_backup import set_scheduler as set_backup_scheduler
from utils.schedule_backup import setup_database_backup_schedule
from utils.schedule_broadcast import (reload_scheduled_broadcasts,
                                      send_scheduled_broadcast)
from utils.schedule_broadcast import set_scheduler as set_broadcast_scheduler
from utils.schedule_broadcast import setup_scheduled_broadcasts
from utils.schedule_daily_report import send_daily_report
from utils.schedule_daily_report import set_scheduler as set_report_scheduler
from utils.schedule_daily_report import setup_daily_report
from utils.schedule_data_integrity import check_data_integrity
from utils.schedule_data_integrity import \
    set_scheduler as set_integrity_scheduler
from utils.schedule_data_integrity import setup_data_integrity_check_schedule
from utils.schedule_message_helpers import (
    _combine_fixed_message_with_anti_fraud, _combine_message_with_anti_fraud,
    _send_group_message, create_message_keyboard, format_admin_mentions,
    format_admin_mentions_from_group, format_red_message,
    get_current_weekday_index, get_group_admins_from_chat, get_weekday_message,
    select_random_anti_fraud_message, select_rotated_message)
from utils.schedule_operations_summary import (send_daily_operations_summary,
                                               setup_daily_operations_summary)
from utils.schedule_promotion import (send_company_promotion_messages,
                                      send_promotion_messages_internal)
from utils.schedule_promotion import set_scheduler as set_promotion_scheduler
from utils.schedule_promotion import setup_promotion_messages_schedule
from utils.schedule_work_messages import (send_end_work_messages,
                                          send_start_work_messages)
from utils.schedule_work_messages import set_scheduler as set_work_scheduler
from utils.schedule_work_messages import (setup_end_work_schedule,
                                          setup_start_work_schedule)

# 北京时区
BEIJING_TZ = pytz.timezone("Asia/Shanghai")

logger = logging.getLogger(__name__)

# 全局调度器
scheduler = None


def _init_scheduler():
    """初始化全局调度器并设置到各个模块"""
    global scheduler
    if scheduler is None:
        scheduler = AsyncIOScheduler()
        scheduler.start()

    # 设置调度器到各个模块
    set_broadcast_scheduler(scheduler)
    set_report_scheduler(scheduler)
    set_work_scheduler(scheduler)
    set_promotion_scheduler(scheduler)
    set_integrity_scheduler(scheduler)
    set_backup_scheduler(scheduler)


# 导出所有函数以保持向后兼容
__all__ = [
    # 消息辅助函数
    "select_rotated_message",
    "get_current_weekday_index",
    "get_weekday_message",
    "create_message_keyboard",
    "select_random_anti_fraud_message",
    "format_red_message",
    "_send_group_message",
    "_combine_message_with_anti_fraud",
    "_combine_fixed_message_with_anti_fraud",
    "get_group_admins_from_chat",
    "format_admin_mentions_from_group",
    "format_admin_mentions",
    # 定时播报
    "send_scheduled_broadcast",
    "setup_scheduled_broadcasts",
    "reload_scheduled_broadcasts",
    # 日切报表
    "send_daily_report",
    "setup_daily_report",
    # 开工收工消息
    "send_start_work_messages",
    "setup_start_work_schedule",
    "send_end_work_messages",
    "setup_end_work_schedule",
    # 每日操作汇总
    "send_daily_operations_summary",
    "setup_daily_operations_summary",
    # 公司宣传消息
    "send_company_promotion_messages",
    "send_promotion_messages_internal",
    "setup_promotion_messages_schedule",
    # 数据完整性检查
    "check_data_integrity",
    "setup_data_integrity_check_schedule",
    # 数据库备份
    "create_database_backup",
    "setup_database_backup_schedule",
    # 常量和调度器
    "BEIJING_TZ",
    "scheduler",
    "_init_scheduler",
]
