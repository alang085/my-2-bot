"""基础命令处理器"""

import logging
from typing import Any, Dict, List, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

import db_operations  # 使用向后兼容的包装层
from decorators import (admin_required, authorized_required, error_handler,
                        private_chat_only)

logger = logging.getLogger(__name__)


@error_handler
async def check_permission(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """检查当前用户的权限状态（所有人可用）"""
    from utils.handler_helpers import check_user_permissions, get_user_info

    user_id, username, first_name = get_user_info(update)
    if not user_id:
        await update.message.reply_text("❌ 无法获取用户信息")
        return

    username = username or "无"
    first_name = first_name or "无"

    # 检查是否为管理员和授权用户
    is_admin, is_authorized, _ = await check_user_permissions(user_id)

    # 获取用户可访问的归属ID
    user_group_ids = await db_operations.get_user_group_ids(user_id)

    # 构建权限信息
    permission_info = []
    permission_info.append("👤 用户信息:")
    permission_info.append(f"  ID: {user_id}")
    permission_info.append(f"  用户名: @{username}")
    permission_info.append(f"  姓名: {first_name}")
    permission_info.append("")
    permission_info.append("🔐 权限状态:")

    if is_admin:
        permission_info.append("  ✅ 管理员")
    else:
        permission_info.append("  ❌ 非管理员")

    if is_authorized:
        permission_info.append("  ✅ 授权用户")
    else:
        permission_info.append("  ❌ 未授权用户")

    if user_group_ids:
        permission_info.append("")
        permission_info.append("📋 可访问的归属ID:")
        for group_id in user_group_ids:
            permission_info.append(f"  - {group_id}")
    else:
        permission_info.append("")
        permission_info.append("📋 可访问的归属ID: 无")

    # 发送权限信息
    message = "\n".join(permission_info)
    await update.message.reply_text(message)


@error_handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """发送欢迎消息和命令帮助（优化版：使用内联键盘分页）"""
    from handlers.command_start_group import handle_start_group
    from handlers.command_start_private import handle_start_private
    from utils.handler_helpers import get_user_id

    financial_data = await db_operations.get_financial_data()
    user_id = get_user_id(update)

    # 根据聊天类型处理
    if update.effective_chat.type != "private":
        await handle_start_group(update, context, financial_data, user_id)
    else:
        await handle_start_private(update, context, financial_data, user_id)


@error_handler
@authorized_required
@private_chat_only
def _calculate_valid_amount_statistics(
    all_orders: List[Dict],
) -> Tuple[List[Dict], float]:
    """计算有效金额统计

    Args:
        all_orders: 所有订单列表

    Returns:
        (有效订单列表, 实际有效金额)
    """
    valid_orders = [o for o in all_orders if o.get("state") in ["normal", "overdue"]]
    actual_valid_amount = sum(order.get("amount", 0) for order in valid_orders)
    return valid_orders, actual_valid_amount


def _build_group_statistics(valid_orders: List[Dict]) -> Dict[str, Dict[str, Any]]:
    """构建按归属ID分组的统计

    Args:
        valid_orders: 有效订单列表

    Returns:
        分组统计字典
    """
    group_stats = {}
    for order in valid_orders:
        group_id = order.get("group_id") or "未分配"
        if group_id not in group_stats:
            group_stats[group_id] = {"count": 0, "amount": 0.0}
        group_stats[group_id]["count"] += 1
        group_stats[group_id]["amount"] += order.get("amount", 0)
    return group_stats


def _build_valid_amount_message(
    valid_orders: List[Dict],
    actual_valid_amount: float,
    stats_valid_amount: float,
    group_stats: Dict[str, Dict[str, Any]],
) -> str:
    """构建有效金额统计消息

    Args:
        valid_orders: 有效订单列表
        actual_valid_amount: 实际有效金额
        stats_valid_amount: 统计有效金额
        group_stats: 分组统计

    Returns:
        消息文本
    """
    msg = "💰 有效金额统计\n\n"
    msg += f"📊 总体统计：\n"
    msg += f"有效订单数: {len(valid_orders)}\n"
    msg += f"实际有效金额: {actual_valid_amount:,.2f}\n"
    msg += f"统计有效金额: {stats_valid_amount:,.2f}\n"

    diff = stats_valid_amount - actual_valid_amount
    if abs(diff) > 0.01:
        msg += f"⚠️ 差异: {diff:+,.2f}\n"
    else:
        msg += f"✅ 数据一致\n"

    msg += f"\n📋 按归属ID分组：\n"
    sorted_groups = sorted(
        group_stats.items(), key=lambda x: x[1]["amount"], reverse=True
    )

    for group_id, stats in sorted_groups:
        msg += f"{group_id}: {stats['count']} 单, {stats['amount']:,.2f}\n"

    return msg


async def show_valid_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """显示有效金额统计"""
    try:
        all_orders = await db_operations.search_orders_advanced_all_states({})
        valid_orders, actual_valid_amount = _calculate_valid_amount_statistics(
            all_orders
        )

        financial_data = await db_operations.get_financial_data()
        stats_valid_amount = financial_data.get("valid_amount", 0.0)

        group_stats = _build_group_statistics(valid_orders)
        msg = _build_valid_amount_message(
            valid_orders, actual_valid_amount, stats_valid_amount, group_stats
        )

        await update.message.reply_text(msg)

    except Exception as e:
        logger.error(f"统计有效金额失败: {e}", exc_info=True)
        await update.message.reply_text(f"❌ 统计失败: {str(e)}")
