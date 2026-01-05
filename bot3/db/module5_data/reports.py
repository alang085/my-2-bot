"""
报表操作模块（兼容层）

此模块已拆分为多个子模块，保留此文件以保持向后兼容。
所有函数都从相应的子模块导入。
"""

# 从子模块导入所有函数以保持向后兼容
from db.module5_data.baseline_report import (check_baseline_exists,
                                             get_baseline_date,
                                             get_incremental_orders,
                                             save_baseline_date)
from db.module5_data.incremental_orders import \
    get_incremental_orders_with_details
from db.module5_data.merge_records import (check_merge_record_exists,
                                           get_all_merge_records,
                                           get_merge_record, save_merge_record)
from db.module5_data.operation_history import (get_operations_by_filters,
                                               update_operation_data)
from db.module5_data.payment_balance_history import (
    get_balance_history_by_date, get_balance_summary_by_date,
    record_payment_balance_history)

__all__ = [
    # 支付账号余额历史
    "record_payment_balance_history",
    "get_balance_history_by_date",
    "get_balance_summary_by_date",
    # 操作历史查询
    "get_operations_by_filters",
    "update_operation_data",
    # 基准报表操作
    "check_baseline_exists",
    "get_baseline_date",
    "save_baseline_date",
    "get_incremental_orders",
    # 增量订单查询
    "get_incremental_orders_with_details",
    # 增量报表合并记录
    "check_merge_record_exists",
    "get_merge_record",
    "get_all_merge_records",
    "save_merge_record",
]
