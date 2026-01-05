"""群组消息回调处理器 - 精简版：只保留测试消息回调"""

import logging
import random

from telegram import Update
from telegram.ext import ContextTypes

import db_operations
from utils.callback_helpers import safe_edit_message_text
from utils.schedule_executor import (_combine_fixed_message_with_anti_fraud,
                                     _send_group_message,
                                     get_current_weekday_index,
                                     get_weekday_message)

logger = logging.getLogger(__name__)


async def handle_group_message_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """处理群组消息相关的回调 - 精简版：只处理测试消息"""
    query = update.callback_query
    if not query or not query.data:
        return

    data = query.data
    logger.info(f"处理群组消息回调: {data}")

    # 只处理测试消息回调
    if data.startswith("test_msg_"):
        try:
            await query.answer()
            chat = query.message.chat
            if chat.type == "private":
                await query.answer("❌ 此功能只能在群组中使用", show_alert=True)
                return

            msg_type_map = {
                "test_msg_start_work": "start_work",
                "test_msg_end_work": "end_work",
                "test_msg_promotion": "promotion",
            }

            msg_type = msg_type_map.get(data)
            if not msg_type:
                await query.answer("❌ 无效的消息类型", show_alert=True)
                return

            # 获取群组配置
            config = await db_operations.get_group_message_config_by_chat_id(chat.id)
            if not config:
                await query.answer(
                    "❌ 群组未配置，请先使用 /groupmsg_setup 开启", show_alert=True
                )
                return

            bot_links = config.get("bot_links")
            worker_links = config.get("worker_links")

            # 获取当前星期几索引（1-7）
            weekday_index = get_current_weekday_index()

            # 根据消息类型选择内容（从配置中按星期几读取）
            main_message = ""
            if msg_type == "start_work":
                main_message = get_weekday_message(
                    config, "start_work_message", weekday_index
                )
                if not main_message:
                    await query.answer(
                        f"❌ 开工消息（星期{weekday_index}）未配置", show_alert=True
                    )
                    return

            elif msg_type == "end_work":
                main_message = get_weekday_message(
                    config, "end_work_message", weekday_index
                )
                if not main_message:
                    await query.answer(
                        f"❌ 收工消息（星期{weekday_index}）未配置", show_alert=True
                    )
                    return

            elif msg_type == "promotion":
                # 宣传消息仍然从表随机选择
                messages = await db_operations.get_active_promotion_messages()
                valid_messages = [
                    m for m in messages if m.get("message") and m.get("message").strip()
                ]
                if not valid_messages:
                    await query.answer("❌ 没有有效的宣传消息", show_alert=True)
                    return
                main_message = random.choice(valid_messages).get("message", "").strip()

            if not main_message:
                await query.answer("❌ 消息内容为空", show_alert=True)
                return

            # 获取防诈骗文案（从配置中按星期几读取）
            anti_fraud = get_weekday_message(
                config, "anti_fraud_message", weekday_index
            )

            # 组合消息并发送
            if msg_type == "promotion":
                # 宣传消息使用固定防诈骗文案
                final_message = _combine_fixed_message_with_anti_fraud(
                    main_message, anti_fraud
                )
            else:
                # 开工、收工使用固定文案
                final_message = _combine_fixed_message_with_anti_fraud(
                    main_message, anti_fraud
                )

            bot = context.bot
            if await _send_group_message(
                bot, chat.id, final_message, bot_links, worker_links
            ):
                await safe_edit_message_text(
                    query, f"✅ 测试消息已发送（星期{weekday_index}）"
                )
            else:
                await query.answer("❌ 发送失败", show_alert=True)
        except Exception as e:
            logger.error(f"发送测试消息失败: {e}", exc_info=True)
            await query.answer(f"❌ 发送失败: {str(e)[:50]}", show_alert=True)
