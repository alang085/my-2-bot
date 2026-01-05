"""群组消息配置 - 新字段更新模块

包含更新新字段的逻辑。
"""

from typing import Any, Dict

from db.module4_automation.messages_group_fields import get_new_field_names
from db.module4_automation.messages_group_update import build_update_query


def update_new_fields_after_create(
    cursor, chat_id: int, new_fields: Dict[str, Any]
) -> bool:
    """创建后更新新字段

    Args:
        cursor: 数据库游标
        chat_id: 群组ID
        new_fields: 新字段字典

    Returns:
        bool: 是否更新成功
    """
    if not new_fields:
        return False

    valid_field_names = get_new_field_names()
    updates, params = build_update_query(new_fields, valid_field_names)

    if not updates:
        return False

    params.append(chat_id)

    cursor.execute(
        f"""
        UPDATE group_message_config
        SET {', '.join(updates)}
        WHERE chat_id = ?
        """,
        params,
    )
    return cursor.rowcount > 0
