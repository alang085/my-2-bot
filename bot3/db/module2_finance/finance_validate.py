"""财务数据更新 - 验证模块

包含验证财务数据更新请求的逻辑。
"""

import logging

logger = logging.getLogger(__name__)


def validate_financial_field(field: str) -> bool:
    """验证财务数据字段名

    Args:
        field: 字段名

    Returns:
        bool: 是否有效
    """
    valid_fields = [
        "valid_orders",
        "valid_amount",
        "liquid_funds",
        "new_clients",
        "new_clients_amount",
        "old_clients",
        "old_clients_amount",
        "interest",
        "completed_orders",
        "completed_amount",
        "breach_orders",
        "breach_amount",
        "breach_end_orders",
        "breach_end_amount",
        "overdue_orders",  # 添加overdue字段支持
        "overdue_amount",  # 添加overdue字段支持
    ]
    if field not in valid_fields:
        logger.error(f"无效的财务数据字段名: {field}")
        return False

    return True
