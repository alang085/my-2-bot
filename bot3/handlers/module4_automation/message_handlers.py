"""
消息处理器（向后兼容层）

此文件保留用于向后兼容，实际功能已拆分到：
- chat_event_handlers.py - 群组事件处理
- text_input_handlers.py - 文本输入主路由
- text_input_helpers.py - 文本输入辅助函数
"""

# 向后兼容导入
from handlers.module4_automation.chat_event_handlers import (
    handle_new_chat_members, handle_new_chat_title)
from handlers.module4_automation.text_input_handlers import handle_text_input

# 导出所有函数以保持向后兼容
__all__ = [
    "handle_new_chat_members",
    "handle_new_chat_title",
    "handle_text_input",
]
