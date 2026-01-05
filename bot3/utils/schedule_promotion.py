"""公司宣传消息任务

包含公司宣传语录的发送和设置功能。
"""

# 标准库
import logging
import random
from typing import Optional, Tuple

# 第三方库
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

# 本地模块
import db_operations
from utils.schedule_message_helpers import (
    _combine_fixed_message_with_anti_fraud, _send_group_message,
    get_current_weekday_index, get_weekday_message)

logger = logging.getLogger(__name__)

# 全局调度器（从主模块导入）
scheduler = None


def set_scheduler(sched):
    """设置全局调度器"""
    global scheduler
    scheduler = sched


async def send_company_promotion_messages(bot):
    """轮播发送公司宣传语录到所有配置的总群（每3小时）"""
    await send_promotion_messages_internal(bot)


async def _get_valid_promotion_message() -> Optional[str]:
    """获取有效的宣传语录

    Returns:
        宣传语录文本，如果没有则返回None
    """
    promotion_messages = await db_operations.get_active_promotion_messages()
    if not promotion_messages:
        logger.info("没有激活的公司宣传语录，跳过发送")
        return None

    valid_messages = [
        msg
        for msg in promotion_messages
        if msg.get("message") and msg.get("message").strip()
    ]

    if not valid_messages:
        logger.warning("没有有效的公司宣传语录（所有消息都为空），跳过发送")
        return None

    selected_msg_dict = random.choice(valid_messages)
    selected_message = selected_msg_dict.get("message")

    if not selected_message or not selected_message.strip():
        logger.warning("选中的宣传语录消息为空，跳过发送")
        return None

    return selected_message


async def _send_promotion_to_group(
    bot,
    config: dict,
    selected_message: str,
    weekday_index: int,
    success_count: int,
    fail_count: int,
) -> tuple[int, int]:
    """向单个群组发送宣传消息

    Args:
        bot: Telegram Bot实例
        config: 群组配置
        selected_message: 选中的宣传消息
        weekday_index: 星期索引
        success_count: 成功计数
        fail_count: 失败计数

    Returns:
        (success_count, fail_count)
    """
    chat_id = config.get("chat_id")
    if not chat_id:
        return success_count, fail_count

    try:
        anti_fraud = get_weekday_message(config, "anti_fraud_message", weekday_index)
        final_message = _combine_fixed_message_with_anti_fraud(
            selected_message, anti_fraud
        )
        bot_links = config.get("bot_links") or None
        worker_links = config.get("worker_links") or None

        if await _send_group_message(
            bot, chat_id, final_message, bot_links, worker_links
        ):
            success_count += 1
            logger.info(f"公司宣传语录已发送到群组 {chat_id} (星期{weekday_index})")
        else:
            fail_count += 1
    except Exception as e:
        fail_count += 1
        logger.error(f"发送公司宣传语录到群组 {chat_id} 失败: {e}", exc_info=True)

    return success_count, fail_count


async def send_promotion_messages_internal(bot):
    """内部函数：发送公司宣传语录"""
    try:
        selected_message = await _get_valid_promotion_message()
        if not selected_message:
            return

        configs = await db_operations.get_group_message_configs()
        if not configs:
            logger.info("没有配置的总群，跳过发送公司宣传语录")
            return

        weekday_index = get_current_weekday_index()
        success_count = 0
        fail_count = 0

        for config in configs:
            success_count, fail_count = await _send_promotion_to_group(
                bot, config, selected_message, weekday_index, success_count, fail_count
            )

        logger.info(
            f"公司宣传语录发送完成: 成功 {success_count}, 失败 {fail_count} (星期{weekday_index})"
        )
    except Exception as e:
        logger.error(f"发送公司宣传语录失败: {e}", exc_info=True)


async def setup_promotion_messages_schedule(bot, sched=None):
    """设置公司宣传语录轮播任务（每3小时执行一次）"""
    global scheduler
    if sched:
        scheduler = sched

    if scheduler is None:
        scheduler = AsyncIOScheduler()
        scheduler.start()

    try:
        # 移除旧任务（如果存在）
        try:
            scheduler.remove_job("company_promotion_messages")
            logger.info("已移除旧的宣传语录任务")
        except Exception as e:
            logger.debug(f"移除旧任务时出错（可忽略）: {e}")

        # 添加定时任务（每3小时执行一次）
        scheduler.add_job(
            send_company_promotion_messages,
            trigger=IntervalTrigger(hours=3),
            args=[bot],
            id="promotion_messages_schedule",
            replace_existing=True,
        )
        logger.info("已设置公司宣传语录轮播任务: 每 3 小时自动发送")
    except Exception as e:
        logger.error(f"设置公司宣传语录轮播任务失败: {e}", exc_info=True)
