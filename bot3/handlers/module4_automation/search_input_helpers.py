"""搜索相关文本输入辅助函数"""

# 标准库
import logging
from typing import Optional

# 第三方库
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

# 本地模块
import db_operations
from utils.amount_helpers import (distribute_orders_evenly_by_weekday,
                                  parse_amount)
from utils.error_messages import ErrorMessages
from utils.message_helpers import display_search_results_helper

logger = logging.getLogger(__name__)


def _clear_user_state(context: ContextTypes.DEFAULT_TYPE):
    """清除用户状态"""
    context.user_data["state"] = None


def _parse_key_value_search(text: str, criteria: dict) -> None:
    """解析key=value格式的搜索条件"""
    parts = text.split()
    for part in parts:
        if "=" in part:
            key, value = part.split("=", 1)
            key = key.strip().lower()
            value = value.strip()

            if key == "group":
                key = "weekday_group"
                if value.startswith("周") and len(value) == 2:
                    value = value[1]

            if key in ["group_id", "state", "customer", "order_id", "weekday_group"]:
                criteria[key] = value


def _parse_simple_search(text: str, criteria: dict) -> None:
    """解析简单文本搜索条件"""
    val = text.strip()
    if val in ["一", "二", "三", "四", "五", "六", "日"]:
        criteria["weekday_group"] = val
    elif (
        val.startswith("周")
        and len(val) == 2
        and val[1] in ["一", "二", "三", "四", "五", "六", "日"]
    ):
        criteria["weekday_group"] = val[1]
    elif val.upper() in ["A", "B"]:
        criteria["customer"] = val.upper()
    elif val in [
        "normal",
        "overdue",
        "breach",
        "end",
        "breach_end",
        "正常",
        "逾期",
        "违约",
        "完成",
        "违约完成",
    ]:
        state_map = {
            "正常": "normal",
            "逾期": "overdue",
            "违约": "breach",
            "完成": "end",
            "违约完成": "breach_end",
        }
        criteria["state"] = state_map.get(val, val)
    elif len(val) == 3 and val[0].isalpha() and val[1:].isdigit():
        from utils.validation_helpers import validate_group_id

        is_valid, validated_group_id, _ = validate_group_id(val)
        if is_valid:
            criteria["group_id"] = validated_group_id
    else:
        criteria["order_id"] = val


async def _parse_search_criteria(text: str, criteria: dict) -> bool:
    """解析搜索条件，返回是否成功"""
    if "=" in text:
        _parse_key_value_search(text, criteria)
    else:
        _parse_simple_search(text, criteria)
    return bool(criteria)


async def _handle_search_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str
):
    """处理搜索输入"""
    criteria = {}
    try:
        if not await _parse_search_criteria(text, criteria):
            await update.message.reply_text(
                "❌ 无法识别搜索条件\n\n"
                "支持的格式：\n"
                "• 订单ID（如：0001）\n"
                "• 归属ID（如：S01）\n"
                "• 客户类型（A 或 B）\n"
                "• 订单状态（正常、逾期、违约、完成、违约完成）\n"
                "• 星期分组（一、二、三、四、五、六、日）\n"
                "• key=value 格式（如：group_id=S01）"
            )
            _clear_user_state(context)
            return

        orders = await db_operations.search_orders_advanced(criteria)

        if not orders:
            await update.message.reply_text("❌ 未找到匹配的订单")
            _clear_user_state(context)
            return

        locked_groups = list(set(order["chat_id"] for order in orders))
        context.user_data["locked_groups"] = locked_groups

        await update.message.reply_text(
            f"✅ Found {len(orders)} orders in {len(locked_groups)} groups.\n"
            f"Groups locked. You can now use 【Broadcast】 feature.\n"
            f"Enter 'cancel' to exit search mode (locks retained)."
        )
        context.user_data["state"] = None

    except Exception as e:
        logger.error(f"搜索出错: {e}", exc_info=True)
        await update.message.reply_text(f"⚠️ 搜索出错: {str(e)[:200]}")
        _clear_user_state(context)


async def _process_search_amount_orders(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    target_amount: float,
    processing_msg,
) -> Optional[list]:
    """处理金额搜索的订单获取和分配

    Returns:
        选中的订单列表，如果失败则返回None
    """
    from handlers.module4_automation.search_amount_distribute import \
        distribute_orders_safely
    from handlers.module4_automation.search_amount_fetch import \
        fetch_and_validate_orders

    result = await fetch_and_validate_orders(
        update, context, processing_msg, target_amount
    )
    if result is None:
        return None

    all_valid_orders, total_valid_amount = result
    selected_orders = await distribute_orders_safely(
        update, context, processing_msg, all_valid_orders, target_amount
    )

    return selected_orders


async def _display_search_amount_results(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    selected_orders: list,
    target_amount: float,
) -> None:
    """显示金额搜索结果"""
    from handlers.module4_automation.search_amount_stats import (
        build_result_message, calculate_weekday_stats)

    selected_amount = sum(order.get("amount", 0) for order in selected_orders)
    selected_count = len(selected_orders)
    weekday_stats = calculate_weekday_stats(selected_orders)
    daily_target = target_amount / 7

    result_msg = build_result_message(
        target_amount, selected_amount, selected_count, weekday_stats, daily_target
    )
    await update.message.reply_text(result_msg)

    try:
        await display_search_results_helper(update, context, selected_orders)
    except Exception as e:
        logger.error(f"显示搜索结果时出错: {e}", exc_info=True)
        await update.message.reply_text(f"⚠️ 显示结果时出错: {e}")


async def _handle_search_amount_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str
):
    """处理按总有效金额查找输入"""
    from handlers.module4_automation.search_amount_parse import \
        parse_and_validate_amount

    try:
        target_amount = await parse_and_validate_amount(update, context, text)
        if target_amount is None:
            return

        processing_msg = await update.message.reply_text("⏳ 正在查找订单，请稍候...")

        selected_orders = await _process_search_amount_orders(
            update, context, target_amount, processing_msg
        )
        if selected_orders is None:
            return

        try:
            await processing_msg.delete()
        except Exception:
            pass

        await _display_search_amount_results(
            update, context, selected_orders, target_amount
        )
        context.user_data["state"] = None

    except Exception as e:
        logger.error(f"按金额查找出错: {e}", exc_info=True)
        await update.message.reply_text(f"⚠️ 查找出错: {e}")
        context.user_data["state"] = None


async def _handle_report_search(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str
):
    """处理报表查找输入"""
    from handlers.module4_automation.search_parse import parse_search_criteria
    from handlers.module4_automation.search_result import \
        display_search_results

    try:
        # 解析搜索条件
        criteria = parse_search_criteria(text)

        if not criteria:
            await update.message.reply_text(
                "❌ 无法识别查询条件\n\n示例：\n• S01\n• 三 正常\n• S01 正常"
            )
            return

        # 显示搜索结果
        await display_search_results(update, context, criteria)

    except Exception as e:
        logger.error(f"报表查找出错: {e}", exc_info=True)
        await update.message.reply_text(f"⚠️ 查找出错: {e}")
        context.user_data["state"] = None
