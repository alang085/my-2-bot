"""订单相关工具函数（向后兼容层）

此文件保留用于向后兼容，实际功能已拆分到：
- order_parsing.py - 订单解析相关
- order_date.py - 订单日期相关
- order_state.py - 订单状态相关
- order_creation.py - 订单创建辅助函数
- order_creation_main.py - 订单创建主函数
- order_broadcast.py - 订单播报相关
"""

# 向后兼容导入 - 从拆分后的文件导入所有函数
from utils.order_broadcast import send_auto_broadcast
from utils.order_creation import (_associate_order_to_group,
                                  _create_new_order_internal,
                                  _get_existing_chat_title,
                                  _handle_parse_error,
                                  _update_existing_order_from_parsed_info)
from utils.order_creation_main import try_create_order_from_title
from utils.order_date import (_parse_current_order_date,
                              _update_order_date_and_weekday)
from utils.order_parsing import (_match_a_prefix_format,
                                 _match_traditional_format,
                                 _parse_amount_from_digits,
                                 _parse_date_from_digits, get_state_from_title,
                                 parse_order_from_title)
from utils.order_state import (_handle_state_transition_stats,
                               _record_state_change_operation,
                               _validate_state_transition,
                               update_order_state_from_title)

# 导出所有函数以保持向后兼容
__all__ = [
    # 解析相关
    "parse_order_from_title",
    "get_state_from_title",
    "_match_a_prefix_format",
    "_match_traditional_format",
    "_parse_date_from_digits",
    "_parse_amount_from_digits",
    # 日期相关
    "_parse_current_order_date",
    "_update_order_date_and_weekday",
    # 状态相关
    "_validate_state_transition",
    "_handle_state_transition_stats",
    "_record_state_change_operation",
    "update_order_state_from_title",
    # 创建相关
    "try_create_order_from_title",
    "_create_new_order_internal",
    "_update_existing_order_from_parsed_info",
    "_associate_order_to_group",
    "_get_existing_chat_title",
    "_handle_parse_error",
    # 播报相关
    "send_auto_broadcast",
]
