"""开销记录 - 验证模块

包含验证开销记录请求的逻辑。
"""

import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def validate_expense_record(type: str, amount: float) -> Tuple[bool, str]:
    """验证开销记录

    Args:
        type: 开销类型
        amount: 金额

    Returns:
        Tuple: (是否有效, 错误消息)
    """
    valid_expense_types = ["company", "other"]
    if type not in valid_expense_types:
        logger.error(f"无效的开销类型: {type}")
        return False, f"无效的开销类型: {type}，必须是 {valid_expense_types} 之一"

    return True, ""


def get_expense_field(type: str) -> str:
    """获取开销字段名

    Args:
        type: 开销类型

    Returns:
        str: 字段名
    """
    field = "company_expenses" if type == "company" else "other_expenses"
    valid_expense_fields = ["company_expenses", "other_expenses"]
    if field not in valid_expense_fields:
        logger.error(f"无效的开销字段名: {field}")
        raise ValueError(f"无效的开销字段名: {field}")

    return field
