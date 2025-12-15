"""定时播报执行器"""
# 标准库
import asyncio
import logging
from datetime import datetime, time as dt_time

# 第三方库
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# 本地模块
import db_operations
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# 北京时区
BEIJING_TZ = pytz.timezone('Asia/Shanghai')

logger = logging.getLogger(__name__)

# 全局调度器
scheduler = None


async def send_scheduled_broadcast(bot, broadcast):
    """发送定时播报"""
    try:
        chat_id = broadcast['chat_id']
        message = broadcast['message']
        
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
            time_str = broadcast['time']
            # 解析时间 (HH:MM 或 HH)
            time_parts = time_str.split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1]) if len(time_parts) > 1 else 0
            
            # 创建定时任务（每天执行）
            job_id = f"broadcast_{broadcast['slot']}"
            
            scheduler.add_job(
                send_scheduled_broadcast,
                trigger=CronTrigger(hour=hour, minute=minute, timezone=BEIJING_TZ),
                args=[bot, broadcast],
                id=job_id,
                replace_existing=True
            )
            
            logger.info(f"已设置定时播报 {broadcast['slot']}: 每天 {time_str} 发送到群组 {broadcast['chat_id']}")
        except Exception as e:
            logger.error(f"设置定时播报 {broadcast['slot']} 失败: {e}", exc_info=True)


async def reload_scheduled_broadcasts(bot):
    """重新加载定时播报任务"""
    await setup_scheduled_broadcasts(bot)


async def send_daily_report(bot):
    """发送日切报表Excel文件给所有管理员（每天生成两个Excel：订单总表和每日变化数据）"""
    try:
        from utils.date_helpers import get_daily_period_date
        from config import ADMIN_IDS
        import db_operations
        
        # 获取日切日期（使用get_daily_period_date，因为日切是在23:00后）
        # 如果当前时间在23:00之后，get_daily_period_date会返回明天的日期
        # 但我们需要统计的是今天的数据，所以需要减一天
        from datetime import datetime, timedelta
        import pytz
        tz = pytz.timezone('Asia/Shanghai')
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
                valid_orders,
                completed_orders,
                breach_end_orders,
                daily_interest,
                daily_summary
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
        
        # 发送给所有管理员
        success_count = 0
        fail_count = 0
        for admin_id in ADMIN_IDS:
            try:
                # 发送订单总表Excel
                if orders_excel_path:
                    with open(orders_excel_path, 'rb') as f:
                        await bot.send_document(
                            chat_id=admin_id,
                            document=f,
                            filename=f"订单总表_{report_date}.xlsx",
                            caption=f"📊 订单总表 ({report_date})\n\n包含所有有效订单及利息记录"
                        )
                
                # 发送每日变化数据Excel
                if changes_excel_path:
                    with open(changes_excel_path, 'rb') as f:
                        await bot.send_document(
                            chat_id=admin_id,
                            document=f,
                            filename=f"每日变化数据_{report_date}.xlsx",
                            caption=f"📈 每日变化数据 ({report_date})\n\n包含：\n• 新增订单\n• 完成订单\n• 违约完成订单\n• 收入明细（利息等）\n• 开销明细\n• 数据汇总"
                        )
                
                success_count += 1
                logger.info(f"每日Excel报表已发送给管理员 {admin_id}")
            except Exception as e:
                fail_count += 1
                logger.error(f"发送每日Excel报表给管理员 {admin_id} 失败: {e}", exc_info=True)
        
        # 清理临时文件
        import os
        for file_path in [orders_excel_path, changes_excel_path]:
            if file_path:
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.warning(f"删除临时文件失败 {file_path}: {e}")
        
        logger.info(f"每日Excel报表发送完成: 成功 {success_count}, 失败 {fail_count}")
    except Exception as e:
        logger.error(f"发送每日Excel报表失败: {e}", exc_info=True)


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
            replace_existing=True
        )
        logger.info("已设置日切报表任务: 每天 23:05 自动发送")
    except Exception as e:
        logger.error(f"设置日切报表任务失败: {e}", exc_info=True)


async def send_start_work_messages(bot):
    """发送开工信息到所有配置的总群"""
    try:
        configs = await db_operations.get_group_message_configs()
        
        if not configs:
            logger.info("没有配置的总群，跳过发送开工信息")
            return
        
        success_count = 0
        fail_count = 0
        
        for config in configs:
            chat_id = config.get('chat_id')
            message = config.get('start_work_message')
            
            if not chat_id or not message:
                continue
            
            try:
                await bot.send_message(chat_id=chat_id, text=message)
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
            replace_existing=True
        )
        logger.info("已设置开工信息任务: 每天 11:00 自动发送")
    except Exception as e:
        logger.error(f"设置开工信息任务失败: {e}", exc_info=True)


async def send_end_work_messages(bot):
    """发送收工信息到所有配置的总群"""
    try:
        configs = await db_operations.get_group_message_configs()
        
        if not configs:
            logger.info("没有配置的总群，跳过发送收工信息")
            return
        
        success_count = 0
        fail_count = 0
        
        for config in configs:
            chat_id = config.get('chat_id')
            message = config.get('end_work_message')
            
            if not chat_id or not message:
                continue
            
            try:
                await bot.send_message(chat_id=chat_id, text=message)
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
            replace_existing=True
        )
        logger.info("已设置收工信息任务: 每天 23:00 自动发送")
    except Exception as e:
        logger.error(f"设置收工信息任务失败: {e}", exc_info=True)


async def send_random_announcements(bot):
    """随机发送公司公告到所有配置的总群"""
    try:
        import random
        from datetime import datetime, timedelta
        import pytz
        
        # 检查发送计划配置
        schedule = await db_operations.get_announcement_schedule()
        if not schedule or not schedule.get('is_active'):
            logger.info("公告发送功能未激活，跳过发送")
            return
        
        # 检查发送间隔
        last_sent_at = schedule.get('last_sent_at')
        interval_hours = schedule.get('interval_hours', 3)
        
        if last_sent_at:
            tz = pytz.timezone('Asia/Shanghai')
            last_sent = datetime.strptime(last_sent_at, '%Y-%m-%d %H:%M:%S')
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
        message = selected_announcement.get('message')
        
        if not message:
            logger.warning("选中的公告消息为空，跳过发送")
            return
        
        # 获取所有配置的总群
        configs = await db_operations.get_group_message_configs()
        
        if not configs:
            logger.info("没有配置的总群，跳过发送公告")
            return
        
        success_count = 0
        fail_count = 0
        
        for config in configs:
            chat_id = config.get('chat_id')
            
            if not chat_id:
                continue
            
            try:
                await bot.send_message(chat_id=chat_id, text=message)
                success_count += 1
                logger.info(f"公司公告已发送到群组 {chat_id}")
            except Exception as e:
                fail_count += 1
                logger.error(f"发送公司公告到群组 {chat_id} 失败: {e}", exc_info=True)
        
        # 更新最后发送时间
        await db_operations.update_announcement_last_sent()
        
        logger.info(f"公司公告发送完成: 成功 {success_count}, 失败 {fail_count}")
    except Exception as e:
        logger.error(f"发送公司公告失败: {e}", exc_info=True)


async def setup_announcement_schedule(bot):
    """设置公告定时任务（按配置的间隔执行）"""
    global scheduler
    
    if scheduler is None:
        scheduler = AsyncIOScheduler()
        scheduler.start()
    
    try:
        from apscheduler.triggers.interval import IntervalTrigger
        
        # 获取配置的间隔
        schedule = await db_operations.get_announcement_schedule()
        interval_hours = schedule.get('interval_hours', 3) if schedule else 3
        
        scheduler.add_job(
            send_random_announcements,
            trigger=IntervalTrigger(hours=interval_hours),
            args=[bot],
            id="random_announcements",
            replace_existing=True
        )
        logger.info(f"已设置公司公告任务: 每 {interval_hours} 小时自动发送")
    except Exception as e:
        logger.error(f"设置公司公告任务失败: {e}", exc_info=True)


async def send_incremental_orders_report(bot):
    """发送增量订单报表（每天11:05执行）"""
    try:
        from utils.incremental_report_generator import (
            get_or_create_baseline_date,
            prepare_incremental_data
        )
        from utils.excel_export import export_incremental_orders_report_to_excel
        from config import ADMIN_IDS
        
        # 获取或创建基准日期
        baseline_date = await get_or_create_baseline_date()
        current_date = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d')
        
        logger.info(f"开始生成增量订单报表 (基准日期: {baseline_date}, 当前日期: {current_date})")
        
        # 准备增量数据
        incremental_data = await prepare_incremental_data(baseline_date)
        orders_data = incremental_data.get('orders', [])
        expense_records = incremental_data.get('expenses', [])
        
        if not orders_data and not expense_records:
            # 没有增量数据，发送提示消息
            for admin_id in ADMIN_IDS:
                try:
                    await bot.send_message(
                        chat_id=admin_id,
                        text=f"📊 增量订单报表 ({current_date})\n\n"
                             f"基准日期: {baseline_date}\n"
                             f"当前日期: {current_date}\n\n"
                             f"✅ 无增量数据"
                    )
                except Exception as e:
                    logger.error(f"发送增量报表提示给管理员 {admin_id} 失败: {e}", exc_info=True)
            return
        
        # 生成Excel报表
        try:
            excel_path = await export_incremental_orders_report_to_excel(
                baseline_date,
                current_date,
                orders_data,
                expense_records
            )
            logger.info(f"增量订单报表Excel已生成: {excel_path}")
        except Exception as e:
            logger.error(f"生成增量订单报表Excel失败: {e}", exc_info=True)
            excel_path = None
        
        # 发送给所有管理员
        success_count = 0
        fail_count = 0
        for admin_id in ADMIN_IDS:
            try:
                if excel_path:
                    # 检查是否已经合并过
                    merge_record = await db_operations.get_merge_record(current_date)
                    if merge_record:
                        # 已经合并过，显示提示
                        merge_button_text = "⚠️ 已合并（再次合并）"
                    else:
                        # 未合并，显示合并按钮
                        merge_button_text = "✅ 合并到总表"
                    
                    keyboard = [[
                        InlineKeyboardButton(
                            merge_button_text,
                            callback_data=f"merge_incremental_{current_date}"
                        )
                    ]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    with open(excel_path, 'rb') as f:
                        await bot.send_document(
                            chat_id=admin_id,
                            document=f,
                            filename=f"增量订单报表_{current_date}.xlsx",
                            caption=f"📊 增量订单报表 ({current_date})\n\n"
                                   f"基准日期: {baseline_date}\n"
                                   f"订单数: {len(orders_data)}\n"
                                   f"开销记录: {len(expense_records)}\n\n"
                                   f"💡 提示：点击利息总数列可以展开查看每期利息明细",
                            reply_markup=reply_markup
                        )
                else:
                    await bot.send_message(
                        chat_id=admin_id,
                        text=f"📊 增量订单报表 ({current_date})\n\n"
                             f"基准日期: {baseline_date}\n"
                             f"订单数: {len(orders_data)}\n"
                             f"开销记录: {len(expense_records)}\n\n"
                             f"❌ Excel生成失败，请查看日志"
                    )
                
                success_count += 1
                logger.info(f"增量订单报表已发送给管理员 {admin_id}")
            except Exception as e:
                fail_count += 1
                logger.error(f"发送增量订单报表给管理员 {admin_id} 失败: {e}", exc_info=True)
        
        # 清理临时文件
        if excel_path:
            import os
            try:
                os.remove(excel_path)
            except Exception as e:
                logger.warning(f"删除临时文件失败 {excel_path}: {e}")
        
        logger.info(f"增量订单报表发送完成: 成功 {success_count}, 失败 {fail_count}")
    except Exception as e:
        logger.error(f"发送增量订单报表失败: {e}", exc_info=True)


async def setup_incremental_orders_report(bot):
    """设置增量订单报表定时任务（每天11:05执行）"""
    global scheduler
    
    if scheduler is None:
        scheduler = AsyncIOScheduler()
        scheduler.start()
    
    try:
        scheduler.add_job(
            send_incremental_orders_report,
            trigger=CronTrigger(hour=11, minute=5, timezone=BEIJING_TZ),
            args=[bot],
            id="incremental_orders_report",
            replace_existing=True
        )
        logger.info("已设置增量订单报表任务: 每天 11:05 自动发送")
    except Exception as e:
        logger.error(f"设置增量订单报表任务失败: {e}", exc_info=True)

