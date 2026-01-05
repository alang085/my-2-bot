"""群组消息配置 - 更新模块

包含更新现有配置的逻辑。
"""

import logging
from typing import Any, Dict

from db.module4_automation.messages_group_fields import get_new_field_names

logger = logging.getLogger(__name__)


def build_update_query(
    field_updates: Dict[str, Any], valid_field_names: list
) -> tuple[list[str], list[Any]]:
    """构建更新查询的字段和参数

    Args:
        field_updates: 字段更新字典
        valid_field_names: 有效字段名列表

    Returns:
        tuple: (更新字段列表, 参数列表)
    """
    updates = []
    params = []
    for field_name, value in field_updates.items():
        if field_name not in valid_field_names:
            logger.warning(f"跳过无效的群组消息配置字段名: {field_name}")
            continue
        updates.append(f"{field_name} = ?")
        params.append(value)

    return updates, params


def update_existing_config(
    cursor, chat_id: int, field_updates: Dict[str, Any], valid_field_names: list
) -> bool:
    """更新现有配置

    Args:
        cursor: 数据库游标
        chat_id: 群组ID
        field_updates: 字段更新字典
        valid_field_names: 有效字段名列表

    Returns:
        bool: 是否更新成功
    """
    if not field_updates:
        return False

    updates, params = build_update_query(field_updates, valid_field_names)

    if not updates:
        return False

    updates.append("updated_at = CURRENT_TIMESTAMP")
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
