"""消息发送辅助函数

包含统一的消息发送函数，提取重复的消息发送模式。

规则：
- 群组：所有消息必须使用英文（English only）
- 私聊：所有消息必须使用中文（Chinese only）
"""

from telegram import Update


async def send_bilingual_message(
    update: Update, english_message: str, chinese_message: str
) -> None:
    """发送消息（根据聊天类型选择语言）

    规则：
    - 群组：使用英文消息（English only）
    - 私聊：使用中文消息（Chinese only）

    Args:
        update: Telegram 更新对象
        english_message: 英文消息（用于群组）
        chinese_message: 中文消息（用于私聊）
    """
    from utils.chat_helpers import is_group_chat

    if is_group_chat(update):
        # 群组：必须使用英文
        await update.message.reply_text(english_message)
    else:
        # 私聊：必须使用中文
        await update.message.reply_text(chinese_message)


async def send_success_message(
    update: Update, english_text: str, chinese_text: str
) -> None:
    """发送成功消息

    规则：
    - 群组：使用英文（English only）
    - 私聊：使用中文（Chinese only）

    Args:
        update: Telegram 更新对象
        english_text: 英文成功消息（群组使用）
        chinese_text: 中文成功消息（私聊使用）
    """
    await send_bilingual_message(update, english_text, chinese_text)


async def send_error_message(
    update: Update, english_text: str, chinese_text: str
) -> None:
    """发送错误消息

    规则：
    - 群组：使用英文（English only）
    - 私聊：使用中文（Chinese only）

    Args:
        update: Telegram 更新对象
        english_text: 英文错误消息（群组使用）
        chinese_text: 中文错误消息（私聊使用）
    """
    await send_bilingual_message(update, english_text, chinese_text)


async def display_search_results_helper(
    update: Update, context, orders: list
) -> None:
    """显示搜索结果辅助函数

    Args:
        update: Telegram 更新对象
        context: 上下文对象
        orders: 订单列表
    """
    from handlers.module4_automation.search_result import (
        _build_search_result_keyboard,
        _build_search_result_message,
        _calculate_search_statistics,
    )

    if not orders:
        await send_bilingual_message(
            update,
            "❌ No matching orders found",
            "❌ 未找到匹配的订单",
        )
        context.user_data["state"] = None
        return

    order_count, total_amount, locked_groups = _calculate_search_statistics(orders)
    context.user_data["locked_groups"] = locked_groups
    context.user_data["report_search_orders"] = orders

    result_msg = _build_search_result_message(
        order_count, total_amount, len(locked_groups)
    )
    reply_markup = _build_search_result_keyboard()

    await update.message.reply_text(result_msg, reply_markup=reply_markup)
    context.user_data["state"] = None
