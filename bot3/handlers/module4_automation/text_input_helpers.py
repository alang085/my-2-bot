"""文本输入辅助函数（向后兼容层）

此文件保留用于向后兼容，实际功能已拆分到：
- finance_input_helpers.py - 财务相关输入处理
- order_input_helpers.py - 订单相关输入处理
- search_input_helpers.py - 搜索相关输入处理
- payment_input_helpers.py - 支付账户相关输入处理
- report_input_helpers.py - 报表相关输入处理
- group_message_input_helpers.py - 群组消息相关输入处理
"""

# 向后兼容导入
from handlers.module4_automation.finance_input_helpers import (
    _handle_expense_input, _handle_expense_query, _handle_income_query_date)
from handlers.module4_automation.group_message_input_helpers import (
    _handle_broadcast, _handle_set_bot_links, _handle_set_worker_links)
from handlers.module4_automation.order_input_helpers import \
    _handle_breach_end_amount
from handlers.module4_automation.payment_input_helpers import (
    _handle_add_account, _handle_edit_account, _handle_edit_account_by_id,
    _handle_update_balance, _handle_update_balance_by_id)
from handlers.module4_automation.report_input_helpers import \
    _handle_report_query
from handlers.module4_automation.search_input_helpers import (
    _handle_report_search, _handle_search_amount_input, _handle_search_input)

# 导出所有函数以保持向后兼容
__all__ = [
    "_handle_add_account",
    "_handle_breach_end_amount",
    "_handle_broadcast",
    "_handle_edit_account",
    "_handle_edit_account_by_id",
    "_handle_expense_input",
    "_handle_expense_query",
    "_handle_income_query_date",
    "_handle_report_query",
    "_handle_report_search",
    "_handle_search_amount_input",
    "_handle_search_input",
    "_handle_set_bot_links",
    "_handle_set_worker_links",
    "_handle_update_balance",
    "_handle_update_balance_by_id",
]
