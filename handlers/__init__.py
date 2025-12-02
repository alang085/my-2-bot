"""命令处理器模块 - 统一导出所有处理器函数"""
from .undo_handlers import undo_last_operation
from .schedule_handlers import show_schedule_menu, handle_schedule_input
from .payment_handlers import show_gcash, show_paymaya, show_all_accounts
from .broadcast_handlers import broadcast_payment
from .message_handlers import (
    handle_new_chat_members,
    handle_new_chat_title,
    handle_text_input
)
from .search_handlers import search_orders
from .income_handlers import show_income_detail
from .report_handlers import show_report, show_my_report
from .amount_handlers import handle_amount_operation
from .order_handlers import (
    set_normal,
    set_overdue,
    set_end,
    set_breach,
    set_breach_end
)
from .command_handlers import (
    start,
    create_order,
    show_current_order,
    adjust_funds,
    create_attribution,
    list_attributions,
    add_employee,
    remove_employee,
    list_employees,
    update_weekday_groups,
    fix_statistics,
    find_tail_orders,
    set_user_group_id,
    remove_user_group_id,
    list_user_group_mappings,
    check_mismatch,
    customer_contribution
)
import os
import sys
from pathlib import Path

# 确保项目根目录在 Python 路径中
# 这样子模块在导入时能找到 decorators, utils 等模块
# ⚠️ 必须在所有导入语句之前执行！否则会导致 ModuleNotFoundError
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入所有处理器
# 命令处理器

# 订单状态处理器

# 金额操作处理器

# 报表处理器

# 收入明细处理器（新增）

# 搜索处理器

# 消息处理器

# 播报处理器

# 支付账户处理器

# 定时播报处理器

# 撤销操作处理器


__all__ = [
    # 命令处理器
    'start',
    'create_order',
    'show_current_order',
    'adjust_funds',
    'create_attribution',
    'list_attributions',
    'add_employee',
    'remove_employee',
    'list_employees',
    'update_weekday_groups',
    'fix_statistics',
    'find_tail_orders',
    'set_user_group_id',
    'remove_user_group_id',
    'list_user_group_mappings',
    'check_mismatch',
    'customer_contribution',
    # 订单状态处理器
    'set_normal',
    'set_overdue',
    'set_end',
    'set_breach',
    'set_breach_end',
    # 金额操作处理器
    'handle_amount_operation',
    # 报表处理器
    'show_report',
    'show_my_report',
    # 收入明细处理器
    'show_income_detail',
    # 搜索处理器
    'search_orders',
    # 消息处理器
    'handle_new_chat_members',
    'handle_new_chat_title',
    'handle_text_input',
    # 播报处理器
    'broadcast_payment',
    # 支付账户处理器
    'show_gcash',
    'show_paymaya',
    'show_all_accounts',
    # 定时播报处理器
    'show_schedule_menu',
    'handle_schedule_input',
    # 撤销操作处理器
    'undo_last_operation'
]
