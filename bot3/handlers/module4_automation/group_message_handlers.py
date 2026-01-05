"""群组消息管理处理器 - 精简版：只保留核心命令"""

import logging
import random
from typing import Dict, Optional

from telegram import Update
from telegram.ext import ContextTypes

import db_operations
from decorators import admin_required, error_handler
from services.module4_automation.group_message_service import \
    GroupMessageService
from utils.schedule_executor import (_combine_fixed_message_with_anti_fraud,
                                     _send_group_message,
                                     get_current_weekday_index,
                                     get_weekday_message,
                                     send_start_work_messages)

logger = logging.getLogger(__name__)


@error_handler
@admin_required
async def get_group_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get current group/channel ID"""
    chat = update.effective_chat
    if chat.type == "private":
        await update.message.reply_text(
            "❌ This command can only be used in groups or channels"
        )
        return

    chat_type = "Channel" if chat.type == "channel" else "Group"
    await update.message.reply_text(
        f"📌 {chat_type} Info\n\n"
        f"{chat_type} Name: {chat.title}\n"
        f"{chat_type} ID: `{chat.id}`\n\n"
        f"Use /groupmsg_setup to enable automatic messages",
        parse_mode="Markdown",
    )


@error_handler
@admin_required
async def setup_group_auto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Enable automatic group/channel messages"""
    chat = update.effective_chat
    if not chat or chat.type == "private":
        await update.message.reply_text(
            "❌ This command can only be used in groups or channels"
        )
        return

    chat_type = "Channel" if chat.type == "channel" else "Group"
    chat_title = chat.title or "Unknown"
    success, error_msg = await GroupMessageService.setup_group_auto(chat.id, chat_title)
    if success:
        await update.message.reply_text(
            f"✅ {chat_type} automatic messages enabled!\n\n"
            f"Default weekly messages have been configured.\n"
            f"Use /test_group_message to test sending messages."
        )
    else:
        await update.message.reply_text(f"❌ Failed: {error_msg}")


@error_handler
@admin_required
async def test_group_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Test sending group message (default: start_work)"""
    chat = update.effective_chat
    if not chat or chat.type == "private":
        await update.message.reply_text(
            "❌ This command can only be used in groups or channels"
        )
        return

    # 解析消息类型参数（默认为 start_work）
    msg_type = "start_work"
    if context.args:
        msg_type = context.args[0].lower()

    await _send_test_message(update, context, chat, msg_type)


@error_handler
@admin_required
async def test_weekday_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """显示当前星期几对应的文案配置"""
    chat = update.effective_chat
    if not chat or chat.type == "private":
        await update.message.reply_text(
            "❌ This command can only be used in groups or channels"
        )
        return

    config = await db_operations.get_group_message_config_by_chat_id(chat.id)
    if not config:
        await update.message.reply_text("❌ 群组未配置，请先使用 /groupmsg_setup 开启")
        return

    weekday_index = get_current_weekday_index()
    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    weekday_name = weekday_names[weekday_index - 1]

    start_work = get_weekday_message(config, "start_work_message", weekday_index)
    end_work = get_weekday_message(config, "end_work_message", weekday_index)
    welcome = get_weekday_message(config, "welcome_message", weekday_index)
    anti_fraud = get_weekday_message(config, "anti_fraud_message", weekday_index)

    response = f"📅 当前是{weekday_name}（星期{weekday_index}）\n\n"
    response += (
        f"🌅 开工消息:\n{start_work[:100]}{'...' if len(start_work) > 100 else ''}\n\n"
    )
    response += (
        f"🌙 收工消息:\n{end_work[:100]}{'...' if len(end_work) > 100 else ''}\n\n"
    )
    response += (
        f"👋 欢迎消息:\n{welcome[:100]}{'...' if len(welcome) > 100 else ''}\n\n"
    )
    response += (
        f"⚠️ 防诈骗消息:\n{anti_fraud[:100]}{'...' if len(anti_fraud) > 100 else ''}\n\n"
    )
    response += f"💡 使用 /test_group_message start_work 测试发送消息"

    await update.message.reply_text(response)


@error_handler
@admin_required
def _format_links_info(bot_links: Optional[str], worker_links: Optional[str]) -> str:
    """格式化链接信息

    Args:
        bot_links: 机器人链接
        worker_links: 客服链接

    Returns:
        链接信息文本
    """
    links_info = ""
    if bot_links:
        if len(bot_links) > 30:
            links_info += f"🤖 机器人链接: {bot_links[:30]}...\n"
        else:
            links_info += f"🤖 机器人链接: {bot_links}\n"
    if worker_links:
        if len(worker_links) > 30:
            links_info += f"👤 客服链接: {worker_links[:30]}...\n"
        else:
            links_info += f"👤 客服链接: {worker_links}\n"
    return links_info


def _get_message_types_info(config: Dict) -> str:
    """获取消息类型信息

    Args:
        config: 群组配置

    Returns:
        消息类型信息文本
    """
    has_start = bool(config.get("start_work_message_1"))
    has_end = bool(config.get("end_work_message_1"))
    has_welcome = bool(config.get("welcome_message_1"))
    has_anti_fraud = bool(config.get("anti_fraud_message_1"))

    msg_types = []
    if has_start:
        msg_types.append("开工")
    if has_end:
        msg_types.append("收工")
    if has_welcome:
        msg_types.append("欢迎")
    if has_anti_fraud:
        msg_types.append("防诈骗")

    return "、".join(msg_types) if msg_types else "未配置"


def _build_config_item_text(i: int, config: Dict) -> str:
    """构建单个配置项文本

    Args:
        i: 序号
        config: 群组配置

    Returns:
        配置项文本
    """
    chat_id = config.get("chat_id")
    chat_title = config.get("chat_title") or "未命名"
    is_active = config.get("is_active", 0)
    bot_links = config.get("bot_links")
    worker_links = config.get("worker_links")

    status = "✅ 已启用" if is_active else "❌ 已禁用"
    links_info = _format_links_info(bot_links, worker_links)
    msg_info = _get_message_types_info(config)

    item_text = f"{i}. {chat_title}\n"
    item_text += f"   ID: {chat_id}\n"
    item_text += f"   状态: {status}\n"
    item_text += f"   消息类型: {msg_info}\n"
    if links_info:
        item_text += f"   {links_info}"
    item_text += "\n"

    return item_text


async def list_group_message_configs(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """列出所有已开启群组自动消息的群组"""
    try:
        configs = await db_operations.get_group_message_configs()
        if not configs:
            await update.message.reply_text("❌ 没有已配置的群组")
            return

        response = f"📋 已配置的群组 ({len(configs)} 个):\n\n"
        for i, config in enumerate(configs, 1):
            response += _build_config_item_text(i, config)

        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"列出群组配置失败: {e}", exc_info=True)
        await update.message.reply_text(f"❌ 列出失败: {e}")


@error_handler
@admin_required
async def send_start_work_messages_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """手动触发发送开工消息到所有配置的群组"""
    try:
        await update.message.reply_text("⏳ 正在发送开工消息...")
        bot = context.bot
        await send_start_work_messages(bot)
        await update.message.reply_text("✅ 开工消息发送完成！")
    except Exception as e:
        logger.error(f"手动触发发送开工消息失败: {e}", exc_info=True)
        await update.message.reply_text(f"❌ 发送失败: {str(e)}")


async def _get_test_message_content(
    config: Dict, msg_type: str, weekday_index: int
) -> Optional[str]:
    """获取测试消息内容

    Args:
        config: 群组配置
        msg_type: 消息类型
        weekday_index: 星期索引

    Returns:
        消息内容，如果类型无效则返回None
    """
    if msg_type in ["start", "start_work"]:
        main_message = get_weekday_message(config, "start_work_message", weekday_index)
        return main_message or f"测试开工消息（星期{weekday_index}未配置）"

    elif msg_type in ["end", "end_work"]:
        main_message = get_weekday_message(config, "end_work_message", weekday_index)
        return main_message or f"测试收工消息（星期{weekday_index}未配置）"

    elif msg_type == "promotion":
        messages = await db_operations.get_active_promotion_messages()
        valid_messages = [
            m for m in messages if m.get("message") and m.get("message").strip()
        ]
        if valid_messages:
            return random.choice(valid_messages).get("message", "").strip()
        return "Best Service for you!"

    return None


async def _send_test_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE, chat, msg_type: str
) -> None:
    """内部函数：发送测试消息"""
    config = await db_operations.get_group_message_config_by_chat_id(chat.id)
    if not config:
        await update.message.reply_text("❌ 群组未配置，请先使用 /groupmsg_setup 开启")
        return

    weekday_index = get_current_weekday_index()
    main_message = await _get_test_message_content(config, msg_type, weekday_index)

    if main_message is None:
        await update.message.reply_text(
            "❌ Invalid message type. Use: start_work, end_work, promotion"
        )
        return

    if not main_message:
        await update.message.reply_text("❌ Message content is empty")
        return

    bot_links = config.get("bot_links") or None
    worker_links = config.get("worker_links") or None
    anti_fraud = get_weekday_message(config, "anti_fraud_message", weekday_index)
    final_message = _combine_fixed_message_with_anti_fraud(main_message, anti_fraud)

    logger.info(f"_send_test_message: 准备发送消息，长度: {len(final_message)}")
    try:
        success = await _send_group_message(
            context.bot, chat.id, final_message, bot_links, worker_links
        )
        if success:
            logger.info(f"_send_test_message: 消息发送成功")
            await update.message.reply_text(
                f"✅ Test message sent (星期{weekday_index})"
            )
        else:
            logger.warning(f"_send_test_message: 消息发送失败")
            await update.message.reply_text("❌ Send failed")
    except Exception as e:
        logger.error(f"_send_test_message: 发送消息时出错: {e}", exc_info=True)
        await update.message.reply_text(f"❌ 发送失败: {str(e)}")
