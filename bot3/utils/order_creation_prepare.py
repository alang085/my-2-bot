"""订单创建辅助函数 - 准备模块

包含订单创建前的数据准备逻辑。
"""

import logging
from datetime import date
from typing import Any, Dict, Tuple

from utils.chat_helpers import get_weekday_group_from_date
from utils.order_parsing import get_state_from_title

logger = logging.getLogger(__name__)


def prepare_order_data(
    parsed_info: Dict[str, Any], title: str, order_date: date
) -> Tuple[str, str, str, str, float, str, str]:
    """准备订单数据

    Args:
        parsed_info: 解析后的订单信息
        title: 群名
        order_date: 订单日期

    Returns:
        Tuple: (order_id, customer, amount, initial_state, group_id, weekday_group, created_at)
    """
    order_id = parsed_info["order_id"]
    customer = parsed_info["customer"]
    amount = parsed_info["amount"]

    # 初始状态识别 (根据群名标志)
    initial_state = get_state_from_title(title)

    # 准备订单基础数据
    group_id = "S01"  # 默认归属
    weekday_group = get_weekday_group_from_date(order_date)
    created_at = f"{order_date.strftime('%Y-%m-%d')} 12:00:00"

    logger.info(
        f"创建订单 {order_id}: 日期={order_date}, 星期分组={weekday_group}, "
        f"weekday()={order_date.weekday()}"
    )

    return (
        order_id,
        customer,
        amount,
        initial_state,
        group_id,
        weekday_group,
        created_at,
    )
