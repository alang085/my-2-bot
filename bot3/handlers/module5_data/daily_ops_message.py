"""每日操作记录 - 消息构建模块

包含构建操作记录消息的逻辑。
"""

from typing import List

from constants import TELEGRAM_MESSAGE_SAFE_LENGTH
from handlers.module5_data.daily_operations_handlers import \
    format_operation_detail


def build_full_operations_message(operations: List[dict], date: str) -> List[str]:
    """构建完整操作记录消息（分段）

    Args:
        operations: 操作记录列表
        date: 日期字符串

    Returns:
        List[str]: 消息分段列表
    """
    max_length = TELEGRAM_MESSAGE_SAFE_LENGTH
    current_message = f"📋 完整操作记录 ({date})\n"
    current_message += "═══════════════════════════════════════\n"
    current_message += f"总操作数: {len(operations)}\n\n"

    message_parts = [current_message]
    current_part = ""

    for i, op in enumerate(operations, 1):
        op_detail = f"{i}. {format_operation_detail(op)}\n"

        if len(current_part + op_detail) > max_length:
            message_parts.append(current_part)
            current_part = op_detail
        else:
            current_part += op_detail

    if current_part:
        message_parts.append(current_part)

    return message_parts


def build_summary_operations_message(operations: List[dict], date: str) -> str:
    """构建摘要操作记录消息（前50条）

    Args:
        operations: 操作记录列表
        date: 日期字符串

    Returns:
        str: 消息文本
    """
    message = f"📋 操作记录 ({date})\n"
    message += "═══════════════════════════════════════\n"
    message += f"总操作数: {len(operations)}\n"
    message += f"显示前 50 条（共 {len(operations)} 条）\n\n"

    for i, op in enumerate(operations[:50], 1):
        message += f"{i}. {format_operation_detail(op)}\n"

    message += f"\n... 还有 {len(operations) - 50} 条操作未显示"
    return message
