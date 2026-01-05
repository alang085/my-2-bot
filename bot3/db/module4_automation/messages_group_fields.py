"""群组消息配置 - 字段验证模块

包含获取有效字段名列表的逻辑。
"""

from typing import List


def get_valid_field_names() -> List[str]:
    """获取所有有效的字段名列表（包括新旧字段）

    Returns:
        List[str]: 有效字段名列表
    """
    valid_field_names = [
        "chat_title",
        "start_work_message",
        "end_work_message",
        "welcome_message",
        "bot_links",
        "worker_links",
        "is_active",
        "updated_at",
    ]
    # 添加所有新字段（28个）
    for prefix in [
        "start_work_message",
        "end_work_message",
        "welcome_message",
        "anti_fraud_message",
    ]:
        for i in range(1, 8):
            valid_field_names.append(f"{prefix}_{i}")

    return valid_field_names


def get_new_field_names() -> List[str]:
    """获取新字段名列表（不包括基本字段）

    Returns:
        List[str]: 新字段名列表
    """
    valid_field_names = []
    for prefix in [
        "start_work_message",
        "end_work_message",
        "welcome_message",
        "anti_fraud_message",
    ]:
        for i in range(1, 8):
            valid_field_names.append(f"{prefix}_{i}")

    return valid_field_names


def filter_new_fields(field_updates: dict) -> dict:
    """过滤出新字段（不包括基本字段）

    Args:
        field_updates: 字段更新字典

    Returns:
        dict: 新字段字典
    """
    basic_fields = [
        "chat_title",
        "start_work_message",
        "end_work_message",
        "welcome_message",
        "bot_links",
        "worker_links",
        "is_active",
    ]

    return {k: v for k, v in field_updates.items() if k not in basic_fields}
