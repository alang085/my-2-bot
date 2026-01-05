"""客户档案管理命令处理器"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from decorators import (admin_required, authorized_required, error_handler,
                        private_chat_only)
from services.module6_credit import (create_customer, get_customer,
                                     list_customers, set_customer_type_func,
                                     update_customer)

logger = logging.getLogger(__name__)


@error_handler
@authorized_required
@private_chat_only
async def create_customer_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """创建客户档案"""
    from utils.handler_helpers import validate_args

    if not await validate_args(
        update, context, 2, "❌ 用法: /create_customer <姓名> <电话> [证件]"
    ):
        return

    name = context.args[0]
    phone = context.args[1]
    id_card = context.args[2] if len(context.args) > 2 else None

    success, error_msg, customer = await create_customer(name, phone, id_card)
    if success and customer:
        msg = (
            f"✅ 客户档案创建成功\n"
            f"客户ID: {customer['customer_id']}\n"
            f"姓名: {customer['name']}\n"
            f"电话: {customer['phone']}\n"
            f"类型: {'白户' if customer['customer_type'] == 'white' else '黑户'}"
        )
    else:
        msg = error_msg or "❌ 创建失败"
    await update.message.reply_text(msg)


@error_handler
@authorized_required
@private_chat_only
async def update_customer_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """更新客户信息"""
    from utils.handler_helpers import send_success_or_error, validate_args

    if not await validate_args(
        update,
        context,
        3,
        "❌ 用法: /update_customer <电话> <字段> <值>\n字段: name, id_card",
    ):
        return

    phone = context.args[0]
    field = context.args[1]
    value = " ".join(context.args[2:])

    success, error_msg = await update_customer(phone, field, value)
    await send_success_or_error(
        update, success, "✅ 更新成功", error_msg or "❌ 更新失败"
    )


@error_handler
@authorized_required
@private_chat_only
async def view_customer_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """查看客户档案"""
    from utils.handler_helpers import check_and_send_not_found, validate_args

    if not await validate_args(update, context, 1, "❌ 用法: /view_customer <电话>"):
        return

    phone = context.args[0]
    customer = await get_customer(phone)

    if await check_and_send_not_found(update, customer, "❌ 客户不存在"):
        return

    from handlers.module6_credit._helpers import (format_customer_info,
                                                  get_customer_id_from_phone)
    from services.module6_credit import get_credit_info, get_value_info

    customer_id = get_customer_id_from_phone(phone)
    credit = await get_credit_info(customer_id)
    value = await get_value_info(customer_id)

    msg = format_customer_info(customer, credit, value)
    if customer.get("first_contact_date"):
        msg += f"\n首次接触: {customer['first_contact_date']}\n"

    await update.message.reply_text(msg)


@error_handler
@admin_required
@private_chat_only
async def set_customer_type_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """设置客户类型"""
    from utils.handler_helpers import send_success_or_error, validate_args

    if not await validate_args(
        update, context, 2, "❌ 用法: /set_customer_type <电话> <white|black>"
    ):
        return

    phone = context.args[0]
    customer_type = context.args[1].lower()

    success, error_msg = await set_customer_type_func(phone, customer_type)
    if success:
        type_name = "白户" if customer_type == "white" else "黑户"
        await send_success_or_error(update, True, f"✅ 已设置为{type_name}")
    else:
        await send_success_or_error(update, False, "", error_msg or "❌ 设置失败")


@error_handler
@admin_required
@private_chat_only
async def list_customers_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """列出所有客户"""
    from utils.handler_helpers import (check_and_send_not_found,
                                       format_list_message)

    customer_type = context.args[0] if context.args else None
    customers = await list_customers(customer_type)

    if await check_and_send_not_found(update, customers, "📋 暂无客户"):
        return

    def format_customer(item: dict, index: int) -> str:
        type_name = "白户" if item["customer_type"] == "white" else "黑户"
        return f"{index}. {item['name']} ({item['phone']}) - {type_name}"

    msg = format_list_message(customers, "📋 客户列表", format_customer, max_items=20)
    await update.message.reply_text(msg)
