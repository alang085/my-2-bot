"""群组消息配置 - 创建模块

包含创建新配置的逻辑。
"""

from typing import Any, Dict


def create_new_config(cursor, chat_id: int, field_updates: Dict[str, Any]) -> bool:
    """创建新配置

    Args:
        cursor: 数据库游标
        chat_id: 群组ID
        field_updates: 字段更新字典

    Returns:
        bool: 是否创建成功
    """
    cursor.execute(
        """
        INSERT INTO group_message_config (
            chat_id, chat_title, start_work_message, end_work_message,
            welcome_message, bot_links, worker_links, is_active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            chat_id,
            field_updates.get("chat_title") or "",
            field_updates.get("start_work_message") or "",
            field_updates.get("end_work_message") or "",
            field_updates.get("welcome_message") or "",
            field_updates.get("bot_links") or "",
            field_updates.get("worker_links") or "",
            field_updates.get("is_active", 1),
        ),
    )
    return cursor.rowcount > 0
