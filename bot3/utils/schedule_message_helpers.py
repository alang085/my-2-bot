"""定时任务消息辅助函数

包含消息格式化、键盘创建、管理员提及等辅助函数。
"""

# 标准库
import logging
import random
from typing import List, Optional

# 第三方库
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)

# 缓存管理员用户名（只提取一次）
_cached_admin_mentions = None
_cached_group_chat_id = None


def select_rotated_message(message: str) -> str:
    """简化版：直接返回消息（已移除基于日期的复杂轮换逻辑）"""
    if not message:
        return ""
    return message.strip()


def get_current_weekday_index() -> int:
    """获取当前星期几对应的文案索引（1-7）
    返回: 1=周一, 2=周二, ..., 7=周日
    """
    from datetime import date

    weekday = date.today().weekday()  # 0=Monday, 6=Sunday
    return weekday + 1  # 转换为1-7


def get_weekday_message(config: dict, prefix: str, weekday_index: int) -> str:
    """
    从配置字典中获取指定星期几的文案
    Args:
        config: 群组配置字典
        prefix: 字段前缀，如 "start_work_message", "end_work_message" 等
        weekday_index: 星期几的索引（1-7）
    Returns:
        文案字符串，如果不存在或为None则返回空字符串
    """
    field_name = f"{prefix}_{weekday_index}"
    value = config.get(field_name)
    if value is None:
        return ""
    return str(value).strip()


def create_message_keyboard(
    bot_links: str = None, worker_links: str = None
) -> Optional[InlineKeyboardMarkup]:
    """创建消息内联键盘（自动和人工按钮）

    Args:
        bot_links: 机器人链接（多个链接用换行符分隔）
        worker_links: 人工链接（多个链接用换行符分隔）

    Returns:
        InlineKeyboardMarkup 或 None（如果没有链接）
    """
    keyboard = []

    # 解析链接（支持换行符分隔的多个链接）
    bot_link_list = []
    if bot_links:
        bot_link_list = [
            link.strip()
            for link in bot_links.split("\n")
            if link.strip()
            and (
                link.strip().startswith("http://")
                or link.strip().startswith("https://")
            )
        ]

    worker_link_list = []
    if worker_links:
        worker_link_list = [
            link.strip()
            for link in worker_links.split("\n")
            if link.strip()
            and (
                link.strip().startswith("http://")
                or link.strip().startswith("https://")
            )
        ]

    # 添加"Auto"按钮（机器人链接）
    if bot_link_list:
        keyboard.append([InlineKeyboardButton("🤖 Auto", url=bot_link_list[0])])

    # 添加"Manual"按钮（个人链接）
    if worker_link_list:
        keyboard.append([InlineKeyboardButton("👤 Manual", url=worker_link_list[0])])

    if not keyboard:
        return None

    return InlineKeyboardMarkup(keyboard)


def select_random_anti_fraud_message(messages: list) -> str:
    """随机选择一个防诈骗语录"""
    if not messages:
        return ""
    return random.choice(messages)


def format_red_message(message: str) -> str:
    """将消息格式化为强调显示（HTML格式）
    注意：Telegram Bot API不支持CSS样式，使用加粗和emoji来强调
    """
    if not message:
        return ""
    # 转义 HTML 特殊字符，避免解析错误
    import html

    escaped_message = html.escape(message)
    # 使用加粗和警告emoji来强调（Telegram不支持CSS样式）
    return f"⚠️ <b>{escaped_message}</b>"


async def _send_group_message(
    bot, chat_id: int, message: str, bot_links: str = None, worker_links: str = None
) -> bool:
    """统一的群组消息发送辅助函数
    机器人直接在群组中发送消息（可以添加内联键盘按钮）

    Args:
        bot: Telegram Bot 实例
        chat_id: 群组ID
        message: 消息内容
        bot_links: 机器人链接（可选）
        worker_links: 人工客服链接（可选）

    Returns:
        bool: 发送是否成功
    """
    try:
        if not message or not message.strip():
            logger.warning(f"群组 {chat_id}: 消息内容为空，跳过发送")
            return False

        logger.debug(
            f"群组 {chat_id}: 准备发送消息，长度={len(message)}, "
            f"bot_links={bool(bot_links)}, worker_links={bool(worker_links)}"
        )

        # 创建内联键盘（如果有链接）
        reply_markup = create_message_keyboard(bot_links, worker_links)
        logger.debug(f"群组 {chat_id}: 内联键盘已创建: {reply_markup is not None}")

        # 机器人直接在群组中发送消息
        logger.info(f"机器人正在向群组 {chat_id} 发送消息（长度: {len(message)} 字符）")
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )
        logger.info(f"✅ 消息已成功发送到群组 {chat_id}")
        return True
    except Exception as e:
        logger.error(
            f"❌ 发送消息到群组 {chat_id} 失败: {type(e).__name__}: {e}", exc_info=True
        )
        return False


def _combine_message_with_anti_fraud(
    main_message: str, anti_fraud_messages: list
) -> str:
    """组合主消息和防诈骗语录（旧版，用于宣传消息）

    Args:
        main_message: 主消息内容
        anti_fraud_messages: 防诈骗语录列表

    Returns:
        str: 组合后的消息
    """
    final_message = main_message

    # 添加防诈骗语录（如果存在）
    if anti_fraud_messages:
        random_anti_fraud = select_random_anti_fraud_message(anti_fraud_messages)
        if random_anti_fraud:
            # 处理多版本（如果语录包含 ⸻ 分隔符）
            rotated_anti_fraud = select_rotated_message(random_anti_fraud)
            if rotated_anti_fraud:
                red_anti_fraud = format_red_message(rotated_anti_fraud)
                final_message = f"{main_message}\n\n{red_anti_fraud}"

    return final_message


def _combine_fixed_message_with_anti_fraud(
    main_message: str, anti_fraud_message: str
) -> str:
    """组合主消息和固定的防诈骗文案（新版，用于按星期轮换的消息）

    Args:
        main_message: 主消息内容
        anti_fraud_message: 防诈骗文案字符串（固定，不是列表）

    Returns:
        str: 组合后的消息
    """
    if not main_message:
        return ""
    if not anti_fraud_message:
        return main_message
    formatted_anti_fraud = format_red_message(anti_fraud_message.strip())
    return f"{main_message}\n\n{formatted_anti_fraud}"


async def get_group_admins_from_chat(bot, chat_id: int) -> list:
    """
    从指定群组获取所有管理员用户名
    返回用户名列表（不包含@符号）
    """
    try:
        # 获取群组管理员列表
        administrators = await bot.get_chat_administrators(chat_id)

        usernames = []
        for admin in administrators:
            user = admin.user
            # 只获取有用户名的管理员
            if user.username:
                usernames.append(user.username)

        return usernames
    except Exception as e:
        logger.error(f"获取群组 {chat_id} 管理员失败: {e}", exc_info=True)
        return []


async def _check_cached_admin_mentions(group_chat_id: Optional[int]) -> Optional[str]:
    """检查缓存的管理员提及

    Args:
        group_chat_id: 群组ID

    Returns:
        缓存的提及字符串，如果不存在则返回None
    """
    global _cached_admin_mentions, _cached_group_chat_id

    if _cached_admin_mentions is not None and _cached_group_chat_id is not None:
        if group_chat_id is None or group_chat_id == _cached_group_chat_id:
            logger.debug(f"使用缓存的管理员用户名（群组ID: {_cached_group_chat_id}）")
            return _cached_admin_mentions
    return None


async def _find_target_group_by_name(bot) -> Optional[int]:
    """查找目标群组ID（通过名称）

    Args:
        bot: Telegram Bot 实例

    Returns:
        群组ID，如果未找到则返回None
    """
    import db_operations

    configs = await db_operations.get_group_message_configs()
    target_group_name = "📱iPhone loan Chat(2)"

    for config in configs:
        chat_title = config.get("chat_title", "")
        if target_group_name in chat_title or chat_title == target_group_name:
            group_chat_id = config.get("chat_id")
            logger.info(f"找到目标群组: {chat_title} (ID: {group_chat_id})")
            return group_chat_id

    try:
        for config in configs:
            chat_id = config.get("chat_id")
            try:
                chat = await bot.get_chat(chat_id)
                if chat.title == target_group_name or target_group_name in chat.title:
                    logger.info(f"通过API找到目标群组: {chat.title} (ID: {chat_id})")
                    return chat_id
            except Exception as e:
                logger.debug(f"检查群组 {chat_id} 失败: {e}")
                continue
    except Exception as e:
        logger.debug(f"查找群组失败: {e}")

    return None


async def _get_and_format_group_admins(bot, group_chat_id: int) -> str:
    """获取并格式化群组管理员

    Args:
        bot: Telegram Bot 实例
        group_chat_id: 群组ID

    Returns:
        格式化的管理员提及字符串
    """
    global _cached_admin_mentions, _cached_group_chat_id

    admin_usernames = await get_group_admins_from_chat(bot, group_chat_id)
    if not admin_usernames:
        logger.warning(f"群组 {group_chat_id} 没有找到管理员用户名，使用默认")
        from config import ADMIN_IDS

        return await format_admin_mentions(bot, ADMIN_IDS)

    mentions = [f"@{username}" for username in admin_usernames]
    formatted_mentions = " ".join(mentions) if mentions else ""

    _cached_admin_mentions = formatted_mentions
    _cached_group_chat_id = group_chat_id
    logger.info(
        f"已缓存管理员用户名（群组ID: {group_chat_id}，共 {len(admin_usernames)} 个管理员）"
    )

    return formatted_mentions


async def format_admin_mentions_from_group(bot, group_chat_id: int = None) -> str:
    """
    从指定群组获取管理员用户名并格式化（使用缓存，只提取一次）
    如果未指定群组ID，则查找名为 "📱iPhone loan Chat(2)" 的群组
    """
    try:
        cached_mentions = await _check_cached_admin_mentions(group_chat_id)
        if cached_mentions is not None:
            return cached_mentions

        if group_chat_id is None:
            group_chat_id = await _find_target_group_by_name(bot)

        if group_chat_id is None:
            logger.warning("未找到目标群组，使用默认管理员列表")
            from config import ADMIN_IDS

            return await format_admin_mentions(bot, ADMIN_IDS)

        return await _get_and_format_group_admins(bot, group_chat_id)
    except Exception as e:
        logger.error(f"从群组获取管理员用户名失败: {e}", exc_info=True)
        from config import ADMIN_IDS

        return await format_admin_mentions(bot, ADMIN_IDS)


async def _get_luckyno44_id(bot) -> Optional[int]:
    """获取 @luckyno44 的用户ID

    Args:
        bot: Telegram bot 对象

    Returns:
        用户ID，如果获取失败则返回None
    """
    try:
        user = await bot.get_chat("@luckyno44")
        if hasattr(user, "id"):
            return user.id
    except Exception as e:
        logger.debug(f"无法获取 @luckyno44 的用户ID: {e}")
    return None


async def _collect_admin_usernames(
    bot, admin_ids: List[int], target_count: int
) -> List[str]:
    """收集管理员用户名

    Args:
        bot: Telegram bot 对象
        admin_ids: 管理员ID列表
        target_count: 目标数量

    Returns:
        用户名列表
    """
    shuffled_admins = admin_ids.copy()
    random.shuffle(shuffled_admins)

    mentions = []
    collected_count = 0

    for admin_id in shuffled_admins:
        if collected_count >= target_count:
            break

        try:
            user = await bot.get_chat(admin_id)
            username = user.username
            if username:
                mentions.append(f"@{username}")
                collected_count += 1
        except Exception as e:
            logger.debug(f"获取管理员 {admin_id} 用户名失败: {e}")

    return mentions


async def format_admin_mentions(bot, admin_ids: list) -> str:
    """
    格式化管理员@用户名
    固定包含 @luckyno44，然后随机选择4名其他管理员
    如果某些管理员没有用户名或获取失败，继续尝试其他管理员
    """
    if not admin_ids:
        return ""

    try:
        fixed_username = "@luckyno44"
        mentions = [fixed_username]

        luckyno44_id = await _get_luckyno44_id(bot)
        other_admins = [aid for aid in admin_ids if aid != luckyno44_id]

        if not other_admins:
            return fixed_username

        additional_mentions = await _collect_admin_usernames(bot, other_admins, 4)
        mentions.extend(additional_mentions)

        return " ".join(mentions) if mentions else fixed_username
    except Exception as e:
        logger.error(f"格式化管理员@用户名失败: {e}", exc_info=True)
        return "@luckyno44"
