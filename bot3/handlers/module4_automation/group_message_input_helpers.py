"""群组消息相关文本输入辅助函数"""

# 标准库
import logging
from typing import Optional, Tuple

# 第三方库
from telegram import Update
from telegram.ext import ContextTypes

# 本地模块
from services.module4_automation.group_message_service import \
    GroupMessageService

logger = logging.getLogger(__name__)


async def _handle_broadcast(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str
):
    """处理群发消息"""
    # 检查是否取消
    if text.lower().strip() == "cancel":
        context.user_data["state"] = None
        await update.message.reply_text("❌ 群发已取消")
        return

    locked_groups = context.user_data.get("locked_groups", [])
    if not locked_groups:
        await update.message.reply_text("⚠️ No locked groups")
        context.user_data["state"] = None
        return

    success_count = 0
    fail_count = 0

    await update.message.reply_text(
        f"⏳ Sending message to {len(locked_groups)} groups..."
    )

    for chat_id in locked_groups:
        try:
            await context.bot.send_message(chat_id=chat_id, text=text)
            success_count += 1
        except Exception as e:
            logger.error(f"群发失败 {chat_id}: {e}")
            fail_count += 1

    await update.message.reply_text(
        f"✅ Broadcast Completed\n"
        f"Success: {success_count}\n"
        f"Failed: {fail_count}"
    )
    context.user_data["state"] = None


def _extract_chat_id_from_context(context: ContextTypes.DEFAULT_TYPE) -> Optional[int]:
    """从上下文中提取chat_id

    Args:
        context: 上下文对象

    Returns:
        chat_id，如果无法提取则返回None
    """
    chat_id = context.user_data.get("setting_chat_id")
    if chat_id:
        return chat_id

    user_state = context.user_data.get("state", "")
    if user_state:
        try:
            parts = user_state.split("_")
            if len(parts) > 1:
                return int(parts[-1])
        except (ValueError, IndexError):
            pass

    return None


def _validate_and_process_links(text: str) -> Tuple[Optional[str], Optional[str]]:
    """验证并处理链接

    Args:
        text: 输入的文本

    Returns:
        (处理后的链接字符串, 错误消息)
    """
    if text.strip().lower() == "clear":
        return "", None

    links = [link.strip() for link in text.split("\n") if link.strip()]
    valid_links = []
    for link in links:
        if link.startswith("http://") or link.startswith("https://"):
            valid_links.append(link)
        else:
            return None, f"❌ 链接格式错误: {link}\n链接必须以 http:// 或 https:// 开头"

    return "\n".join(valid_links) if valid_links else "", None


async def _save_and_respond_bot_links(
    update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, bot_links: str
) -> None:
    """保存机器人链接并发送响应

    Args:
        update: Telegram更新对象
        context: 上下文对象
        chat_id: 群组ID
        bot_links: 链接字符串
    """
    success, error_msg = await GroupMessageService.save_config(
        chat_id=chat_id, bot_links=bot_links
    )

    if success:
        if bot_links:
            await update.message.reply_text(
                f"✅ 机器人链接已设置\n\n链接:\n{bot_links}"
            )
        else:
            await update.message.reply_text("✅ 机器人链接已清空")
    else:
        await update.message.reply_text(error_msg or "❌ 设置失败")


async def _save_and_respond_worker_links(
    update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, worker_links: str
) -> None:
    """保存人工链接并发送响应

    Args:
        update: Telegram更新对象
        context: 上下文对象
        chat_id: 群组ID
        worker_links: 链接字符串
    """
    success, error_msg = await GroupMessageService.save_config(
        chat_id=chat_id, worker_links=worker_links
    )

    if success:
        if worker_links:
            await update.message.reply_text(
                f"✅ 人工链接已设置\n\n链接:\n{worker_links}"
            )
        else:
            await update.message.reply_text("✅ 人工链接已清空")
    else:
        await update.message.reply_text(error_msg or "❌ 设置失败")


async def _handle_set_bot_links(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str
):
    """处理设置机器人链接"""
    if text.strip().lower() == "cancel":
        context.user_data["state"] = None
        context.user_data.pop("setting_chat_id", None)
        await update.message.reply_text("✅ 操作已取消")
        return

    chat_id = _extract_chat_id_from_context(context)
    if not chat_id:
        await update.message.reply_text("❌ 错误：无法获取群组ID")
        context.user_data["state"] = None
        return

    try:
        bot_links, error_msg = _validate_and_process_links(text)
        if bot_links is None:
            await update.message.reply_text(error_msg)
            return

        await _save_and_respond_bot_links(update, context, chat_id, bot_links)
    except Exception as e:
        logger.error(f"设置机器人链接失败: {e}", exc_info=True)
        await update.message.reply_text(f"❌ 设置失败: {e}")
    finally:
        context.user_data["state"] = None
        context.user_data.pop("setting_chat_id", None)


async def _handle_set_worker_links(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str
):
    """处理设置人工链接"""
    if text.strip().lower() == "cancel":
        context.user_data["state"] = None
        context.user_data.pop("setting_chat_id", None)
        await update.message.reply_text("✅ 操作已取消")
        return

    chat_id = _extract_chat_id_from_context(context)
    if not chat_id:
        await update.message.reply_text("❌ 错误：无法获取群组ID")
        context.user_data["state"] = None
        return

    try:
        worker_links, error_msg = _validate_and_process_links(text)
        if worker_links is None:
            await update.message.reply_text(error_msg)
            return

        await _save_and_respond_worker_links(update, context, chat_id, worker_links)
    except Exception as e:
        logger.error(f"设置人工链接失败: {e}", exc_info=True)
        await update.message.reply_text(f"❌ 设置失败: {e}")
    finally:
        context.user_data["state"] = None
        context.user_data.pop("setting_chat_id", None)
