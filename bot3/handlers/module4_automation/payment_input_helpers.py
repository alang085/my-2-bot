"""支付账户相关文本输入辅助函数（兼容层）

此模块已拆分为多个子模块，保留此文件以保持向后兼容。
所有函数都从相应的子模块导入。
"""

# 从子模块导入所有函数以保持向后兼容
from handlers.module4_automation.payment_account_add import (
    _handle_add_account, _parse_add_account_input, _validate_add_account_input)
from handlers.module4_automation.payment_account_edit import (
    _handle_delete_account, _handle_edit_account, _handle_edit_account_by_id,
    _parse_account_edit_input, _parse_account_input,
    _record_account_update_operation, _refresh_account_display,
    _update_account_info)
from handlers.module4_automation.payment_balance_helpers import (
    _clear_balance_update_state, _handle_update_balance,
    _handle_update_balance_by_id, _process_balance_update,
    _record_balance_update_operation, _validate_account_for_balance_update,
    _validate_and_get_account_for_balance_update,
    _verify_and_display_balance_update)

__all__ = [
    # 余额更新相关
    "_validate_account_for_balance_update",
    "_record_balance_update_operation",
    "_verify_and_display_balance_update",
    "_handle_update_balance",
    "_validate_and_get_account_for_balance_update",
    "_clear_balance_update_state",
    "_process_balance_update",
    "_handle_update_balance_by_id",
    # 账户添加相关
    "_parse_add_account_input",
    "_validate_add_account_input",
    "_handle_add_account",
    # 账户编辑相关
    "_parse_account_edit_input",
    "_record_account_update_operation",
    "_refresh_account_display",
    "_handle_edit_account",
    "_handle_delete_account",
    "_parse_account_input",
    "_update_account_info",
    "_handle_edit_account_by_id",
]
