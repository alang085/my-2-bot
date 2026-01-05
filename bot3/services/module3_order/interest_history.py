"""利息处理 - 历史记录模块

包含准备操作历史数据的逻辑。
"""

from typing import Any, Dict, Optional


def prepare_operation_data(
    amount_validated: float,
    group_id: str,
    order_model: Any,
    date: str,
    income_record_id: Optional[int],
) -> Dict[str, Any]:
    """准备操作历史数据

    Args:
        amount_validated: 验证后的金额
        group_id: 归属ID
        order_model: 订单模型
        date: 日期
        income_record_id: 收入记录ID

    Returns:
        Dict: 操作数据字典
    """
    operation_data = {
        "amount": amount_validated,
        "group_id": group_id,
        "order_id": order_model.order_id,
        "date": date,
        "income_record_id": income_record_id,
    }
    return operation_data
