"""订单播报相关工具函数

包含订单创建后自动播报的功能。
"""

# 标准库
import logging
from typing import List, Optional

# 第三方库
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

# 本地模块
import db_operations
from utils.broadcast_helpers import (calculate_next_payment_date,
                                     format_broadcast_message)

logger = logging.getLogger(__name__)


def _parse_links(links: Optional[str]) -> List[str]:
    """解析链接字符串

    Args:
        links: 链接字符串（多行）

    Returns:
        链接列表
    """
    if not links:
        return []

    return [
        link.strip()
        for link in links.split("\n")
        if link.strip()
        and (link.strip().startswith("http://") or link.strip().startswith("https://"))
    ]


def _build_broadcast_keyboard(
    bot_links: Optional[str], worker_links: Optional[str]
) -> Optional[InlineKeyboardMarkup]:
    """构建播报内联键盘

    Args:
        bot_links: 机器人链接
        worker_links: 人工链接

    Returns:
        内联键盘，如果没有链接则返回None
    """
    keyboard = []
    bot_link_list = _parse_links(bot_links)
    worker_link_list = _parse_links(worker_links)

    if bot_link_list:
        keyboard.append([InlineKeyboardButton("Bot", url=bot_link_list[0])])
    if worker_link_list:
        keyboard.append([InlineKeyboardButton("Worker", url=worker_link_list[0])])

    return InlineKeyboardMarkup(keyboard) if keyboard else None


async def _prepare_broadcast_message(amount: float, order_date: Optional[str]) -> str:
    """准备播报消息

    Args:
        amount: 订单金额
        order_date: 订单日期

    Returns:
        播报消息文本
    """
    principal = amount
    principal_12 = principal * 0.12
    outstanding_interest = 0

    _, date_str, weekday_str = calculate_next_payment_date(order_date)
    return format_broadcast_message(
        principal=principal,
        principal_12=principal_12,
        outstanding_interest=outstanding_interest,
        date_str=date_str,
        weekday_str=weekday_str,
    )


async def send_auto_broadcast(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    amount: float,
    order_date: str = None,
):
    """订单创建后自动播报下一期还款（无中文，带内联键盘）"""
    try:
        message = await _prepare_broadcast_message(amount, order_date)

        config = await db_operations.get_group_message_config_by_chat_id(chat_id)
        bot_links = config.get("bot_links") if config else None
        worker_links = config.get("worker_links") if config else None

        reply_markup = _build_broadcast_keyboard(bot_links, worker_links)

        await context.bot.send_message(
            chat_id=chat_id, text=message, reply_markup=reply_markup
        )
        logger.info(f"自动播报已发送到群组 {chat_id}（带内联键盘）")
    except Exception as e:
        logger.error(f"自动播报失败: {e}", exc_info=True)
