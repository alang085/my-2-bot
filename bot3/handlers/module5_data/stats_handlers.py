"""统计修复命令处理器"""

import logging
from typing import Dict, List, Tuple

from telegram import Update
from telegram.ext import ContextTypes

import db_operations
from decorators import admin_required, error_handler, private_chat_only
from services.module5_data.stats_service import StatsService

logger = logging.getLogger(__name__)


@error_handler
@admin_required
@private_chat_only
async def _fix_group_statistics(all_orders: List[Dict]) -> Tuple[int, List[str]]:
    """修复归属ID统计数据

    Args:
        all_orders: 所有订单列表

    Returns:
        (修复数量, 修复的归属ID列表)
    """
    from handlers.module5_data.command_handlers_stats import \
        _fix_group_statistics

    return await _fix_group_statistics(all_orders)


async def _fix_global_statistics(all_orders: List[Dict]) -> int:
    """修复全局统计数据

    Args:
        all_orders: 所有订单列表

    Returns:
        是否修复了全局统计
    """
    from handlers.module5_data.command_handlers_stats import \
        _fix_global_statistics

    return await _fix_global_statistics(all_orders)


def _build_fix_result_message(fixed_count: int, fixed_groups: List[str]) -> str:
    """构建修复结果消息

    Args:
        fixed_count: 修复数量
        fixed_groups: 修复的归属ID列表

    Returns:
        结果消息
    """
    from handlers.module5_data.command_handlers_stats import \
        _build_fix_result_message

    return _build_fix_result_message(fixed_count, fixed_groups)


async def fix_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """修复统计数据：根据实际订单数据重新计算所有统计数据（管理员命令）"""
    msg = await update.message.reply_text("🔄 开始修复统计数据...")

    all_orders = await db_operations.search_orders_advanced_all_states({})

    fixed_count, fixed_groups = await _fix_group_statistics(all_orders)
    fixed_count += await _fix_global_statistics(all_orders)

    result_msg = _build_fix_result_message(fixed_count, fixed_groups)
    await msg.edit_text(result_msg)


@error_handler
@admin_required
@private_chat_only
async def fix_income_statistics(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """修复收入统计数据：根据收入明细重新计算所有收入统计数据（管理员命令）"""
    from handlers.module5_data.stats_fix_helpers_calculate import \
        calculate_income_summary_from_records
    from handlers.module5_data.stats_fix_helpers_daily import \
        fix_daily_statistics
    from handlers.module5_data.stats_fix_helpers_global import \
        fix_global_statistics
    from handlers.module5_data.stats_fix_helpers_message import \
        build_fix_result_message

    msg = await update.message.reply_text("🔄 开始修复收入统计数据...")

    # 获取所有收入明细
    income_records = await db_operations.get_income_records("1970-01-01", "2099-12-31")

    # 计算收入明细汇总
    calculation_result = calculate_income_summary_from_records(income_records)
    income_summary = calculation_result["income_summary"]
    daily_income = calculation_result["daily_income"]

    # 获取当前统计数据
    financial_data = await db_operations.get_financial_data()
    await db_operations.get_stats_by_date_range("1970-01-01", "2099-12-31", None)

    # 修复全局统计数据
    fixed_items = await fix_global_statistics(income_summary, financial_data)

    # 修复日结统计数据
    daily_fixed_count = await fix_daily_statistics(daily_income)

    # 构建并发送结果消息
    result_msg = build_fix_result_message(
        fixed_items, daily_fixed_count, income_summary
    )
    await msg.edit_text(result_msg)
