"""Excel导入列索引解析模块

包含Excel列索引解析的逻辑。
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


def parse_column_indices(headers: List[str]) -> Dict[str, int]:
    """解析表头，找到各列的索引

    Args:
        headers: 表头列表

    Returns:
        Dict[str, int]: 列索引字典，键为字段名，值为列索引
    """
    col_indices = {}

    # 查找关键列（按优先级，避免重复匹配）
    for idx, header in enumerate(headers):
        header_lower = header.lower()
        # 订单号：优先匹配"订单号"，避免匹配到"订单金额"
        if "订单号" in header and "order_id" not in col_indices:
            col_indices["order_id"] = idx
        # 时间/日期：优先匹配
        elif (
            "时间" in header or "日期" in header or "date" in header_lower
        ) and "date" not in col_indices:
            col_indices["date"] = idx
        # 会员/客户
        elif ("会员" in header or "客户" in header) and "customer" not in col_indices:
            col_indices["customer"] = idx
        # 归属ID
        elif (
            "归属" in header or "group" in header_lower
        ) and "group_id" not in col_indices:
            col_indices["group_id"] = idx
        # 订单金额：必须包含"金额"，避免匹配到"订单号"
        elif (
            "金额" in header or "amount" in header_lower
        ) and "amount" not in col_indices:
            col_indices["amount"] = idx
        # 状态
        elif (
            "状态" in header or "state" in header_lower
        ) and "state" not in col_indices:
            col_indices["state"] = idx
        # 如果"订单号"没找到，再尝试匹配"订单"（但要排除"订单金额"）
        elif (
            "订单" in header
            and "订单号" not in header
            and "金额" not in header
            and "order_id" not in col_indices
        ):
            col_indices["order_id"] = idx

    logger.info(f"找到列索引: {col_indices}")
    return col_indices
