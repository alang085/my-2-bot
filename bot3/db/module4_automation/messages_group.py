"""群组消息配置操作模块

包含群组消息的配置功能。
"""

# 标准库
import logging
from typing import Dict, List, Optional

# 本地模块
from db.base import db_query, db_transaction
from db.module4_automation.message_config_data import GroupMessageConfigParams
from utils.query_builder import QueryBuilder

# 日志
logger = logging.getLogger(__name__)


@db_query
def get_group_message_configs(conn, cursor) -> List[Dict]:
    """获取所有激活的群组消息配置"""
    query, params = (
        QueryBuilder("group_message_config")
        .where("is_active = ?", 1)
        .order_by_field("chat_id")
        .build()
    )
    cursor.execute(query, params)
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


@db_query
def get_group_message_config_by_chat_id(conn, cursor, chat_id: int) -> Optional[Dict]:
    """根据chat_id获取群组消息配置"""
    query, params = (
        QueryBuilder("group_message_config").where("chat_id = ?", chat_id).build()
    )
    cursor.execute(query, params)
    row = cursor.fetchone()
    if row:
        return dict(row)
    return None


@db_transaction
def _check_config_exists(cursor, chat_id: int) -> bool:
    """检查配置是否存在

    Args:
        cursor: 数据库游标
        chat_id: 群组ID

    Returns:
        是否存在
    """
    cursor.execute("SELECT * FROM group_message_config WHERE chat_id = ?", (chat_id,))
    return cursor.fetchone() is not None


def _create_new_config_with_fields(cursor, chat_id: int, field_updates: Dict) -> bool:
    """创建新配置并处理新字段

    Args:
        cursor: 数据库游标
        chat_id: 群组ID
        field_updates: 字段更新字典

    Returns:
        是否成功
    """
    from db.module4_automation.messages_group_create import create_new_config
    from db.module4_automation.messages_group_fields import filter_new_fields
    from db.module4_automation.messages_group_new_fields import \
        update_new_fields_after_create

    if not create_new_config(cursor, chat_id, field_updates):
        return False

    new_fields = filter_new_fields(field_updates)
    if new_fields:
        update_new_fields_after_create(cursor, chat_id, new_fields)

    return True


@db_transaction
def save_group_message_config(
    conn=None,
    cursor=None,
    chat_id: Optional[int] = None,
    chat_title: Optional[str] = None,
    start_work_message: Optional[str] = None,
    end_work_message: Optional[str] = None,
    welcome_message: Optional[str] = None,
    bot_links: Optional[str] = None,
    worker_links: Optional[str] = None,
    is_active: int = 1,
    params: Optional[GroupMessageConfigParams] = None,
    **kwargs,
) -> bool:
    """保存或更新群组消息配置

    支持两种调用方式：
    1. 旧方式（向后兼容）：直接传递参数
    2. 新方式：传递GroupMessageConfigParams对象

    Args:
        conn: 数据库连接（旧方式）
        cursor: 数据库游标（旧方式）
        chat_id: 群组ID（旧方式）
        chat_title: 群组标题（旧方式）
        start_work_message: 开工消息（旧方式）
        end_work_message: 收工消息（旧方式）
        welcome_message: 欢迎消息（旧方式）
        bot_links: 机器人链接（旧方式）
        worker_links: 员工链接（旧方式）
        is_active: 是否激活（旧方式）
        params: 群组消息配置参数（新方式）
        **kwargs: 额外字段（支持的新字段）：
            - start_work_message_1 到 start_work_message_7
            - end_work_message_1 到 end_work_message_7
            - welcome_message_1 到 welcome_message_7
            - anti_fraud_message_1 到 anti_fraud_message_7

    Returns:
        是否成功
    """
    from db.module4_automation.messages_group_fields import \
        get_valid_field_names
    from db.module4_automation.messages_group_prepare import \
        prepare_field_updates
    from db.module4_automation.messages_group_update import \
        update_existing_config

    # 向后兼容：如果使用旧方式调用，创建params对象
    if params is None:
        if chat_id is None:
            raise ValueError("必须提供chat_id或params参数")
        params = GroupMessageConfigParams(
            conn=conn,
            cursor=cursor,
            chat_id=chat_id,
            chat_title=chat_title,
            start_work_message=start_work_message,
            end_work_message=end_work_message,
            welcome_message=welcome_message,
            bot_links=bot_links,
            worker_links=worker_links,
            is_active=is_active,
            extra_fields=kwargs if kwargs else None,
        )
    else:
        # 合并extra_fields和kwargs
        all_extra = {}
        if params.extra_fields:
            all_extra.update(params.extra_fields)
        all_extra.update(kwargs)
        if all_extra:
            params.extra_fields = all_extra

    exists = _check_config_exists(params.cursor, params.chat_id)
    field_updates = prepare_field_updates(
        chat_title=params.chat_title,
        start_work_message=params.start_work_message,
        end_work_message=params.end_work_message,
        welcome_message=params.welcome_message,
        bot_links=params.bot_links,
        worker_links=params.worker_links,
        is_active=params.is_active,
        **(params.extra_fields or {}),
    )

    if exists:
        valid_field_names = get_valid_field_names()
        return update_existing_config(
            params.cursor, params.chat_id, field_updates, valid_field_names
        )
    else:
        return _create_new_config_with_fields(
            params.cursor, params.chat_id, field_updates
        )


@db_transaction
def delete_group_message_config(conn, cursor, chat_id: int) -> bool:
    """删除群组消息配置"""
    cursor.execute("DELETE FROM group_message_config WHERE chat_id = ?", (chat_id,))
    return cursor.rowcount > 0
