"""信用查询命令处理器"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from db.module6_credit.credit_history import get_credit_history
from decorators import authorized_required, error_handler, private_chat_only
from services.module6_credit import (get_credit_benefits, get_credit_info,
                                     get_customer)

logger = logging.getLogger(__name__)


@error_handler
@authorized_required
@private_chat_only
async def view_credit_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """查看客户信用信息"""
    from utils.handler_helpers import check_and_send_not_found, validate_args

    if not await validate_args(update, context, 1, "❌ 用法: /credit <电话>"):
        return

    phone = context.args[0]
    customer = await get_customer(phone)

    if await check_and_send_not_found(update, customer, "❌ 客户不存在"):
        return

    from handlers.module6_credit._helpers import get_customer_id_from_phone

    customer_id = get_customer_id_from_phone(phone)
    credit = await get_credit_info(customer_id)

    if await check_and_send_not_found(update, credit, "❌ 信用记录不存在"):
        return

    benefits = await get_credit_benefits(customer_id)

    msg = (
        f"💳 客户信用信息\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"客户: {customer['name']} ({phone})\n"
        f"信用分数: {credit['credit_score']}/1000\n"
        f"信用等级: {credit['credit_level']}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 统计信息\n"
        f"总订单: {credit['total_orders']}\n"
        f"完成订单: {credit['completed_orders']}\n"
        f"准时付息: {credit['on_time_payments']}次\n"
        f"连续准时: {credit['consecutive_on_time']}次\n"
        f"违约次数: {credit['breach_count']}次\n"
    )

    if benefits:
        msg += (
            f"\n🎁 信用权益\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"额度系数: {benefits['limit_multiplier']}倍\n"
            f"利息折扣: {benefits['interest_discount']*100:.0f}%\n"
        )
        if benefits["has_bonus"]:
            msg += f"赠送金: {benefits['bonus_amount']:.2f}\n"

    await update.message.reply_text(msg)


@error_handler
@authorized_required
@private_chat_only
async def credit_history_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """查看信用历史记录"""
    from utils.handler_helpers import check_and_send_not_found, validate_args

    if not await validate_args(update, context, 1, "❌ 用法: /credit_history <电话>"):
        return

    phone = context.args[0]
    customer = await get_customer(phone)

    if await check_and_send_not_found(update, customer, "❌ 客户不存在"):
        return

    from handlers.module6_credit._helpers import get_customer_id_from_phone

    customer_id = get_customer_id_from_phone(phone)
    history = await get_credit_history(customer_id, limit=10)

    if await check_and_send_not_found(update, history, "📋 暂无信用历史记录"):
        return

    msg = f"📋 信用历史记录（最近10条）\n━━━━━━━━━━━━━━━━━━━━\n"
    for i, record in enumerate(history, 1):
        change_sign = "+" if record["score_change"] >= 0 else ""
        msg += (
            f"{i}. {record['change_type']}\n"
            f"   分数: {record['score_before']} → {record['score_after']} "
            f"({change_sign}{record['score_change']})\n"
            f"   时间: {record['created_at'][:10]}\n"
        )
        if record.get("reason"):
            msg += f"   原因: {record['reason']}\n"
        msg += "\n"

    await update.message.reply_text(msg)
