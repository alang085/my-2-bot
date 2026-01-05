"""利息处理 - 准备模块

包含准备订单信息和备注的逻辑。
"""

import logging
from typing import Any, Dict, Optional

from utils.date_helpers import get_daily_period_date

logger = logging.getLogger(__name__)


async def prepare_interest_data(
    order_model: Any, amount_validated: float
) -> Dict[str, Any]:
    """准备利息处理所需的数据

    Args:
        order_model: 订单模型
        amount_validated: 验证后的金额

    Returns:
        Dict: 准备的数据字典
    """
    group_id = order_model.group_id
    order_state = order_model.state
    date = get_daily_period_date()

    # 获取订单的customer_id（从数据库查询）
    customer_id = None
    try:
        from db.module3_order.orders import get_order_by_chat_id

        order_dict = await get_order_by_chat_id(order_model.chat_id)
        customer_id = order_dict.get("customer_id") if order_dict else None
    except Exception as e:
        logger.debug(f"获取订单customer_id失败: {e}")

    # 根据订单状态确定备注信息
    if order_state == "end":
        note = "补利息（订单已完成）"
    elif order_state == "breach_end":
        note = "补利息（违约还款）"
    elif order_state == "breach":
        note = "利息收入（违约状态）"
    else:
        note = "利息收入"

    return {
        "group_id": group_id,
        "order_state": order_state,
        "date": date,
        "customer_id": customer_id,
        "note": note,
    }
