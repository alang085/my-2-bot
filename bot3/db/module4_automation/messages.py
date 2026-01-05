"""消息配置操作模块（向后兼容层）

此文件保留用于向后兼容，实际功能已拆分到：
- messages_schedule.py - 定时播报操作
- messages_group.py - 群组消息配置操作
- messages_announcement.py - 公司公告操作
- messages_anti_fraud.py - 防诈骗语录操作
- messages_promotion.py - 公司宣传轮播语录操作
- messages_work.py - 开工收工消息操作
"""

# 向后兼容导入 - 从拆分后的文件导入所有函数
from db.module4_automation.messages_announcement import (
    delete_company_announcement, get_all_company_announcements,
    get_announcement_schedule, get_company_announcements,
    save_announcement_schedule, save_company_announcement,
    toggle_company_announcement, update_announcement_last_sent)
from db.module4_automation.messages_anti_fraud import (
    delete_anti_fraud_message, get_active_anti_fraud_messages,
    get_all_anti_fraud_messages, save_anti_fraud_message,
    toggle_anti_fraud_message)
from db.module4_automation.messages_group import (
    delete_group_message_config, get_group_message_config_by_chat_id,
    get_group_message_configs, save_group_message_config)
from db.module4_automation.messages_promotion import (
    delete_promotion_message, get_active_promotion_messages,
    get_all_promotion_messages, get_promotion_schedule, save_promotion_message,
    toggle_promotion_message)
from db.module4_automation.messages_schedule import (
    create_or_update_scheduled_broadcast, delete_scheduled_broadcast,
    get_active_scheduled_broadcasts, get_all_scheduled_broadcasts,
    get_scheduled_broadcast, toggle_scheduled_broadcast)
from db.module4_automation.messages_work import (
    delete_end_work_message, delete_start_work_message,
    get_active_end_work_messages, get_active_start_work_messages,
    get_all_end_work_messages, get_all_start_work_messages,
    get_end_work_message_by_weekday, get_start_work_message_by_weekday,
    save_end_work_message, save_start_work_message, toggle_end_work_message,
    toggle_start_work_message)

# 导出所有函数以保持向后兼容
__all__ = [
    # 定时播报
    "get_scheduled_broadcast",
    "get_all_scheduled_broadcasts",
    "get_active_scheduled_broadcasts",
    "create_or_update_scheduled_broadcast",
    "delete_scheduled_broadcast",
    "toggle_scheduled_broadcast",
    # 群组消息配置
    "get_group_message_configs",
    "get_group_message_config_by_chat_id",
    "save_group_message_config",
    "delete_group_message_config",
    # 公司公告
    "get_company_announcements",
    "get_all_company_announcements",
    "save_company_announcement",
    "delete_company_announcement",
    "toggle_company_announcement",
    "get_announcement_schedule",
    "save_announcement_schedule",
    "update_announcement_last_sent",
    # 防诈骗语录
    "get_active_anti_fraud_messages",
    "get_all_anti_fraud_messages",
    "save_anti_fraud_message",
    "delete_anti_fraud_message",
    "toggle_anti_fraud_message",
    # 公司宣传轮播语录
    "get_active_promotion_messages",
    "get_all_promotion_messages",
    "save_promotion_message",
    "delete_promotion_message",
    "toggle_promotion_message",
    "get_promotion_schedule",
    # 开工消息
    "get_start_work_message_by_weekday",
    "get_all_start_work_messages",
    "get_active_start_work_messages",
    "save_start_work_message",
    "delete_start_work_message",
    "toggle_start_work_message",
    # 收工消息
    "get_end_work_message_by_weekday",
    "get_all_end_work_messages",
    "get_active_end_work_messages",
    "save_end_work_message",
    "delete_end_work_message",
    "toggle_end_work_message",
]
