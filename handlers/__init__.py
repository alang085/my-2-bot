"""命令处理器模块 - 统一导出所有处理器函数"""

import sys
from pathlib import Path

from .amount_handlers import handle_amount_operation
from .broadcast_handlers import broadcast_payment
from .command_handlers import (
    add_employee,
    adjust_funds,
    check_mismatch,
    create_attribution,
    create_order,
    customer_contribution,
    diagnose_data_inconsistency,
    find_tail_orders,
    fix_income_statistics,
    fix_statistics,
    list_attributions,
    list_employees,
    list_user_group_mappings,
    remove_employee,
    remove_user_group_id,
    set_user_group_id,
    show_current_order,
    start,
    update_weekday_groups,
)
from .daily_changes_handlers import show_daily_changes_table
from .daily_operations_handlers import show_daily_operations, show_daily_operations_summary
from .daily_summary_handlers import show_daily_summary
from .income_handlers import show_income_detail
from .message_handlers import handle_new_chat_members, handle_new_chat_title, handle_text_input
from .order_handlers import set_breach, set_breach_end, set_end, set_normal, set_overdue
from .order_table_handlers import show_order_table
from .payment_handlers import show_all_accounts, show_gcash, show_paymaya
from .report_handlers import show_my_report, show_report
from .restore_handlers import restore_daily_data
from .schedule_handlers import handle_schedule_input, show_schedule_menu
from .search_handlers import search_orders
from .undo_handlers import undo_last_operation

# 确保项目根目录在 Python 路径中
# 这样子模块在导入时能找到 decorators, utils 等模块
# ⚠️ 必须在所有导入语句之前执行！否则会导致 ModuleNotFoundError
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入所有处理器

__all__ = [
    # 命令处理器
    "start",
    "create_order",
    "show_current_order",
    "adjust_funds",
    "create_attribution",
    "list_attributions",
    "add_employee",
    "remove_employee",
    "list_employees",
    "update_weekday_groups",
    "fix_statistics",
    "fix_income_statistics",
    "find_tail_orders",
    "set_user_group_id",
    "remove_user_group_id",
    "list_user_group_mappings",
    "check_mismatch",
    "diagnose_data_inconsistency",
    "customer_contribution",
    # 订单状态处理器
    "set_normal",
    "set_overdue",
    "set_end",
    "set_breach",
    "set_breach_end",
    # 金额操作处理器
    "handle_amount_operation",
    # 报表处理器
    "show_report",
    "show_my_report",
    # 收入明细处理器
    "show_income_detail",
    # 搜索处理器
    "search_orders",
    # 消息处理器
    "handle_new_chat_members",
    "handle_new_chat_title",
    "handle_text_input",
    # 播报处理器
    "broadcast_payment",
    # 支付账户处理器
    "show_gcash",
    "show_paymaya",
    "show_all_accounts",
    # 定时播报处理器
    "show_schedule_menu",
    "handle_schedule_input",
    # 撤销操作处理器
    "undo_last_operation",
    # 订单总表处理器
    "show_order_table",
    # 日切数据处理器
    "show_daily_summary",
    # 每日数据变更表处理器
    "show_daily_changes_table",
    # 每日操作记录处理器
    "show_daily_operations",
    "show_daily_operations_summary",
    # 数据还原处理器
    "restore_daily_data",
]
