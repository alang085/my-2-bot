"""模块6内部辅助函数"""

from typing import Optional

from db.module6_credit.customer_profiles import _generate_customer_id


def format_customer_info(
    customer: dict, credit: Optional[dict] = None, value: Optional[dict] = None
) -> str:
    """格式化客户信息显示

    Args:
        customer: 客户数据
        credit: 信用数据（可选）
        value: 价值数据（可选）

    Returns:
        格式化后的消息文本
    """
    msg = (
        f"👤 客户档案\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"客户ID: {customer.get('customer_id', 'N/A')}\n"
        f"姓名: {customer.get('name', 'N/A')}\n"
        f"电话: {customer.get('phone', 'N/A')}\n"
    )

    if customer.get("id_card"):
        msg += f"证件: {customer['id_card']}\n"

    msg += f"类型: {'白户' if customer.get('customer_type') == 'white' else '黑户'}\n"

    if credit:
        msg += (
            f"\n💳 信用信息\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"信用分数: {credit.get('credit_score', 0)}/1000\n"
            f"信用等级: {credit.get('credit_level', 'N/A')}\n"
        )

    if value:
        msg += (
            f"\n💰 客户价值\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"总利润: {value.get('total_profit', 0):,.2f}\n"
            f"完成订单: {value.get('completed_orders', 0)}\n"
        )

    return msg


def get_customer_id_from_phone(phone: str) -> str:
    """从电话生成客户ID

    Args:
        phone: 电话号码

    Returns:
        客户ID
    """
    return _generate_customer_id(phone)
