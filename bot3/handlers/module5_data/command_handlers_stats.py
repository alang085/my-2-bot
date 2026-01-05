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
    all_group_ids = list(
        set(order.get("group_id") for order in all_orders if order.get("group_id"))
    )

    fixed_count = 0
    fixed_groups = []

    for group_id in sorted(all_group_ids):
        group_orders = [o for o in all_orders if o.get("group_id") == group_id]
        valid_orders = [
            o for o in group_orders if o.get("state") in ["normal", "overdue"]
        ]

        actual_valid_count = len(valid_orders)
        actual_valid_amount = sum(o.get("amount", 0) for o in valid_orders)

        grouped_data = await db_operations.get_grouped_data(group_id)

        valid_count_diff = actual_valid_count - grouped_data["valid_orders"]
        valid_amount_diff = actual_valid_amount - grouped_data["valid_amount"]

        if abs(valid_count_diff) > 0 or abs(valid_amount_diff) > 0.01:
            if valid_count_diff != 0:
                await db_operations.update_grouped_data(
                    group_id, "valid_orders", valid_count_diff
                )
            if abs(valid_amount_diff) > 0.01:
                await db_operations.update_grouped_data(
                    group_id, "valid_amount", valid_amount_diff
                )
            fixed_count += 1
            fixed_groups.append(
                f"{group_id} (订单数: {valid_count_diff}, 金额: {valid_amount_diff:,.2f})"
            )

    return fixed_count, fixed_groups


async def _fix_global_statistics(all_orders: List[Dict]) -> int:
    """修复全局统计数据

    Args:
        all_orders: 所有订单列表

    Returns:
        是否修复了全局统计
    """
    all_valid_orders = [
        o for o in all_orders if o.get("state") in ["normal", "overdue"]
    ]
    global_valid_count = len(all_valid_orders)
    global_valid_amount = sum(o.get("amount", 0) for o in all_valid_orders)

    financial_data = await db_operations.get_financial_data()
    global_valid_count_diff = global_valid_count - financial_data["valid_orders"]
    global_valid_amount_diff = global_valid_amount - financial_data["valid_amount"]

    if abs(global_valid_count_diff) > 0 or abs(global_valid_amount_diff) > 0.01:
        if global_valid_count_diff != 0:
            await db_operations.update_financial_data(
                "valid_orders", global_valid_count_diff
            )
        if abs(global_valid_amount_diff) > 0.01:
            await db_operations.update_financial_data(
                "valid_amount", global_valid_amount_diff
            )
        return 1
    return 0


def _build_fix_result_message(fixed_count: int, fixed_groups: List[str]) -> str:
    """构建修复结果消息

    Args:
        fixed_count: 修复数量
        fixed_groups: 修复的归属ID列表

    Returns:
        结果消息
    """
    if fixed_count > 0:
        result_msg = (
            f"✅ 统计数据修复完成！\n\n已修复 {fixed_count} 个归属ID的统计数据。"
        )
        if fixed_groups:
            result_msg += f"\n\n修复的归属ID:\n" + "\n".join(
                f"• {g}" for g in fixed_groups
            )
        return result_msg
    else:
        return "✅ 统计数据一致，无需修复。"


# 注意：fix_statistics 和 fix_income_statistics 处理函数已移动到 stats_handlers.py
# 此文件仅保留辅助函数实现，避免重复代码
