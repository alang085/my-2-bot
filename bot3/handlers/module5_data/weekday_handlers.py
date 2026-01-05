"""星期分组命令处理器"""

import logging
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

import db_operations
from decorators import admin_required, error_handler, private_chat_only
from utils.chat_helpers import get_weekday_group_from_date

logger = logging.getLogger(__name__)


def _parse_order_date_from_fields(order_date_str: str, order_id: str):
    """从订单日期字符串或订单ID解析日期

    Args:
        order_date_str: 订单日期字符串
        order_id: 订单ID

    Returns:
        解析的日期，如果无法解析则返回None
    """
    from handlers.module5_data.date_parse_helpers import \
        parse_order_date_from_fields

    return parse_order_date_from_fields(order_date_str, order_id)


def _check_order_weekday_group(order, incorrect_orders: list) -> bool:
    """检查单个订单的星期分组是否正确，返回是否跳过了该订单"""
    order_id = order["order_id"]
    chat_id = order["chat_id"]
    order_date_str = order.get("date", "")
    current_weekday_group = order.get("weekday_group", "")

    if not order_date_str:
        return True

    order_date = _parse_order_date_from_fields(order_date_str, order_id)
    if not order_date:
        return True

    correct_weekday_group = get_weekday_group_from_date(order_date)
    if current_weekday_group != correct_weekday_group:
        incorrect_orders.append(
            {
                "order_id": order_id,
                "chat_id": chat_id,
                "date": order_date_str,
                "current": current_weekday_group or "未设置",
                "correct": correct_weekday_group,
            }
        )
    return False


def _build_check_result_message(
    incorrect_orders: list, skipped_count: int, total_count: int
) -> str:
    """构建检查结果消息"""
    if not incorrect_orders:
        return (
            "✅ 检查完成！\n\n"
            f"所有订单的星期分组都正确\n"
            f"跳过: {skipped_count} 个订单（无法解析日期）\n"
            f"总计: {total_count} 个订单"
        )

    result_msg = (
        f"⚠️ 发现 {len(incorrect_orders)} 个订单的星期分组不正确\n\n"
        f"跳过: {skipped_count} 个订单（无法解析日期）\n"
        f"总计: {total_count} 个订单\n\n"
        "前20个不正确的订单：\n"
    )

    for idx, order_info in enumerate(incorrect_orders[:20], 1):
        result_msg += (
            f"{idx}. {order_info['order_id']} | "
            f"日期: {order_info['date']} | "
            f"当前: {order_info['current']} → 正确: {order_info['correct']}\n"
        )

    if len(incorrect_orders) > 20:
        result_msg += f"\n... 还有 {len(incorrect_orders) - 20} 个订单需要修复\n"

    result_msg += "\n💡 使用 /update_weekday_groups 修复这些问题"
    return result_msg


@error_handler
@admin_required
@private_chat_only
async def check_weekday_groups(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """检查所有订单的星期分组是否正确（诊断命令）"""
    msg = await update.message.reply_text("🔍 正在检查订单星期分组...")

    all_orders = await db_operations.search_orders_advanced_all_states({})

    if not all_orders:
        await msg.edit_text("❌ 没有找到订单")
        return

    incorrect_orders = []
    skipped_count = 0

    for order in all_orders:
        if _check_order_weekday_group(order, incorrect_orders):
            skipped_count += 1

    result_msg = _build_check_result_message(
        incorrect_orders, skipped_count, len(all_orders)
    )
    await msg.edit_text(result_msg)


@error_handler
@admin_required
@private_chat_only
async def _process_single_order_weekday_update(order: dict, counters: dict) -> None:
    """处理单个订单的星期分组更新

    Args:
        order: 订单字典
        counters: 计数器字典（会被修改）
    """
    from handlers.module5_data.weekday_parse import parse_order_date
    from handlers.module5_data.weekday_update import \
        update_order_weekday_group_if_needed
    from utils.weekday_helpers import get_weekday_group_from_date

    order_id = order["order_id"]
    order_date_str = order.get("date", "")
    current_weekday_group = order.get("weekday_group", "")

    try:
        order_date = parse_order_date(order_date_str, order_id)
        if not order_date:
            counters["skipped_count"] += 1
            return

        correct_weekday_group = get_weekday_group_from_date(order_date)
        if current_weekday_group == correct_weekday_group:
            counters["no_change_count"] += 1
            return

        updated, verification_failed, update_failed = (
            await update_order_weekday_group_if_needed(
                order, order_date, correct_weekday_group
            )
        )

        if updated:
            counters["updated_count"] += 1
        elif verification_failed:
            counters["verification_failed_count"] += 1
        elif update_failed:
            counters["error_count"] += 1

    except Exception as e:
        counters["error_count"] += 1
        logger.warning(f"处理订单 {order_id} 时出错: {e}")


def _build_weekday_update_result_message(counters: dict, total_orders: int) -> str:
    """构建星期分组更新结果消息

    Args:
        counters: 计数器字典
        total_orders: 总订单数

    Returns:
        结果消息文本
    """
    return (
        "✅ 更新完成！\n\n"
        f"已更新: {counters['updated_count']} 个订单（值已改变）\n"
        f"无需更新: {counters['no_change_count']} 个订单（值正确）\n"
        f"跳过: {counters['skipped_count']} 个订单（无法解析日期）\n"
        f"验证失败: {counters['verification_failed_count']} 个订单\n"
        f"错误: {counters['error_count']} 个订单\n"
        f"总计: {total_orders} 个订单"
    )


async def update_weekday_groups(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """更新所有订单的星期分组（管理员命令）"""
    msg = await update.message.reply_text("🔄 开始更新所有订单的星期分组...")

    all_orders = await db_operations.search_orders_advanced_all_states({})

    if not all_orders:
        await msg.edit_text("❌ 没有找到订单")
        return

    counters = {
        "updated_count": 0,
        "no_change_count": 0,
        "error_count": 0,
        "skipped_count": 0,
        "verification_failed_count": 0,
    }

    for order in all_orders:
        await _process_single_order_weekday_update(order, counters)

    result_msg = _build_weekday_update_result_message(counters, len(all_orders))
    await msg.edit_text(result_msg)
