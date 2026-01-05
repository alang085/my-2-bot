"""群组消息配置字段准备辅助函数

包含字段准备逻辑的辅助函数。
"""

from typing import Any, Dict, Optional


def _prepare_standard_fields(
    chat_title: Optional[str] = None,
    start_work_message: Optional[str] = None,
    end_work_message: Optional[str] = None,
    welcome_message: Optional[str] = None,
    bot_links: Optional[str] = None,
    worker_links: Optional[str] = None,
    is_active: Optional[int] = None,
) -> Dict[str, Any]:
    """准备标准字段更新字典

    Args:
        chat_title: 群组标题
        start_work_message: 开始工作消息
        end_work_message: 结束工作消息
        welcome_message: 欢迎消息
        bot_links: 机器人链接
        worker_links: 员工链接
        is_active: 是否激活

    Returns:
        Dict: 字段更新字典
    """
    # 使用字典映射简化多个if语句，降低复杂度
    field_mapping = {
        "chat_title": chat_title,
        "start_work_message": start_work_message,
        "end_work_message": end_work_message,
        "welcome_message": welcome_message,
        "bot_links": bot_links,
        "worker_links": worker_links,
        "is_active": is_active,
    }

    # 过滤None值，只保留非None的字段
    return {key: value for key, value in field_mapping.items() if value is not None}
