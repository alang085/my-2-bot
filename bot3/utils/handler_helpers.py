"""Handler辅助函数（向后兼容层）

此文件保留用于向后兼容，实际功能已拆分到：
- update_info.py - Update信息提取
- order_validation_helpers.py - 订单验证
- message_helpers.py - 消息发送
- permission_helpers.py - 权限检查
- data_helpers.py - 数据操作
- parsing_helpers.py - 参数解析
- formatting_helpers.py - 格式化
- handler_context.py - Handler上下文类
"""

# 标准库
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from telegram import Update
from telegram.ext import ContextTypes

# 本地模块
import db_operations
from utils.data_helpers import (check_data_consistency,
                                safe_execute_with_error_handling)
from utils.formatting_helpers import format_error
from utils.handler_context import HandlerContext
from utils.message_helpers import (send_bilingual_message, send_error_message,
                                   send_success_message)
from utils.models import (OrderModel, OrderStateModel, validate_amount,
                          validate_order, validate_order_state)
from utils.order_validation_helpers import (get_and_validate_order,
                                            validate_and_get_order)
from utils.parsing_helpers import (parse_date_from_args, parse_date_string,
                                   parse_user_id_from_args,
                                   validate_args_count)
from utils.permission_helpers import (check_user_permissions, is_admin_user,
                                      is_authorized_user, require_permission)
from utils.update_info import (get_chat_info, get_user_id, get_user_info,
                               require_chat_info)

logger = logging.getLogger(__name__)

# 导出所有函数以保持向后兼容
__all__ = [
    # Update信息提取
    "get_chat_info",
    "get_user_id",
    "require_chat_info",
    "get_user_info",
    # 订单验证
    "get_and_validate_order",
    "validate_and_get_order",
    # 消息发送
    "send_error_message",
    "send_success_message",
    "send_bilingual_message",
    # 权限检查
    "check_user_permissions",
    "is_admin_user",
    "is_authorized_user",
    "require_permission",
    # 数据操作
    "check_data_consistency",
    "safe_execute_with_error_handling",
    # 参数解析
    "parse_user_id_from_args",
    "parse_date_from_args",
    "validate_args_count",
    "parse_date_string",
    # 格式化
    "format_error",
    # Handler上下文类
    "HandlerContext",
    # 模型验证（保留导出）
    "OrderModel",
    "OrderStateModel",
    "validate_amount",
    "validate_order",
    "validate_order_state",
]
