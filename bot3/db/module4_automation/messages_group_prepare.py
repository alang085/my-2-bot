"""群组消息配置 - 字段准备模块

包含准备字段更新字典的逻辑。
"""

from typing import Any, Dict, Optional


def prepare_field_updates(
    chat_title: Optional[str] = None,
    start_work_message: Optional[str] = None,
    end_work_message: Optional[str] = None,
    welcome_message: Optional[str] = None,
    bot_links: Optional[str] = None,
    worker_links: Optional[str] = None,
    is_active: Optional[int] = None,
    **kwargs,
) -> Dict[str, Any]:
    """准备字段更新字典

    Args:
        chat_title: 群组标题
        start_work_message: 开始工作消息
        end_work_message: 结束工作消息
        welcome_message: 欢迎消息
        bot_links: 机器人链接
        worker_links: 员工链接
        is_active: 是否激活
        **kwargs: 其他字段（新字段）

    Returns:
        Dict: 字段更新字典
    """
    from db.module4_automation.messages_group_prepare_helpers import \
        _prepare_standard_fields

    # 处理标准字段参数
    field_updates = _prepare_standard_fields(
        chat_title,
        start_work_message,
        end_work_message,
        welcome_message,
        bot_links,
        worker_links,
        is_active,
    )

    # 处理新字段（通过kwargs）
    field_updates.update(kwargs)

    return field_updates
