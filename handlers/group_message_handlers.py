"""群组消息管理处理器"""
# 标准库
import logging

# 第三方库
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# 本地模块
import db_operations
from decorators import error_handler, admin_required, private_chat_only

logger = logging.getLogger(__name__)


@error_handler
@private_chat_only
@admin_required
async def manage_group_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """管理群组消息配置"""
    try:
        configs = await db_operations.get_group_message_configs()
        
        msg = "📢 群组消息管理\n\n"
        
        if not configs:
            msg += "❌ 当前没有配置的总群\n\n"
            msg += "使用 /groupmsg_add <chat_id> 添加总群"
        else:
            msg += "已配置的总群：\n\n"
            for config in configs:
                chat_id = config.get('chat_id')
                chat_title = config.get('chat_title', '未设置')
                is_active = config.get('is_active', 0)
                status = "✅ 启用" if is_active else "❌ 禁用"
                
                msg += f"📌 {chat_title} (ID: {chat_id})\n"
                msg += f"   状态: {status}\n"
                msg += f"   开工信息: {'已设置' if config.get('start_work_message') else '未设置'}\n"
                msg += f"   收工信息: {'已设置' if config.get('end_work_message') else '未设置'}\n"
                msg += f"   欢迎信息: {'已设置' if config.get('welcome_message') else '未设置'}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("➕ 添加总群", callback_data="groupmsg_add")],
            [InlineKeyboardButton("📝 设置消息", callback_data="groupmsg_set_message")],
            [InlineKeyboardButton("🔄 刷新", callback_data="groupmsg_refresh")]
        ]
        
        await update.message.reply_text(
            msg,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"显示群组消息管理失败: {e}", exc_info=True)
        await update.message.reply_text(f"❌ 显示失败: {e}")


@error_handler
@private_chat_only
@admin_required
async def add_group_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """添加总群配置"""
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "请输入群组ID\n"
            "格式: /groupmsg_add <chat_id>\n"
            "示例: /groupmsg_add -1001234567890\n\n"
            "💡 提示：可以在群组中使用 /groupmsg_getid 获取群组ID"
        )
        return
    
    try:
        chat_id = int(context.args[0])
        
        # 尝试获取群组信息
        try:
            chat = await context.bot.get_chat(chat_id)
            chat_title = chat.title or '未设置'
        except:
            chat_title = '未设置'
        
        # 保存配置
        success = await db_operations.save_group_message_config(
            chat_id=chat_id,
            chat_title=chat_title,
            is_active=1
        )
        
        if success:
            await update.message.reply_text(
                f"✅ 总群配置已添加\n\n"
                f"群组ID: {chat_id}\n"
                f"群组名称: {chat_title}\n\n"
                f"请使用 /groupmsg_set_message 设置消息内容"
            )
        else:
            await update.message.reply_text("❌ 添加失败，可能已存在")
    except ValueError:
        await update.message.reply_text("❌ 群组ID必须是数字")
    except Exception as e:
        logger.error(f"添加总群配置失败: {e}", exc_info=True)
        await update.message.reply_text(f"❌ 添加失败: {e}")


@error_handler
@private_chat_only
@admin_required
async def get_group_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """获取当前群组ID（在群组中使用）"""
    chat = update.effective_chat
    
    if chat.type == "private":
        await update.message.reply_text("❌ 此命令只能在群组中使用")
        return
    
    await update.message.reply_text(
        f"📌 群组信息\n\n"
        f"群组名称: {chat.title}\n"
        f"群组ID: `{chat.id}`\n\n"
        f"复制上面的ID，在私聊中使用 /groupmsg_add {chat.id} 添加配置",
        parse_mode='Markdown'
    )


@error_handler
@private_chat_only
@admin_required
async def manage_announcements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """管理公司公告"""
    try:
        announcements = await db_operations.get_all_company_announcements()
        schedule = await db_operations.get_announcement_schedule()
        
        msg = "📢 公司公告管理\n\n"
        
        if schedule:
            interval_hours = schedule.get('interval_hours', 3)
            is_active = schedule.get('is_active', 0)
            status = "✅ 启用" if is_active else "❌ 禁用"
            msg += f"发送间隔: {interval_hours} 小时\n"
            msg += f"状态: {status}\n\n"
        
        if not announcements:
            msg += "❌ 当前没有公告\n\n"
            msg += "使用 /announcement_add <消息内容> 添加公告"
        else:
            msg += f"公告列表（共 {len(announcements)} 条）：\n\n"
            active_count = sum(1 for a in announcements if a.get('is_active'))
            msg += f"激活: {active_count} 条\n\n"
            
            for ann in announcements[:10]:  # 只显示前10条
                ann_id = ann.get('id')
                message = ann.get('message', '')
                is_active = ann.get('is_active', 0)
                status = "✅" if is_active else "❌"
                
                # 截断长消息
                display_msg = message[:50] + "..." if len(message) > 50 else message
                msg += f"{status} [{ann_id}] {display_msg}\n"
            
            if len(announcements) > 10:
                msg += f"\n... 还有 {len(announcements) - 10} 条公告"
        
        keyboard = [
            [InlineKeyboardButton("➕ 添加公告", callback_data="announcement_add")],
            [InlineKeyboardButton("📋 查看全部", callback_data="announcement_list")],
            [InlineKeyboardButton("⚙️ 设置间隔", callback_data="announcement_set_interval")],
            [InlineKeyboardButton("🔄 刷新", callback_data="announcement_refresh")]
        ]
        
        await update.message.reply_text(
            msg,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"显示公告管理失败: {e}", exc_info=True)
        await update.message.reply_text(f"❌ 显示失败: {e}")

