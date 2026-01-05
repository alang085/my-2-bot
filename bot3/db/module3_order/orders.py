"""订单操作模块（向后兼容层）

此文件保留用于向后兼容，实际功能已拆分到：
- orders_basic.py - 基础操作（创建、分类表管理）
- orders_query.py - 查询操作
- orders_update.py - 更新操作
- orders_delete.py - 删除操作
- orders_search.py - 搜索操作

注意：由于循环导入问题，所有导入都使用延迟导入（lazy import）模式。
"""

# 模块缓存（避免重复导入）
_basic_module_cache = None


# 延迟导入辅助函数
def _lazy_import_basic():
    """延迟导入 orders_basic 模块（使用直接文件导入避免循环导入）"""
    global _basic_module_cache
    if _basic_module_cache is None:
        # 使用 importlib 直接导入文件，避免触发 __init__.py
        import importlib.util
        import os

        file_path = os.path.join(os.path.dirname(__file__), "orders_basic.py")
        spec = importlib.util.spec_from_file_location("orders_basic_direct", file_path)
        _basic_module_cache = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_basic_module_cache)
    return _basic_module_cache


def _lazy_import_delete():
    """延迟导入 orders_delete 模块"""
    from db.module3_order import orders_delete

    return orders_delete


def _lazy_import_query():
    """延迟导入 orders_query 模块"""
    from db.module3_order import orders_query

    return orders_query


def _lazy_import_search():
    """延迟导入 orders_search 模块"""
    from db.module3_order import orders_search

    return orders_search


def _lazy_import_update():
    """延迟导入 orders_update 模块"""
    from db.module3_order import orders_update

    return orders_update


# 使用 __getattr__ 实现延迟导入
def __getattr__(name: str):
    """延迟导入函数以支持 from orders import *"""
    # 基础操作
    if name in (
        "create_order",
        "create_order_in_classified_tables",
        "insert_order_to_classified_table",
        "_insert_order_to_classified_table_sync",
        "_batch_insert_to_classified_tables",
        "_get_classified_table_names",
        "_ensure_classified_table_exists",
        "_validate_table_name",
    ):
        module = _lazy_import_basic()
        return getattr(module, name)

    # 删除操作
    if name in ("delete_order_by_chat_id", "delete_order_by_order_id"):
        module = _lazy_import_delete()
        return getattr(module, name)

    # 查询操作
    if name in (
        "get_order_by_chat_id",
        "get_order_by_chat_id_including_archived",
        "get_order_by_order_id",
    ):
        module = _lazy_import_query()
        return getattr(module, name)

    # 搜索操作
    if name in (
        "search_orders_advanced",
        "search_orders_advanced_all_states",
        "search_orders_all",
        "search_orders_by_customer",
        "search_orders_by_date_range",
        "search_orders_by_group_id",
        "search_orders_by_state",
    ):
        module = _lazy_import_search()
        return getattr(module, name)

    # 更新操作
    if name in (
        "update_order_amount",
        "update_order_chat_id",
        "update_order_date",
        "update_order_from_parsed_info",
        "update_order_group_id",
        "update_order_state",
        "update_order_weekday_group",
    ):
        module = _lazy_import_update()
        return getattr(module, name)

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# 导出所有函数以保持向后兼容
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
