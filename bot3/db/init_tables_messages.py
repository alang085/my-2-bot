"""消息和自动化相关表初始化模块

包含定时播报、群组消息配置、公告等表的创建逻辑。
"""

import sqlite3


def create_message_tables(cursor: sqlite3.Cursor) -> None:
    """创建消息和自动化相关表"""
    from db.init_tables_messages_announcement import create_announcement_tables
    from db.init_tables_messages_broadcast import create_broadcast_tables
    from db.init_tables_messages_group import create_group_tables
    from db.init_tables_messages_message import create_message_type_tables

    # 创建定时播报表
    create_broadcast_tables(cursor)

    # 创建群组消息配置表
    create_group_tables(cursor)

    # 创建公告相关表
    create_announcement_tables(cursor)

    # 创建各种消息类型表
    create_message_type_tables(cursor)


def _migrate_group_message_config(cursor: sqlite3.Cursor) -> None:
    """迁移 group_message_config 表结构（添加新字段）

    Args:
        cursor: 数据库游标
    """
    from db.init_tables_messages_helpers import \
        migrate_group_message_config_fields

    migrate_group_message_config_fields(cursor)
