"""归属管理命令处理器"""

import logging
from typing import Tuple

from telegram import Update
from telegram.ext import ContextTypes

from db.module2_finance.finance import (get_all_group_ids, get_grouped_data,
                                        update_grouped_data)
from decorators import error_handler
from utils.stats_helpers import update_all_stats

logger = logging.getLogger(__name__)


@error_handler
async def create_attribution(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """创建新的归属ID"""
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ 用法: /create_attribution <归属ID>\n示例: /create_attribution S03"
        )
        return

    group_id = context.args[0].upper()

    # 验证格式
    if len(group_id) != 3 or not group_id[0].isalpha() or not group_id[1:].isdigit():
        await update.message.reply_text("❌ 格式错误，正确格式：字母+两位数字（如S01）")
        return

    # 检查是否已存在
    existing_groups = await get_all_group_ids()
    if group_id in existing_groups:
        await update.message.reply_text(f"⚠️ 归属ID {group_id} 已存在")
        return

    # 创建分组数据记录
    await update_grouped_data(group_id, "valid_orders", 0)
    await update.message.reply_text(f"✅ 成功创建归属ID {group_id}")


@error_handler
async def list_attributions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """列出所有归属ID"""
    group_ids = await get_all_group_ids()

    if not group_ids:
        await update.message.reply_text(
            "暂无归属ID，使用 /create_attribution <ID> 创建"
        )
        return

    message = "📋 所有归属ID:\n\n"
    for i, group_id in enumerate(sorted(group_ids), 1):
        data = await get_grouped_data(group_id)
        message += (
            f"{i}. {group_id}\n"
            f"   有效订单: {data['valid_orders']} | "
            f"金额: {data['valid_amount']:.2f}\n"
        )

    await update.message.reply_text(message)


async def change_orders_attribution(
    update: Update, context: ContextTypes.DEFAULT_TYPE, orders: list, new_group_id: str
) -> Tuple[int, int]:
    """
    批量修改订单归属

    Args:
        update: Telegram Update对象
        context: Context对象
        orders: 订单列表
        new_group_id: 新的归属ID

    Returns:
        (success_count, fail_count): 成功和失败的数量
    """
    from handlers.module1_user.attribution_migrate import migrate_statistics
    from handlers.module1_user.attribution_update import \
        update_order_attribution

    # 更新订单归属并统计迁移数据
    success_count, fail_count, old_group_stats = await update_order_attribution(
        orders, new_group_id
    )

    # 迁移统计数据
    summary = await migrate_statistics(old_group_stats, new_group_id)

    logger.info(
        f"归属变更完成: {success_count} 成功, {fail_count} 失败, "
        f"迁移到 {new_group_id}: 有效订单 {summary['valid_count']} 个 ({summary['valid_amount']:.2f}), "
        f"违约订单 {summary['breach_count']} 个 ({summary['breach_amount']:.2f})"
    )

    return success_count, fail_count
