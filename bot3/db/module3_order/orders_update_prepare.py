"""订单更新 - 准备数据模块

包含准备新订单数据的逻辑。
"""

from datetime import datetime
from typing import Any, Dict

from utils.chat_helpers import get_weekday_group_from_date


def prepare_new_order_data(
    parsed_info: Dict[str, Any], old_order: Dict[str, Any]
) -> Dict[str, Any]:
    """准备新订单数据

    Args:
        parsed_info: 解析后的订单信息
        old_order: 旧订单信息

    Returns:
        Dict: 新订单数据字典
    """
    new_order_id = parsed_info["order_id"]
    new_date = parsed_info["date"]
    new_customer = parsed_info["customer"]
    new_amount = parsed_info["amount"]
    new_state = parsed_info.get("state", "normal")

    # 计算新的星期分组
    new_weekday_group = get_weekday_group_from_date(new_date)

    # 日期字符串格式
    new_date_str = f"{new_date.strftime('%Y-%m-%d')} 12:00:00"
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {
        "order_id": new_order_id,
        "group_id": old_order["group_id"],
        "chat_id": old_order["chat_id"],
        "date": new_date_str,
        "weekday_group": new_weekday_group,
        "customer": new_customer,
        "amount": new_amount,
        "state": new_state,
        "updated_at": updated_at,
    }
