"""开工收工消息任务

包含开工和收工消息的发送和设置功能。
"""

# 标准库
import logging
from typing import Dict, Tuple

# 第三方库
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# 本地模块
import db_operations
from utils.schedule_message_helpers import (
    _combine_fixed_message_with_anti_fraud, _send_group_message,
    get_current_weekday_index, get_weekday_message)

# 北京时区
BEIJING_TZ = pytz.timezone("Asia/Shanghai")

logger = logging.getLogger(__name__)

# 全局调度器（从主模块导入）
scheduler = None


def set_scheduler(sched):
    """设置全局调度器"""
    global scheduler
    scheduler = sched


async def _get_group_configs() -> list:
    """获取群组消息配置

    Returns:
        配置列表
    """
    logger.info("正在获取群组消息配置...")
    configs = await db_operations.get_group_message_configs()
    logger.info(f"获取到 {len(configs) if configs else 0} 个群组配置")
    return configs or []


async def _send_message_to_group(
    bot, config: dict, weekday_index: int, success_count: int, fail_count: int
) -> tuple[int, int]:
    """向单个群组发送消息

    Args:
        bot: Telegram Bot实例
        config: 群组配置
        weekday_index: 星期索引
        success_count: 成功计数
        fail_count: 失败计数

    Returns:
        (success_count, fail_count)
    """
    chat_id = config.get("chat_id")
    if not chat_id:
        logger.warning(f"群组配置缺少 chat_id，跳过")
        return success_count, fail_count

    try:
        main_message = get_weekday_message(config, "start_work_message", weekday_index)
        anti_fraud = get_weekday_message(config, "anti_fraud_message", weekday_index)

        if not main_message:
            logger.warning(
                f"群组 {chat_id} 的开工消息（星期{weekday_index}）未配置，跳过"
            )
            return success_count, fail_count

        final_message = _combine_fixed_message_with_anti_fraud(main_message, anti_fraud)
        bot_links = config.get("bot_links") or None
        worker_links = config.get("worker_links") or None

        if await _send_group_message(
            bot, chat_id, final_message, bot_links, worker_links
        ):
            success_count += 1
            logger.info(f"✅ 开工信息已发送到群组 {chat_id} (星期{weekday_index})")
        else:
            fail_count += 1
            logger.warning(
                f"❌ 群组 {chat_id} 发送失败（_send_group_message 返回 False）"
            )
    except Exception as e:
        fail_count += 1
        logger.error(f"❌ 发送开工信息到群组 {chat_id} 失败: {e}", exc_info=True)

    return success_count, fail_count


async def send_start_work_messages(bot):
    """发送开工信息到所有配置的总群（按星期几选择固定文案）"""
    logger.info("=" * 60)
    logger.info("开始执行发送开工信息任务")
    logger.info("=" * 60)
    try:
        configs = await _get_group_configs()
        if not configs:
            logger.info("没有配置的总群，跳过发送开工信息")
            return

        weekday_index = get_current_weekday_index()
        logger.info(f"当前是星期{weekday_index}，开始处理 {len(configs)} 个群组")

        success_count = 0
        fail_count = 0

        for i, config in enumerate(configs, 1):
            logger.info(f"处理群组 {i}/{len(configs)}: chat_id={config.get('chat_id')}")
            success_count, fail_count = await _send_message_to_group(
                bot, config, weekday_index, success_count, fail_count
            )

        logger.info("=" * 60)
        logger.info(
            f"开工信息发送完成: 成功 {success_count}, 失败 {fail_count} (星期{weekday_index})"
        )
        logger.info("=" * 60)
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"发送开工信息任务失败: {e}", exc_info=True)
        logger.error("=" * 60)


async def setup_start_work_schedule(bot, sched=None):
    """设置开工信息定时任务（每天11:00执行）"""
    global scheduler
    if sched:
        scheduler = sched

    if scheduler is None:
        scheduler = AsyncIOScheduler()
        scheduler.start()

    try:
        scheduler.add_job(
            send_start_work_messages,
            trigger=CronTrigger(hour=11, minute=0, timezone=BEIJING_TZ),
            args=[bot],
            id="start_work_messages",
            replace_existing=True,
        )
        logger.info("已设置开工信息任务: 每天 11:00 自动发送")
    except Exception as e:
        logger.error(f"设置开工信息任务失败: {e}", exc_info=True)


async def _process_single_end_work_message(
    bot, config: Dict, weekday_index: int
) -> Tuple[bool, int]:
    """处理单个群组的收工消息发送

    Args:
        bot: 机器人实例
        config: 群组配置
        weekday_index: 星期索引

    Returns:
        (是否成功, 群组ID)
    """
    chat_id = config.get("chat_id")
    bot_links = config.get("bot_links") or None
    worker_links = config.get("worker_links") or None

    if not chat_id:
        return False, 0

    try:
        main_message = get_weekday_message(config, "end_work_message", weekday_index)
        anti_fraud = get_weekday_message(config, "anti_fraud_message", weekday_index)

        if not main_message:
            logger.debug(
                f"群组 {chat_id} 的收工消息（星期{weekday_index}）未配置，跳过"
            )
            return False, 0

        final_message = _combine_fixed_message_with_anti_fraud(main_message, anti_fraud)

        if await _send_group_message(
            bot, chat_id, final_message, bot_links, worker_links
        ):
            logger.info(f"收工信息已发送到群组 {chat_id} (星期{weekday_index})")
            return True, chat_id
        else:
            return False, chat_id
    except Exception as e:
        logger.error(f"发送收工信息到群组 {chat_id} 失败: {e}", exc_info=True)
        return False, chat_id


async def send_end_work_messages(bot):
    """发送收工信息到所有配置的总群（按星期几选择固定文案）"""
    try:
        configs = await db_operations.get_group_message_configs()

        if not configs:
            logger.info("没有配置的总群，跳过发送收工信息")
            return

        weekday_index = get_current_weekday_index()
        success_count = 0
        fail_count = 0

        for config in configs:
            success, _ = await _process_single_end_work_message(
                bot, config, weekday_index
            )
            if success:
                success_count += 1
            else:
                fail_count += 1

        logger.info(
            f"收工信息发送完成: 成功 {success_count}, 失败 {fail_count} (星期{weekday_index})"
        )
    except Exception as e:
        logger.error(f"发送收工信息失败: {e}", exc_info=True)


async def setup_end_work_schedule(bot, sched=None):
    """设置收工信息定时任务（每天23:00执行）"""
    global scheduler
    if sched:
        scheduler = sched

    if scheduler is None:
        scheduler = AsyncIOScheduler()
        scheduler.start()

    try:
        scheduler.add_job(
            send_end_work_messages,
            trigger=CronTrigger(hour=23, minute=0, timezone=BEIJING_TZ),
            args=[bot],
            id="end_work_messages",
            replace_existing=True,
        )
        logger.info("已设置收工信息任务: 每天 23:00 自动发送")
    except Exception as e:
        logger.error(f"设置收工信息任务失败: {e}", exc_info=True)
