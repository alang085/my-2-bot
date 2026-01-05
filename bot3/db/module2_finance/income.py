"""收入明细操作模块（向后兼容层）

此文件保留用于向后兼容，实际功能已拆分到：
- income_basic.py - 基础操作（创建、基础查询）
- income_query.py - 查询操作
- income_statistics.py - 统计操作
"""

# 向后兼容导入 - 从拆分后的文件导入所有函数
from db.module2_finance.income_basic import (get_all_interest_by_order_id,
                                             get_income_records,
                                             get_interest_by_order_id,
                                             get_interests_by_order_ids,
                                             record_income)
from db.module2_finance.income_query import (get_all_valid_orders,
                                             get_breach_end_orders_by_date,
                                             get_breach_orders_by_date,
                                             get_completed_orders_by_date,
                                             get_daily_expenses,
                                             get_daily_interest_total,
                                             get_daily_summary,
                                             get_new_orders_by_date,
                                             save_daily_summary)
from db.module2_finance.income_statistics import (
    get_customer_orders_summary, get_customer_total_contribution,
    get_income_summary_by_group, get_income_summary_by_type)

# 导出所有函数以保持向后兼容
__all__ = [
    # 基础操作
    "record_income",
    "get_income_records",
    "get_interest_by_order_id",
    "get_all_interest_by_order_id",
    "get_interests_by_order_ids",
    # 查询操作
    "get_all_valid_orders",
    "get_completed_orders_by_date",
    "get_breach_orders_by_date",
    "get_breach_end_orders_by_date",
    "get_new_orders_by_date",
    "get_daily_interest_total",
    "get_daily_expenses",
    "get_daily_summary",
    "save_daily_summary",
    # 统计操作
    "get_customer_total_contribution",
    "get_customer_orders_summary",
    "get_income_summary_by_type",
    "get_income_summary_by_group",
]
