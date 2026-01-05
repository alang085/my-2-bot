"""客户价值查询命令处理器"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from constants import TOP_CUSTOMER_CRITERIA
from decorators import (admin_required, authorized_required, error_handler,
                        private_chat_only)
from services.module6_credit import (get_customer, get_top_customers,
                                     get_value_info)

logger = logging.getLogger(__name__)


@error_handler
@authorized_required
@private_chat_only
async def customer_value_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """查看客户价值"""
    from handlers.module6_credit._helpers import get_customer_id_from_phone
    from utils.handler_helpers import check_and_send_not_found, validate_args

    if not await validate_args(update, context, 1, "❌ 用法: /customer_value <电话>"):
        return

    phone = context.args[0]
    customer = await get_customer(phone)

    if await check_and_send_not_found(update, customer, "❌ 客户不存在"):
        return

    customer_id = get_customer_id_from_phone(phone)
    value = await get_value_info(customer_id)

    if await check_and_send_not_found(update, value, "❌ 价值记录不存在"):
        return

    msg = (
        f"💰 客户价值信息\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"客户: {customer['name']} ({phone})\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"总借款: {value['total_borrowed']:,.2f}\n"
        f"总付息: {value['total_interest_paid']:,.2f}\n"
        f"总利润: {value['total_profit']:,.2f}\n"
        f"订单数: {value['order_count']}\n"
        f"完成数: {value['completed_order_count']}\n"
        f"平均金额: {value['average_order_amount']:,.2f}\n"
    )

    await update.message.reply_text(msg)


@error_handler
@admin_required
@private_chat_only
async def top_customers_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """查看优质客户列表"""
    # 解析筛选条件
    min_score = TOP_CUSTOMER_CRITERIA.get("min_credit_score")
    min_profit = TOP_CUSTOMER_CRITERIA.get("min_total_profit")
    min_orders = TOP_CUSTOMER_CRITERIA.get("min_completed_orders")

    # 可以从参数覆盖
    if context.args:
        try:
            if len(context.args) >= 1:
                min_score = int(context.args[0]) if context.args[0] else None
            if len(context.args) >= 2:
                min_profit = float(context.args[1]) if context.args[1] else None
            if len(context.args) >= 3:
                min_orders = int(context.args[2]) if context.args[2] else None
        except (ValueError, TypeError):
            pass

    from utils.handler_helpers import check_and_send_not_found

    customers = await get_top_customers(
        min_score=min_score,
        min_profit=min_profit,
        min_orders=min_orders,
        limit=20,
    )

    if await check_and_send_not_found(update, customers, "📋 暂无优质客户"):
        return

    msg = f"⭐ 优质客户列表（共{len(customers)}个）\n" f"━━━━━━━━━━━━━━━━━━━━\n"

    for i, customer in enumerate(customers, 1):
        credit_score = customer.get("credit_score", 0)
        total_profit = customer.get("total_profit", 0)
        completed = customer.get("completed_order_count", 0)
        msg += (
            f"{i}. {customer['name']} ({customer['phone']})\n"
            f"   信用: {credit_score}分 | 利润: {total_profit:,.2f} | "
            f"完成: {completed}单\n"
        )

    await update.message.reply_text(msg)
