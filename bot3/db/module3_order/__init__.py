"""订单数据库操作模块

此模块提供订单的创建、查询、更新、删除和搜索功能。
"""

# 向后兼容导入 - 从拆分后的文件导入所有函数
from db.module3_order.orders_basic import (
    _batch_insert_to_classified_tables, _ensure_classified_table_exists,
    _get_classified_table_names, _insert_order_to_classified_table_sync,
    _validate_table_name, create_order, create_order_in_classified_tables,
    insert_order_to_classified_table)
from db.module3_order.orders_delete import (delete_order_by_chat_id,
                                            delete_order_by_order_id)
from db.module3_order.orders_query import (
    get_order_by_chat_id, get_order_by_chat_id_including_archived,
    get_order_by_order_id)
from db.module3_order.orders_search import (search_orders_advanced,
                                            search_orders_advanced_all_states,
                                            search_orders_all,
                                            search_orders_by_customer,
                                            search_orders_by_date_range,
                                            search_orders_by_group_id,
                                            search_orders_by_state)
from db.module3_order.orders_update import (update_order_amount,
                                            update_order_chat_id,
                                            update_order_date,
                                            update_order_from_parsed_info,
                                            update_order_group_id,
                                            update_order_state,
                                            update_order_weekday_group)

# 导出所有函数
__all__ = [
    # 基础操作
    "create_order",
    "create_order_in_classified_tables",
    "insert_order_to_classified_table",
    "_insert_order_to_classified_table_sync",
    "_batch_insert_to_classified_tables",
    "_get_classified_table_names",
    "_ensure_classified_table_exists",
    "_validate_table_name",
    # 查询操作
    "get_order_by_chat_id",
    "get_order_by_chat_id_including_archived",
    "get_order_by_order_id",
    # 更新操作
    "update_order_amount",
    "update_order_state",
    "update_order_group_id",
    "update_order_weekday_group",
    "update_order_date",
    "update_order_chat_id",
    "update_order_from_parsed_info",
    # 删除操作
    "delete_order_by_chat_id",
    "delete_order_by_order_id",
    # 搜索操作
    "search_orders_by_group_id",
    "search_orders_by_date_range",
    "search_orders_by_customer",
    "search_orders_by_state",
    "search_orders_all",
    "search_orders_advanced",
    "search_orders_advanced_all_states",
]
