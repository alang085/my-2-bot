"""Excel导入行解析模块

包含从Excel行解析订单数据的逻辑。
"""

import logging
from typing import Any, Dict, List, Optional

from utils.excel_import_field_extract import (calculate_weekday_group,
                                              extract_amount, extract_customer,
                                              extract_date, extract_group_id,
                                              extract_order_id, extract_state,
                                              normalize_excel_date)

logger = logging.getLogger(__name__)


def parse_order_row(
    row_values: List[Any], col_indices: Dict[str, int]
) -> Optional[Dict[str, Any]]:
    """解析单行订单数据

    Args:
        row_values: 行数据列表
        col_indices: 列索引字典

    Returns:
        Dict[str, Any] | None: 订单数据字典，如果订单号为空则返回None
    """
    # 提取订单号
    order_id = extract_order_id(row_values, col_indices)
    if not order_id:
        return None  # 跳过没有订单号的行

    # 提取其他字段
    date_str = extract_date(row_values, col_indices)
    customer = extract_customer(row_values, col_indices)
    group_id = extract_group_id(row_values, col_indices)
    amount = extract_amount(row_values, col_indices)
    state = extract_state(row_values, col_indices)

    # 从日期计算星期分组
    weekday_group = calculate_weekday_group(date_str)

    # 规范化日期
    excel_date = normalize_excel_date(date_str)

    order_data = {
        "order_id": order_id,
        "date": excel_date,  # 订单日期（Excel中的时间列）
        "customer": customer or "未知",
        "group_id": group_id or "",
        "amount": amount,
        "state": state,
        "weekday_group": weekday_group,
        "created_at": excel_date,  # 使用Excel中的实际日期作为创建时间
        "updated_at": excel_date,  # 新订单的更新时间等于创建时间
    }

    logger.debug(f"解析订单: {order_id}, {customer}, {amount}, {state}")
    return order_data
