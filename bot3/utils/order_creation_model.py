"""订单创建辅助函数 - 模型创建模块

包含订单模型创建和验证的逻辑。
"""

import logging
from datetime import date
from typing import Any, Dict, Optional, Tuple

from telegram import Update

from utils.chat_helpers import is_group_chat
from utils.models import OrderCreateModel, validate_amount

logger = logging.getLogger(__name__)


def _build_order_model(
    parsed_info: Dict[str, Any],
    chat_id: int,
    group_id: str,
    weekday_group: str,
    initial_state: str,
    order_date: date,
) -> OrderCreateModel:
    """构建订单模型

    Args:
        parsed_info: 解析后的订单信息
        chat_id: 群组ID
        group_id: 归属ID
        weekday_group: 星期分组
        initial_state: 初始状态
        order_date: 订单日期

    Returns:
        订单模型实例
    """
    order_id = parsed_info["order_id"]
    customer = parsed_info["customer"]
    amount = parsed_info["amount"]
    amount_validated = validate_amount(amount)
    created_at = f"{order_date.strftime('%Y-%m-%d')} 12:00:00"

    return OrderCreateModel(
        order_id=order_id,
        group_id=group_id,
        chat_id=chat_id,
        date=created_at,
        weekday_group=weekday_group,
        customer=customer,
        amount=amount_validated,
        state=initial_state,
    )


async def _handle_validation_error(
    update: Update, error: Exception, is_value_error: bool
) -> tuple[bool, None, str]:
    """处理验证错误

    Args:
        update: Telegram 更新对象
        error: 异常对象
        is_value_error: 是否为ValueError

    Returns:
        (False, None, 错误消息)
    """
    if is_value_error:
        logger.error(f"订单数据验证失败: {error}", exc_info=True)
        error_msg = f"❌ Order validation failed: {str(error)}"
    else:
        logger.error(f"创建订单模型失败: {error}", exc_info=True)
        error_msg = "❌ Failed to create order model."

    if is_group_chat(update):
        await update.message.reply_text(error_msg)
    return False, None, error_msg


async def create_and_validate_order_model(
    update: Update,
    parsed_info: Dict[str, Any],
    chat_id: int,
    group_id: str,
    weekday_group: str,
    initial_state: str,
    order_date: date,
) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """创建并验证订单模型

    Args:
        update: Telegram 更新对象
        parsed_info: 解析后的订单信息
        chat_id: 群组ID
        group_id: 归属ID
        weekday_group: 星期分组
        initial_state: 初始状态
        order_date: 订单日期

    Returns:
        Tuple[bool, Optional[Dict], Optional[str]]: (是否成功, 订单字典, 错误消息)
    """
    try:
        order_model = _build_order_model(
            parsed_info, chat_id, group_id, weekday_group, initial_state, order_date
        )
        new_order = order_model.to_dict()

        logger.info(
            f"准备插入订单 {parsed_info['order_id']}: weekday_group={new_order['weekday_group']}, "
            f"date={new_order['date']}"
        )
        return True, new_order, None

    except ValueError as e:
        return await _handle_validation_error(update, e, is_value_error=True)
    except Exception as e:
        return await _handle_validation_error(update, e, is_value_error=False)
