"""定时播报执行器"""

# 标准库
import asyncio
import logging
import random
from datetime import datetime

# 第三方库
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# 本地模块
import db_operations

# 北京时区
BEIJING_TZ = pytz.timezone("Asia/Shanghai")

logger = logging.getLogger(__name__)

# 全局调度器
scheduler = None

# 缓存管理员用户名（只提取一次）
_cached_admin_mentions = None
_cached_group_chat_id = None

# 记录上次发送的消息类型（用于确保公告和语录不同时发送）
_last_sent_message_type = None  # 'announcement' 或 'promotion'


def select_rotated_message(message: str) -> str:
    """从多版本消息中选择一个版本（基于日期轮换），使用 ⸻ 作为分隔符"""
    if not message or "⸻" not in message:
        return message.strip()

    versions = [v.strip() for v in message.split("⸻") if v.strip()]
    if not versions:
        return message.strip()

    day_of_year = datetime.now().timetuple().tm_yday
    version_index = day_of_year % len(versions)
    return versions[version_index]


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


async def format_admin_mentions_from_group(bot, group_chat_id: int = None) -> str:
    """
    从指定群组获取管理员用户名并格式化（使用缓存，只提取一次）
    如果未指定群组ID，则查找名为 "📱iPhone loan Chat(2)" 的群组
    """
    global _cached_admin_mentions, _cached_group_chat_id

    try:
        # 如果缓存存在且群组ID匹配，直接返回缓存
        if _cached_admin_mentions is not None and _cached_group_chat_id is not None:
            if group_chat_id is None or group_chat_id == _cached_group_chat_id:
                logger.debug(f"使用缓存的管理员用户名（群组ID: {_cached_group_chat_id}）")
                return _cached_admin_mentions

        # 如果没有指定群组ID，尝试查找指定名称的群组
        if group_chat_id is None:
            configs = await db_operations.get_group_message_configs()
            target_group_name = "📱iPhone loan Chat(2)"

            for config in configs:
                chat_title = config.get("chat_title", "")
                if target_group_name in chat_title or chat_title == target_group_name:
                    group_chat_id = config.get("chat_id")
                    logger.info(f"找到目标群组: {chat_title} (ID: {group_chat_id})")
                    break

            # 如果还是没找到，尝试通过群组名称查找
            if group_chat_id is None:
                try:
                    # 尝试在所有配置的群组中查找
                    for config in configs:
                        chat_id = config.get("chat_id")
                        try:
                            chat = await bot.get_chat(chat_id)
                            if chat.title == target_group_name or target_group_name in chat.title:
                                group_chat_id = chat_id
                                logger.info(
                                    f"通过API找到目标群组: {chat.title} (ID: {group_chat_id})"
                                )
                                break
                        except Exception as e:
                            logger.debug(f"检查群组 {chat_id} 失败: {e}")
                            continue
                except Exception as e:
                    logger.debug(f"查找群组失败: {e}")

        if group_chat_id is None:
            logger.warning("未找到目标群组，使用默认管理员列表")
            from config import ADMIN_IDS

            return await format_admin_mentions(bot, ADMIN_IDS)

        # 获取群组管理员用户名（只提取一次）
        admin_usernames = await get_group_admins_from_chat(bot, group_chat_id)

        if not admin_usernames:
            logger.warning(f"群组 {group_chat_id} 没有找到管理员用户名，使用默认")
            from config import ADMIN_IDS

            return await format_admin_mentions(bot, ADMIN_IDS)

        # 格式化用户名（添加@符号）
        mentions = [f"@{username}" for username in admin_usernames]
        formatted_mentions = " ".join(mentions) if mentions else ""

        # 缓存结果
        _cached_admin_mentions = formatted_mentions
        _cached_group_chat_id = group_chat_id
        logger.info(
            f"已缓存管理员用户名（群组ID: {group_chat_id}，共 {len(admin_usernames)} 个管理员）"
        )

        return formatted_mentions
    except Exception as e:
        logger.error(f"从群组获取管理员用户名失败: {e}", exc_info=True)
        # 失败时回退到默认方式
        from config import ADMIN_IDS

        return await format_admin_mentions(bot, ADMIN_IDS)


async def format_admin_mentions(bot, admin_ids: list) -> str:
    """
    格式化管理员@用户名
    固定包含 @luckyno44，然后随机选择4名其他管理员
    如果某些管理员没有用户名或获取失败，继续尝试其他管理员
    """
    if not admin_ids:
        return ""

    try:
        import random

        # 固定包含 @luckyno44
        fixed_username = "@luckyno44"
        mentions = [fixed_username]

        # 尝试获取 luckyno44 的用户ID（如果存在）
        luckyno44_id = None
        try:
            # 尝试通过用户名获取用户（需要用户已经与bot交互过）
            # 注意：这个方法可能失败，如果用户从未与bot交互
            user = await bot.get_chat("@luckyno44")
            if hasattr(user, "id"):
                luckyno44_id = user.id
        except Exception as e:
            logger.debug(f"无法获取 @luckyno44 的用户ID: {e}")

        # 从管理员列表中排除 luckyno44（如果存在）
        other_admins = [aid for aid in admin_ids if aid != luckyno44_id]

        if not other_admins:
            return fixed_username

        # 随机打乱管理员列表，然后尝试获取用户名
        # 这样可以确保即使某些管理员获取失败，也能尝试其他管理员
        shuffled_admins = other_admins.copy()
        random.shuffle(shuffled_admins)

        # 尝试获取最多4个有效的管理员用户名
        target_count = 4
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
                # 继续尝试下一个管理员

        return " ".join(mentions) if mentions else fixed_username
    except Exception as e:
        logger.error(f"格式化管理员@用户名失败: {e}", exc_info=True)
        return "@luckyno44"  # 至少返回固定的用户名


async def send_scheduled_broadcast(bot, broadcast):
    """发送定时播报"""
    try:
        chat_id = broadcast["chat_id"]
        message = broadcast["message"]

        if not chat_id:
            logger.warning(f"播报 {broadcast['slot']} 没有设置chat_id，跳过发送")
            return

        await bot.send_message(chat_id=chat_id, text=message)
        logger.info(f"定时播报 {broadcast['slot']} 已发送到群组 {chat_id}")
    except Exception as e:
        logger.error(f"发送定时播报 {broadcast['slot']} 失败: {e}", exc_info=True)


async def setup_scheduled_broadcasts(bot):
    """设置定时播报任务"""
    global scheduler

    if scheduler is None:
        scheduler = AsyncIOScheduler()
        scheduler.start()

    # 只清除播报任务（不清除日切报表任务）
    for job in scheduler.get_jobs():
        if job.id.startswith("broadcast_"):
            scheduler.remove_job(job.id)

    # 获取所有激活的定时播报
    broadcasts = await db_operations.get_active_scheduled_broadcasts()

    for broadcast in broadcasts:
        try:
            time_str = broadcast["time"]
            # 解析时间 (HH:MM 或 HH)
            time_parts = time_str.split(":")
            hour = int(time_parts[0])
            minute = int(time_parts[1]) if len(time_parts) > 1 else 0

            # 创建定时任务（每天执行）
            job_id = f"broadcast_{broadcast['slot']}"

            scheduler.add_job(
                send_scheduled_broadcast,
                trigger=CronTrigger(hour=hour, minute=minute, timezone=BEIJING_TZ),
                args=[bot, broadcast],
                id=job_id,
                replace_existing=True,
            )

            logger.info(
                f"已设置定时播报 {broadcast['slot']}: 每天 {time_str} 发送到群组 {broadcast['chat_id']}"
            )
        except Exception as e:
            logger.error(f"设置定时播报 {broadcast['slot']} 失败: {e}", exc_info=True)


async def reload_scheduled_broadcasts(bot):
    """重新加载定时播报任务"""
    await setup_scheduled_broadcasts(bot)


async def send_daily_report(bot):
    """发送日切报表Excel文件给所有管理员和授权员工（业务员）（每天生成两个Excel：订单总表和每日变化数据）"""
    logger.info("=" * 60)
    logger.info("开始执行每日报表生成任务")
    logger.info("=" * 60)
    try:
        # 获取日切日期（使用get_daily_period_date，因为日切是在23:00后）
        # 如果当前时间在23:00之后，get_daily_period_date会返回明天的日期
        # 但我们需要统计的是今天的数据，所以需要减一天
        from datetime import datetime, timedelta

        import pytz

        import db_operations
        from config import ADMIN_IDS
        from utils.date_helpers import get_daily_period_date

        tz = pytz.timezone("Asia/Shanghai")
        now = datetime.now(tz)
        # 如果当前时间在23:00之后，统计今天的数据；否则统计昨天的数据
        if now.hour >= 23:
            # 23:00之后，统计今天的数据
            report_date = now.strftime("%Y-%m-%d")
        else:
            # 23:00之前，统计昨天的数据
            yesterday = now - timedelta(days=1)
            report_date = yesterday.strftime("%Y-%m-%d")

        logger.info(f"开始生成每日Excel报表 ({report_date})")

        # 1. 生成订单总表Excel
        try:
            from utils.excel_export import export_orders_to_excel

            # 获取所有有效订单
            valid_orders = await db_operations.get_all_valid_orders()

            # 获取当日利息总额
            daily_interest = await db_operations.get_daily_interest_total(report_date)

            # 获取当日完成的订单
            completed_orders = await db_operations.get_completed_orders_by_date(report_date)

            # 获取当日违约完成的订单
            breach_end_orders = await db_operations.get_breach_end_orders_by_date(report_date)

            # 获取日切数据
            daily_summary = await db_operations.get_daily_summary(report_date)

            # 导出订单总表Excel
            orders_excel_path = await export_orders_to_excel(
                valid_orders, completed_orders, breach_end_orders, daily_interest, daily_summary
            )
            logger.info(f"订单总表Excel已生成: {orders_excel_path}")
        except Exception as e:
            logger.error(f"生成订单总表Excel失败: {e}", exc_info=True)
            orders_excel_path = None

        # 2. 生成每日变化数据Excel
        try:
            from utils.excel_export import export_daily_changes_to_excel

            # 导出每日变化数据Excel
            changes_excel_path = await export_daily_changes_to_excel(report_date)
            logger.info(f"每日变化数据Excel已生成: {changes_excel_path}")
        except Exception as e:
            logger.error(f"生成每日变化数据Excel失败: {e}", exc_info=True)
            changes_excel_path = None

        # 获取所有授权员工（业务员）
        authorized_users = await db_operations.get_authorized_users()

        # 合并管理员和授权员工列表（去重）
        all_recipients = list(set(ADMIN_IDS + authorized_users))

        logger.info(
            f"报表接收人: {len(ADMIN_IDS)} 个管理员, {len(authorized_users)} 个业务员, 总计 {len(all_recipients)} 人"
        )

        # 发送给所有管理员和授权员工
        success_count = 0
        fail_count = 0
        for user_id in all_recipients:
            try:
                # 发送订单总表Excel
                if orders_excel_path:
                    with open(orders_excel_path, "rb") as f:
                        await bot.send_document(
                            chat_id=user_id,
                            document=f,
                            filename=f"订单总表_{report_date}.xlsx",
                            caption=f"📊 订单总表 ({report_date})\n\n包含所有有效订单及利息记录",
                        )

                # 发送每日变化数据Excel
                if changes_excel_path:
                    with open(changes_excel_path, "rb") as f:
                        await bot.send_document(
                            chat_id=user_id,
                            document=f,
                            filename=f"每日变化数据_{report_date}.xlsx",
                            caption=f"📈 每日变化数据 ({report_date})\n\n包含：\n• 新增订单\n• 完成订单\n• 违约完成订单\n• 收入明细（利息等）\n• 开销明细\n• 数据汇总",
                        )

                success_count += 1
                recipient_type = "管理员" if user_id in ADMIN_IDS else "业务员"
                logger.info(f"每日Excel报表已发送给{recipient_type} {user_id}")
            except Exception as e:
                fail_count += 1
                recipient_type = "管理员" if user_id in ADMIN_IDS else "业务员"
                logger.error(
                    f"发送每日Excel报表给{recipient_type} {user_id} 失败: {e}", exc_info=True
                )

        # 清理临时文件
        import os

        for file_path in [orders_excel_path, changes_excel_path]:
            if file_path:
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.warning(f"删除临时文件失败 {file_path}: {e}")

        logger.info(f"每日Excel报表发送完成: 成功 {success_count}, 失败 {fail_count}")
        logger.info("=" * 60)
        logger.info("每日报表生成任务执行完成")
        logger.info("=" * 60)
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"发送每日Excel报表失败: {e}", exc_info=True)
        logger.error("=" * 60)
        # 发送错误通知给管理员
        try:
            from config import ADMIN_IDS

            for admin_id in ADMIN_IDS:
                try:
                    await bot.send_message(
                        chat_id=admin_id,
                        text=f"❌ 每日报表生成失败\n\n错误: {str(e)}\n\n请检查日志获取详细信息",
                    )
                except Exception as notify_error:
                    logger.error(
                        f"发送错误通知给管理员 {admin_id} 失败: {notify_error}", exc_info=True
                    )
        except Exception as notify_error:
            logger.error(f"发送错误通知失败: {notify_error}", exc_info=True)


async def setup_daily_report(bot):
    """设置日切报表自动发送任务（每天23:05执行）"""
    global scheduler

    if scheduler is None:
        scheduler = AsyncIOScheduler()
        scheduler.start()

    # 添加日切报表任务
    try:
        scheduler.add_job(
            send_daily_report,
            trigger=CronTrigger(hour=23, minute=5, timezone=BEIJING_TZ),
            args=[bot],
            id="daily_report",
            replace_existing=True,
        )
        logger.info("已设置日切报表任务: 每天 23:05 自动发送")
    except Exception as e:
        logger.error(f"设置日切报表任务失败: {e}", exc_info=True)


async def send_start_work_messages(bot):
    """发送开工信息到所有配置的总群"""
    try:
        from config import ADMIN_IDS

        configs = await db_operations.get_group_message_configs()

        if not configs:
            logger.info("没有配置的总群，跳过发送开工信息")
            return

        # 获取激活的防诈骗语录
        anti_fraud_messages = await db_operations.get_active_anti_fraud_messages()

        # 获取管理员@用户名（从指定群组获取）
        admin_mentions = await format_admin_mentions_from_group(bot)

        success_count = 0
        fail_count = 0

        for config in configs:
            chat_id = config.get("chat_id")
            message = config.get("start_work_message")

            if not chat_id or not message:
                continue

            try:
                # 选择轮换版本
                rotated_message = select_rotated_message(message)

                # 组合消息：主消息 + 防诈骗语录 + 管理员@用户名
                final_message = rotated_message

                # 添加防诈骗语录（如果存在）
                if anti_fraud_messages:
                    random_anti_fraud = select_random_anti_fraud_message(anti_fraud_messages)
                    if random_anti_fraud:
                        # 处理多版本（如果语录包含 ⸻ 分隔符）
                        rotated_anti_fraud = select_rotated_message(random_anti_fraud)
                        if rotated_anti_fraud:
                            red_anti_fraud = format_red_message(rotated_anti_fraud)
                            final_message = f"{rotated_message}\n\n{red_anti_fraud}"

                # 添加管理员@用户名
                if admin_mentions:
                    final_message = f"{final_message}\n\n{admin_mentions}"

                # 发送消息（使用HTML格式以支持红色文字）
                await bot.send_message(chat_id=chat_id, text=final_message, parse_mode="HTML")
                success_count += 1
                logger.info(f"开工信息已发送到群组 {chat_id}")
            except Exception as e:
                fail_count += 1
                logger.error(f"发送开工信息到群组 {chat_id} 失败: {e}", exc_info=True)

        logger.info(f"开工信息发送完成: 成功 {success_count}, 失败 {fail_count}")
    except Exception as e:
        logger.error(f"发送开工信息失败: {e}", exc_info=True)


async def setup_start_work_schedule(bot):
    """设置开工信息定时任务（每天11:00执行）"""
    global scheduler

    if scheduler is None:
        scheduler = AsyncIOScheduler()
        scheduler.start()

    try:
        scheduler.add_job(
            send_start_work_messages,
            trigger=CronTrigger(hour=11, minute=0, timezone=BEIJING_TZ),
            args=[bot],
            id="start_work_messages",
            replace_existing=True,
        )
        logger.info("已设置开工信息任务: 每天 11:00 自动发送")
    except Exception as e:
        logger.error(f"设置开工信息任务失败: {e}", exc_info=True)


async def send_end_work_messages(bot):
    """发送收工信息到所有配置的总群"""
    try:
        from config import ADMIN_IDS

        configs = await db_operations.get_group_message_configs()

        if not configs:
            logger.info("没有配置的总群，跳过发送收工信息")
            return

        # 获取激活的防诈骗语录
        anti_fraud_messages = await db_operations.get_active_anti_fraud_messages()

        # 获取管理员@用户名（从指定群组获取）
        admin_mentions = await format_admin_mentions_from_group(bot)

        success_count = 0
        fail_count = 0

        for config in configs:
            chat_id = config.get("chat_id")
            message = config.get("end_work_message")

            if not chat_id or not message:
                continue

            try:
                # 选择轮换版本
                rotated_message = select_rotated_message(message)

                # 组合消息：主消息 + 防诈骗语录 + 管理员@用户名
                final_message = rotated_message

                # 添加防诈骗语录（如果存在）
                if anti_fraud_messages:
                    random_anti_fraud = select_random_anti_fraud_message(anti_fraud_messages)
                    if random_anti_fraud:
                        # 处理多版本（如果语录包含 ⸻ 分隔符）
                        rotated_anti_fraud = select_rotated_message(random_anti_fraud)
                        if rotated_anti_fraud:
                            red_anti_fraud = format_red_message(rotated_anti_fraud)
                            final_message = f"{rotated_message}\n\n{red_anti_fraud}"

                # 添加管理员@用户名
                if admin_mentions:
                    final_message = f"{final_message}\n\n{admin_mentions}"

                # 发送消息（使用HTML格式以支持红色文字）
                await bot.send_message(chat_id=chat_id, text=final_message, parse_mode="HTML")
                success_count += 1
                logger.info(f"收工信息已发送到群组 {chat_id}")
            except Exception as e:
                fail_count += 1
                logger.error(f"发送收工信息到群组 {chat_id} 失败: {e}", exc_info=True)

        logger.info(f"收工信息发送完成: 成功 {success_count}, 失败 {fail_count}")
    except Exception as e:
        logger.error(f"发送收工信息失败: {e}", exc_info=True)


async def setup_end_work_schedule(bot):
    """设置收工信息定时任务（每天23:00执行）"""
    global scheduler

    if scheduler is None:
        scheduler = AsyncIOScheduler()
        scheduler.start()

    try:
        scheduler.add_job(
            send_end_work_messages,
            trigger=CronTrigger(hour=23, minute=0, timezone=BEIJING_TZ),
            args=[bot],
            id="end_work_messages",
            replace_existing=True,
        )
        logger.info("已设置收工信息任务: 每天 23:00 自动发送")
    except Exception as e:
        logger.error(f"设置收工信息任务失败: {e}", exc_info=True)


async def send_daily_operations_summary(bot):
    """发送每日操作汇总报告（每天23:00执行）"""
    try:
        from config import ADMIN_IDS
        from utils.date_helpers import get_daily_period_date

        date = get_daily_period_date()
        logger.info(f"开始生成每日操作汇总报告 ({date})")

        # 获取操作汇总
        summary = await db_operations.get_daily_operations_summary(date)

        if not summary or summary.get("total_count", 0) == 0:
            # 没有操作记录，发送提示
            message = f"📊 每日操作汇总 ({date})\n\n"
            message += "✅ 今日无操作记录"

            for admin_id in ADMIN_IDS:
                try:
                    await bot.send_message(chat_id=admin_id, text=message)
                except Exception as e:
                    logger.error(f"发送操作汇总给管理员 {admin_id} 失败: {e}", exc_info=True)
            return

        # 操作类型的中文名称映射
        operation_type_names = {
            "order_created": "订单创建",
            "order_state_change": "订单状态变更",
            "order_completed": "订单完成",
            "order_breach_end": "违约完成",
            "interest": "利息收入",
            "principal_reduction": "本金减少",
            "expense": "开销记录",
            "funds_adjustment": "资金调整",
            "other": "其他操作",
        }

        # 格式化汇总消息
        message = f"📊 每日操作汇总 ({date})\n"
        message += "═══════════════════════════════════════\n"
        message += f"总操作数: {summary['total_count']}\n"
        message += f"有效操作: {summary['valid_count']}\n"
        message += f"已撤销: {summary['undone_count']}\n\n"

        # 按操作类型统计
        if summary.get("by_type"):
            message += "📋 按操作类型:\n"
            for op_type, count in sorted(
                summary["by_type"].items(), key=lambda x: x[1], reverse=True
            ):
                type_name = operation_type_names.get(op_type, op_type)
                message += f"  {type_name}: {count} 次\n"
            message += "\n"

        # 按用户统计（只显示前5个）
        if summary.get("by_user"):
            message += "👥 操作最多的用户 (Top 5):\n"
            user_stats = sorted(summary["by_user"].items(), key=lambda x: x[1], reverse=True)[:5]
            for user_id, count in user_stats:
                message += f"  用户 {user_id}: {count} 次\n"

        message += "\n使用 /daily_operations 查看详细操作记录"

        # 发送给所有管理员
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(chat_id=admin_id, text=message)
            except Exception as e:
                logger.error(f"发送操作汇总给管理员 {admin_id} 失败: {e}", exc_info=True)

        logger.info(f"每日操作汇总报告发送完成 ({date})")

    except Exception as e:
        logger.error(f"发送每日操作汇总报告失败: {e}", exc_info=True)


async def setup_daily_operations_summary(bot):
    """设置每日操作汇总定时任务（已禁用自动发送，仅保留命令查询功能）"""
    # 不再设置定时任务，用户可以通过 /daily_operations 和 /daily_operations_summary 命令查询
    logger.info("每日操作汇总功能：已禁用自动发送，请使用命令查询")
    pass


async def send_random_announcements(bot):
    """随机发送公司公告到所有配置的总群（确保与宣传语录不同时发送）"""
    await send_random_announcements_internal(bot, skip_check=False)


async def send_random_announcements_internal(bot, skip_check=False):
    """内部函数：发送公司公告"""
    global _last_sent_message_type

    try:
        import random
        from datetime import datetime, timedelta

        import pytz

        # 检查上次发送的类型，如果上次发送的是公告，这次改为发送宣传语录
        if not skip_check and _last_sent_message_type == "announcement":
            logger.info("上次发送的是公告，本次改为发送宣传语录")
            # 调用宣传语录发送函数，但传入标志避免再次检查
            await send_company_promotion_messages_internal(bot, skip_check=True)
            return

        # 检查发送计划配置
        schedule = await db_operations.get_announcement_schedule()
        if not schedule or not schedule.get("is_active"):
            logger.info("公告发送功能未激活，跳过发送")
            return

        # 检查发送间隔
        last_sent_at = schedule.get("last_sent_at")
        interval_hours = schedule.get("interval_hours", 3)

        if last_sent_at:
            tz = pytz.timezone("Asia/Shanghai")
            last_sent = datetime.strptime(last_sent_at, "%Y-%m-%d %H:%M:%S")
            last_sent = tz.localize(last_sent)
            now = datetime.now(tz)

            if (now - last_sent).total_seconds() < interval_hours * 3600:
                logger.info(f"距离上次发送不足 {interval_hours} 小时，跳过发送")
                return

        # 获取激活的公告列表
        announcements = await db_operations.get_company_announcements()

        if not announcements:
            logger.info("没有激活的公告，跳过发送")
            return

        # 随机选择一条公告
        selected_announcement = random.choice(announcements)
        message = selected_announcement.get("message")

        if not message:
            logger.warning("选中的公告消息为空，跳过发送")
            return

        # 处理多版本消息轮播（如果消息包含 ⸻ 分隔符）
        rotated_message = select_rotated_message(message)

        # 获取所有配置的总群
        configs = await db_operations.get_group_message_configs()

        if not configs:
            logger.info("没有配置的总群，跳过发送公告")
            return

        # 获取管理员@用户名（从指定群组获取，使用缓存）
        admin_mentions = await format_admin_mentions_from_group(bot)

        # 组合消息：主消息 + 管理员@用户名
        final_message = rotated_message
        if admin_mentions:
            final_message = f"{rotated_message}\n\n{admin_mentions}"

        success_count = 0
        fail_count = 0

        for config in configs:
            chat_id = config.get("chat_id")

            if not chat_id:
                continue

            try:
                await bot.send_message(chat_id=chat_id, text=final_message, parse_mode="HTML")
                success_count += 1
                logger.info(f"公司公告已发送到群组 {chat_id}")
            except Exception as e:
                fail_count += 1
                logger.error(f"发送公司公告到群组 {chat_id} 失败: {e}", exc_info=True)

        # 更新最后发送时间
        await db_operations.update_announcement_last_sent()

        # 记录本次发送的类型
        _last_sent_message_type = "announcement"

        logger.info(f"公司公告发送完成: 成功 {success_count}, 失败 {fail_count}")
    except Exception as e:
        logger.error(f"发送公司公告失败: {e}", exc_info=True)


async def send_company_promotion_messages(bot):
    """轮播发送公司宣传语录到所有配置的总群（每2小时，确保与公告不同时发送）"""
    await send_company_promotion_messages_internal(bot, skip_check=False)


async def send_alternating_group_messages(bot):
    """统一的消息发送函数：交替发送公告和宣传语录（确保不同时发送）"""
    global _last_sent_message_type

    try:
        # 根据上次发送的类型决定本次发送哪个
        if _last_sent_message_type == "announcement":
            # 上次发送的是公告，这次发送宣传语录
            logger.info("上次发送的是公告，本次发送宣传语录")
            await send_company_promotion_messages_internal(bot, skip_check=True)
        elif _last_sent_message_type == "promotion":
            # 上次发送的是宣传语录，这次发送公告
            logger.info("上次发送的是宣传语录，本次发送公告")
            await send_random_announcements_internal(bot, skip_check=True)
        else:
            # 未设置或首次发送，随机选择其中一个
            import random

            if random.choice([True, False]):
                logger.info("首次发送，随机选择：公告")
                await send_random_announcements_internal(bot, skip_check=True)
            else:
                logger.info("首次发送，随机选择：宣传语录")
                await send_company_promotion_messages_internal(bot, skip_check=True)
    except Exception as e:
        logger.error(f"发送交替消息失败: {e}", exc_info=True)


async def send_company_promotion_messages_internal(bot, skip_check=False):
    """内部函数：发送公司宣传语录"""
    global _last_sent_message_type

    try:
        # 检查上次发送的类型，如果上次发送的是宣传语录，这次发送公告
        if not skip_check and _last_sent_message_type == "promotion":
            logger.info("上次发送的是宣传语录，本次改为发送公告")
            await send_random_announcements_internal(bot, skip_check=True)
            return

        # 获取激活的宣传语录列表
        promotion_messages = await db_operations.get_active_promotion_messages()

        if not promotion_messages:
            logger.info("没有激活的公司宣传语录，跳过发送")
            return

        # 过滤掉空消息（双重检查，确保没有空消息）
        valid_messages = [
            msg for msg in promotion_messages if msg.get("message") and msg.get("message").strip()
        ]

        if not valid_messages:
            logger.warning("没有有效的公司宣传语录（所有消息都为空），跳过发送")
            return

        # 轮播选择：根据当前时间选择索引（按顺序轮播）
        day_of_year = datetime.now().timetuple().tm_yday
        hour = datetime.now().hour
        # 每2小时轮播一次，一天12次，使用 (day_of_year * 12 + hour // 2) 作为索引
        rotation_index = (day_of_year * 12 + hour // 2) % len(valid_messages)
        selected_message = valid_messages[rotation_index].get("message")

        if not selected_message or not selected_message.strip():
            logger.warning("选中的宣传语录消息为空，跳过发送")
            return

        # 处理多版本消息轮播（如果消息包含 ⸻ 分隔符）
        rotated_message = select_rotated_message(selected_message)

        # 再次检查轮播后的消息是否为空
        if not rotated_message or not rotated_message.strip():
            logger.warning("轮播后的宣传语录消息为空，跳过发送")
            return

        # 获取激活的防诈骗语录
        anti_fraud_messages = await db_operations.get_active_anti_fraud_messages()

        # 获取管理员@用户名（从指定群组获取，使用缓存）
        admin_mentions = await format_admin_mentions_from_group(bot)

        # 组合消息：主消息 + 防诈骗语录 + 管理员@用户名
        final_message = rotated_message

        # 添加防诈骗语录（如果存在）
        if anti_fraud_messages:
            random_anti_fraud = select_random_anti_fraud_message(anti_fraud_messages)
            if random_anti_fraud:
                # 处理多版本（如果语录包含 ⸻ 分隔符）
                rotated_anti_fraud = select_rotated_message(random_anti_fraud)
                if rotated_anti_fraud:
                    red_anti_fraud = format_red_message(rotated_anti_fraud)
                    final_message = f"{rotated_message}\n\n{red_anti_fraud}"

        # 添加管理员@用户名
        if admin_mentions:
            final_message = f"{final_message}\n\n{admin_mentions}"

        # 获取所有配置的总群
        configs = await db_operations.get_group_message_configs()

        if not configs:
            logger.info("没有配置的总群，跳过发送公司宣传语录")
            return

        success_count = 0
        fail_count = 0

        for config in configs:
            chat_id = config.get("chat_id")

            if not chat_id:
                continue

            try:
                # 发送消息（使用HTML格式以支持红色文字）
                await bot.send_message(chat_id=chat_id, text=final_message, parse_mode="HTML")
                success_count += 1
                logger.info(f"公司宣传语录已发送到群组 {chat_id}")
            except Exception as e:
                fail_count += 1
                logger.error(f"发送公司宣传语录到群组 {chat_id} 失败: {e}", exc_info=True)

        # 记录本次发送的类型
        _last_sent_message_type = "promotion"

        logger.info(f"公司宣传语录发送完成: 成功 {success_count}, 失败 {fail_count}")
    except Exception as e:
        logger.error(f"发送公司宣传语录失败: {e}", exc_info=True)


async def setup_alternating_messages_schedule(bot):
    """设置交替消息发送任务（公告和宣传语录交替发送，每2小时执行一次）"""
    global scheduler

    if scheduler is None:
        scheduler = AsyncIOScheduler()
        scheduler.start()

    try:
        # 移除旧的独立任务（如果存在）
        try:
            scheduler.remove_job("company_promotion_messages")
            logger.info("已移除旧的宣传语录独立任务")
        except:
            pass

        try:
            scheduler.remove_job("random_announcements")
            logger.info("已移除旧的公告独立任务")
        except:
            pass

        # 添加新的统一任务（每2小时执行一次）
        scheduler.add_job(
            send_alternating_group_messages,
            trigger=IntervalTrigger(hours=2),
            args=[bot],
            id="alternating_group_messages",
            replace_existing=True,
        )
        logger.info("已设置交替消息发送任务: 每 2 小时自动发送（公告和宣传语录交替）")
    except Exception as e:
        logger.error(f"设置交替消息发送任务失败: {e}", exc_info=True)


async def send_incremental_orders_report(bot):
    """发送增量订单报表（每天23:05执行）"""
    logger.info("=" * 60)
    logger.info("开始执行增量订单报表生成任务")
    logger.info("=" * 60)
    try:
        from config import ADMIN_IDS
        from utils.excel_export import export_incremental_orders_report_to_excel
        from utils.incremental_report_generator import (
            get_or_create_baseline_date,
            prepare_incremental_data,
        )

        # 获取或创建基准日期
        baseline_date = await get_or_create_baseline_date()
        current_date = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d")

        logger.info(f"开始生成增量订单报表 (基准日期: {baseline_date}, 当前日期: {current_date})")

        # 准备增量数据
        incremental_data = await prepare_incremental_data(baseline_date)
        orders_data = incremental_data.get("orders", [])
        expense_records = incremental_data.get("expenses", [])

        # 获取所有授权员工（业务员）
        authorized_users = await db_operations.get_authorized_users()

        # 合并管理员和授权员工列表（去重）
        all_recipients = list(set(ADMIN_IDS + authorized_users))

        logger.info(
            f"增量报表接收人: {len(ADMIN_IDS)} 个管理员, {len(authorized_users)} 个业务员, 总计 {len(all_recipients)} 人"
        )

        if not orders_data and not expense_records:
            # 没有增量数据，发送提示消息
            for user_id in all_recipients:
                try:
                    await bot.send_message(
                        chat_id=user_id,
                        text=f"📊 增量订单报表 ({current_date})\n\n"
                        f"基准日期: {baseline_date}\n"
                        f"当前日期: {current_date}\n\n"
                        f"✅ 无增量数据",
                    )
                except Exception as e:
                    recipient_type = "管理员" if user_id in ADMIN_IDS else "业务员"
                    logger.error(
                        f"发送增量报表提示给{recipient_type} {user_id} 失败: {e}", exc_info=True
                    )
            return

        # 生成Excel报表
        try:
            excel_path = await export_incremental_orders_report_to_excel(
                baseline_date, current_date, orders_data, expense_records
            )
            logger.info(f"增量订单报表Excel已生成: {excel_path}")
        except Exception as e:
            logger.error(f"生成增量订单报表Excel失败: {e}", exc_info=True)
            excel_path = None

        # 发送给所有管理员和授权员工
        success_count = 0
        fail_count = 0

        # 检查是否已经合并过（仅管理员需要合并按钮）
        merge_record = await db_operations.get_merge_record(current_date) if ADMIN_IDS else None
        if merge_record:
            merge_button_text = "⚠️ 已合并（再次合并）"
        else:
            merge_button_text = "✅ 合并到总表"

        for user_id in all_recipients:
            try:
                if excel_path:
                    # 只有管理员显示合并按钮
                    reply_markup = None
                    if user_id in ADMIN_IDS:
                        keyboard = [
                            [
                                InlineKeyboardButton(
                                    merge_button_text,
                                    callback_data=f"merge_incremental_{current_date}",
                                )
                            ]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)

                    with open(excel_path, "rb") as f:
                        await bot.send_document(
                            chat_id=user_id,
                            document=f,
                            filename=f"增量订单报表_{current_date}.xlsx",
                            caption=f"📊 增量订单报表 ({current_date})\n\n"
                            f"基准日期: {baseline_date}\n"
                            f"订单数: {len(orders_data)}\n"
                            f"开销记录: {len(expense_records)}\n\n"
                            f"💡 提示：点击利息总数列可以展开查看每期利息明细",
                            reply_markup=reply_markup,
                        )
                else:
                    await bot.send_message(
                        chat_id=user_id,
                        text=f"📊 增量订单报表 ({current_date})\n\n"
                        f"基准日期: {baseline_date}\n"
                        f"订单数: {len(orders_data)}\n"
                        f"开销记录: {len(expense_records)}\n\n"
                        f"❌ Excel生成失败，请查看日志",
                    )

                success_count += 1
                recipient_type = "管理员" if user_id in ADMIN_IDS else "业务员"
                logger.info(f"增量订单报表已发送给{recipient_type} {user_id}")
            except Exception as e:
                fail_count += 1
                recipient_type = "管理员" if user_id in ADMIN_IDS else "业务员"
                logger.error(
                    f"发送增量订单报表给{recipient_type} {user_id} 失败: {e}", exc_info=True
                )

        # 清理临时文件
        if excel_path:
            import os

            try:
                os.remove(excel_path)
            except Exception as e:
                logger.warning(f"删除临时文件失败 {excel_path}: {e}")

        logger.info(f"增量订单报表发送完成: 成功 {success_count}, 失败 {fail_count}")
        logger.info("=" * 60)
        logger.info("增量订单报表生成任务执行完成")
        logger.info("=" * 60)
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"发送增量订单报表失败: {e}", exc_info=True)
        logger.error("=" * 60)
        # 发送错误通知给管理员
        try:
            from config import ADMIN_IDS

            for admin_id in ADMIN_IDS:
                try:
                    await bot.send_message(
                        chat_id=admin_id,
                        text=f"❌ 增量订单报表生成失败\n\n错误: {str(e)}\n\n请检查日志获取详细信息",
                    )
                except Exception as notify_error:
                    logger.error(
                        f"发送错误通知给管理员 {admin_id} 失败: {notify_error}", exc_info=True
                    )
        except Exception as notify_error:
            logger.error(f"发送错误通知失败: {notify_error}", exc_info=True)


async def setup_incremental_orders_report(bot):
    """设置增量订单报表定时任务（每天23:05执行）"""
    global scheduler

    if scheduler is None:
        scheduler = AsyncIOScheduler()
        scheduler.start()

    try:
        scheduler.add_job(
            send_incremental_orders_report,
            trigger=CronTrigger(hour=23, minute=5, timezone=BEIJING_TZ),
            args=[bot],
            id="incremental_orders_report",
            replace_existing=True,
        )
        logger.info("已设置增量订单报表任务: 每天 23:05 自动发送")
    except Exception as e:
        logger.error(f"设置增量订单报表任务失败: {e}", exc_info=True)


async def save_daily_balance(bot):
    """每天11点统计并保存GCASH和PayMaya账户的总余额"""
    try:
        # 获取当前日期（北京时区）
        now = datetime.now(BEIJING_TZ)
        date_str = now.strftime("%Y-%m-%d")

        logger.info(f"开始统计并保存 {date_str} 的账户余额...")

        # 获取所有账户
        accounts = await db_operations.get_all_payment_accounts()

        if not accounts:
            logger.warning("没有找到任何支付账户")
            return

        # 统计总余额
        gcash_total = 0.0
        paymaya_total = 0.0
        saved_count = 0

        for account in accounts:
            account_id = account.get("id")
            account_type = account.get("account_type", "").lower()
            balance = account.get("balance", 0) or 0.0

            # 只处理GCASH和PayMaya账户
            if account_type in ("gcash", "paymaya"):
                # 保存余额历史
                await db_operations.record_payment_balance_history(
                    account_id=account_id, account_type=account_type, balance=balance, date=date_str
                )
                saved_count += 1

                # 累加总余额
                if account_type == "gcash":
                    gcash_total += balance
                elif account_type == "paymaya":
                    paymaya_total += balance

        total = gcash_total + paymaya_total

        logger.info(
            f"余额统计完成 - 日期: {date_str}, "
            f"GCASH: {gcash_total:,.2f}, "
            f"PayMaya: {paymaya_total:,.2f}, "
            f"总计: {total:,.2f}, "
            f"已保存 {saved_count} 个账户"
        )

    except Exception as e:
        logger.error(f"保存每日余额失败: {e}", exc_info=True)


async def setup_daily_balance_save(bot):
    """设置每日余额统计任务（每天11:00执行）"""
    global scheduler

    if scheduler is None:
        scheduler = AsyncIOScheduler()
        scheduler.start()

    try:
        scheduler.add_job(
            save_daily_balance,
            trigger=CronTrigger(hour=11, minute=0, timezone=BEIJING_TZ),
            args=[bot],
            id="daily_balance_save",
            replace_existing=True,
        )
        logger.info("已设置每日余额统计任务: 每天 11:00 自动保存")
    except Exception as e:
        logger.error(f"设置每日余额统计任务失败: {e}", exc_info=True)
