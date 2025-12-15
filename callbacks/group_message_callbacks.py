"""群组消息回调处理器"""
# 标准库
import logging

# 第三方库
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# 本地模块
import db_operations
from decorators import authorized_required

logger = logging.getLogger(__name__)


@authorized_required
async def handle_group_message_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理群组消息相关的回调"""
    query = update.callback_query
    if not query:
        return

    data = query.data
    if not data:
        return

    try:
        await query.answer()
    except Exception:
        pass

    if data == "groupmsg_refresh":
        from handlers.group_message_handlers import manage_group_messages
        await manage_group_messages(update, context)

    elif data == "groupmsg_add":
        await query.message.reply_text(
            "请输入群组ID：\n"
            "格式: 数字（如：-1001234567890）\n"
            "输入 'cancel' 取消\n\n"
            "💡 提示：在群组中使用 /groupmsg_getid 获取群组ID"
        )
        context.user_data['state'] = 'ADDING_GROUP_CONFIG'
        await query.answer()

    elif data == "groupmsg_set_message":
        # 显示选择总群的界面
        configs = await db_operations.get_group_message_configs()
        
        if not configs:
            await query.answer("❌ 没有配置的总群，请先添加", show_alert=True)
            return
        
        keyboard = []
        for config in configs:
            chat_id = config.get('chat_id')
            chat_title = config.get('chat_title', f'ID: {chat_id}')
            keyboard.append([
                InlineKeyboardButton(
                    chat_title,
                    callback_data=f"groupmsg_select_{chat_id}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("🔙 返回", callback_data="groupmsg_refresh")
        ])
        
        await query.edit_message_text(
            "📝 选择要设置消息的总群：",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("groupmsg_select_"):
        try:
            chat_id = int(data.split("_")[-1])
            config = await db_operations.get_group_message_config_by_chat_id(chat_id)
            
            if not config:
                await query.answer("❌ 配置不存在", show_alert=True)
                return
            
            chat_title = config.get('chat_title', f'ID: {chat_id}')
            
            keyboard = [
                [
                    InlineKeyboardButton(
                        "🌅 设置开工信息",
                        callback_data=f"groupmsg_set_start_{chat_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🌙 设置收工信息",
                        callback_data=f"groupmsg_set_end_{chat_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "👋 设置欢迎信息",
                        callback_data=f"groupmsg_set_welcome_{chat_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔙 返回",
                        callback_data="groupmsg_set_message"
                    )
                ]
            ]
            
            await query.edit_message_text(
                f"📝 设置消息内容\n\n"
                f"总群: {chat_title}\n"
                f"群组ID: {chat_id}\n\n"
                f"请选择要设置的消息类型：",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except (ValueError, IndexError):
            await query.answer("❌ 无效的群组ID", show_alert=True)

    elif data.startswith("groupmsg_set_start_"):
        try:
            chat_id = int(data.split("_")[-1])
            context.user_data['setting_message_chat_id'] = chat_id
            context.user_data['setting_message_type'] = 'start_work'
            
            await query.message.reply_text(
                "请输入开工信息：\n"
                "输入 'cancel' 取消"
            )
            context.user_data['state'] = 'SETTING_GROUP_MESSAGE'
            await query.answer()
        except (ValueError, IndexError):
            await query.answer("❌ 无效的群组ID", show_alert=True)

    elif data.startswith("groupmsg_set_end_"):
        try:
            chat_id = int(data.split("_")[-1])
            context.user_data['setting_message_chat_id'] = chat_id
            context.user_data['setting_message_type'] = 'end_work'
            
            await query.message.reply_text(
                "请输入收工信息：\n"
                "输入 'cancel' 取消"
            )
            context.user_data['state'] = 'SETTING_GROUP_MESSAGE'
            await query.answer()
        except (ValueError, IndexError):
            await query.answer("❌ 无效的群组ID", show_alert=True)

    elif data.startswith("groupmsg_set_welcome_"):
        try:
            chat_id = int(data.split("_")[-1])
            context.user_data['setting_message_chat_id'] = chat_id
            context.user_data['setting_message_type'] = 'welcome'
            
            await query.message.reply_text(
                "请输入欢迎信息：\n"
                "支持变量：{username} - 用户名，{chat_title} - 群组名称\n"
                "输入 'cancel' 取消"
            )
            context.user_data['state'] = 'SETTING_GROUP_MESSAGE'
            await query.answer()
        except (ValueError, IndexError):
            await query.answer("❌ 无效的群组ID", show_alert=True)

    elif data == "announcement_refresh":
        from handlers.group_message_handlers import manage_announcements
        await manage_announcements(update, context)

    elif data == "announcement_add":
        await query.message.reply_text(
            "请输入公告内容：\n"
            "输入 'cancel' 取消"
        )
        context.user_data['state'] = 'ADDING_ANNOUNCEMENT'
        await query.answer()

    elif data == "announcement_list":
        announcements = await db_operations.get_all_company_announcements()
        
        if not announcements:
            await query.answer("❌ 没有公告", show_alert=True)
            return
        
        msg = "📋 所有公告列表\n\n"
        for ann in announcements:
            ann_id = ann.get('id')
            message = ann.get('message', '')
            is_active = ann.get('is_active', 0)
            status = "✅" if is_active else "❌"
            
            msg += f"{status} [{ann_id}] {message}\n\n"
        
        keyboard = []
        for ann in announcements:
            ann_id = ann.get('id')
            is_active = ann.get('is_active', 0)
            action = "禁用" if is_active else "启用"
            keyboard.append([
                InlineKeyboardButton(
                    f"{'✅' if is_active else '❌'} [{ann_id}] {action}",
                    callback_data=f"announcement_toggle_{ann_id}"
                ),
                InlineKeyboardButton(
                    "🗑️ 删除",
                    callback_data=f"announcement_delete_{ann_id}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("🔙 返回", callback_data="announcement_refresh")
        ])
        
        await query.edit_message_text(
            msg,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("announcement_toggle_"):
        try:
            ann_id = int(data.split("_")[-1])
            ann = await db_operations.get_all_company_announcements()
            current = next((a for a in ann if a.get('id') == ann_id), None)
            
            if not current:
                await query.answer("❌ 公告不存在", show_alert=True)
                return
            
            new_status = 0 if current.get('is_active') else 1
            success = await db_operations.toggle_company_announcement(ann_id, new_status)
            
            if success:
                await query.answer("✅ 状态已更新")
                # 刷新列表
                await handle_group_message_callback(update, context)
            else:
                await query.answer("❌ 更新失败", show_alert=True)
        except (ValueError, IndexError):
            await query.answer("❌ 无效的公告ID", show_alert=True)

    elif data.startswith("announcement_delete_"):
        try:
            ann_id = int(data.split("_")[-1])
            success = await db_operations.delete_company_announcement(ann_id)
            
            if success:
                await query.answer("✅ 公告已删除")
                # 刷新列表
                await handle_group_message_callback(update, context)
            else:
                await query.answer("❌ 删除失败", show_alert=True)
        except (ValueError, IndexError):
            await query.answer("❌ 无效的公告ID", show_alert=True)

    elif data == "announcement_set_interval":
        await query.message.reply_text(
            "请输入发送间隔（小时）：\n"
            "格式: 数字（如：3 表示每3小时发送一次）\n"
            "输入 'cancel' 取消"
        )
        context.user_data['state'] = 'SETTING_ANNOUNCEMENT_INTERVAL'
        await query.answer()

