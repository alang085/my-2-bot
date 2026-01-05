"""日结数据更新 - 验证模块

包含验证日结数据更新请求的逻辑。
"""

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


def validate_daily_field(field: str) -> bool:
    """验证日结数据字段名

    Args:
        field: 字段名

    Returns:
        bool: 是否有效
    """
    valid_fields = [
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
        "liquid_flow",
        "company_expenses",
        "other_expenses",
    ]
    if field not in valid_fields:
        logger.error(f"无效的日结数据字段名: {field}")
        return False

    return True


def validate_date_format(date: str) -> bool:
    """验证日期格式

    Args:
        date: 日期字符串

    Returns:
        bool: 是否有效
    """
    try:
        datetime.strptime(date, "%Y-%m-%d")
        return True
    except ValueError:
        logger.error(f"无效的日期格式: {date}")
        return False
