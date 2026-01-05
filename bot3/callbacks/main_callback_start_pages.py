"""主回调启动页面处理模块

包含启动命令页面相关的回调处理逻辑。
"""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from config import ADMIN_IDS
from handlers.data_access import get_financial_data_for_callback

logger = logging.getLogger(__name__)


async def handle_start_page_private(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """显示私聊命令页面"""
    await query.answer()

    financial_data = await get_financial_data_for_callback()

    private_commands = (
        "📋 订单管理系统\n\n"
        "💰 当前流动资金: {:.2f}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💼 私聊命令\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "📊 报表查询:\n"
        "/report [归属ID] - 查看报表\n"
        "/myreport - 查看我的报表（限有权限的归属ID）\n"
        "/ordertable - 订单总表（管理员）\n\n"
        "🔍 订单搜索:\n"
        "/search <类型> <值> - 搜索订单\n"
        "  类型: order_id/group_id/customer/state/date/group\n"
        "  示例: /search order_id A241225001\n\n"
        "📢 定时播报:\n"
        "/schedule - 管理定时播报任务（最多3个）\n\n"
        "💳 支付账户:\n"
        "/accounts - 查看所有账户表格\n"
        "/gcash - 查看GCASH账号\n"
        "/paymaya - 查看PayMaya账号\n"
        "/balance_history - 查看余额历史记录\n\n"
        "📋 数据查询:\n"
        "/valid_amount - 查看有效金额统计\n"
        "/daily_operations [日期] - 操作记录（管理员）\n"
        "/daily_operations_summary [日期] - 操作汇总（管理员）\n"
        "/daily_changes [日期] - 数据变更表（管理员）\n\n"
        "↩️ 撤销操作:\n"
        "/undo - 撤销上一个操作（最多连续3次）\n"
    ).format(financial_data["liquid_funds"])

    keyboard = [
        [
            InlineKeyboardButton("💬 群聊命令", callback_data="start_page_group"),
            InlineKeyboardButton("💳 支付账户", callback_data="start_page_payment"),
        ],
    ]

    user_id = update.effective_user.id if update.effective_user else None

    if user_id and user_id in ADMIN_IDS:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "⚙️ 管理员命令", callback_data="start_show_admin_commands"
                )
            ]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(private_commands, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"编辑消息失败: {e}", exc_info=True)
        await query.answer("显示失败", show_alert=True)


async def handle_start_page_payment(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """显示支付账户命令页面"""
    await query.answer()

    financial_data = await get_financial_data_for_callback()

    payment_commands = (
        "📋 订单管理系统\n\n"
        "💰 当前流动资金: {:.2f}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💳 支付账户命令\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "📊 账户查询:\n"
        "/accounts - 查看所有账户表格\n"
        "/gcash - 查看GCASH账号详情\n"
        "/paymaya - 查看PayMaya账号详情\n"
        "/balance_history - 查看余额历史记录\n\n"
        "💡 提示: 点击下方按钮可快速查看账户信息"
    ).format(financial_data["liquid_funds"])

    keyboard = [
        [
            InlineKeyboardButton("💬 群聊命令", callback_data="start_page_group"),
            InlineKeyboardButton("📊 私聊命令", callback_data="start_page_private"),
        ],
        [
            InlineKeyboardButton(
                "💳 所有账户", callback_data="payment_view_all_accounts"
            ),
            InlineKeyboardButton("💰 GCASH", callback_data="payment_view_gcash"),
        ],
        [
            InlineKeyboardButton("💵 PayMaya", callback_data="payment_view_paymaya"),
            InlineKeyboardButton(
                "📊 余额历史", callback_data="payment_view_balance_history"
            ),
        ],
    ]

    user_id = update.effective_user.id if update.effective_user else None

    if user_id and user_id in ADMIN_IDS:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "⚙️ 管理员命令", callback_data="start_show_admin_commands"
                )
            ]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(payment_commands, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"编辑消息失败: {e}", exc_info=True)
        await query.answer("显示失败", show_alert=True)


async def handle_start_page_group(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """显示群聊命令页面"""
    await query.answer()

    financial_data = await get_financial_data_for_callback()

    group_commands = (
        "📋 订单管理系统\n\n"
        "💰 当前流动资金: {:.2f}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💬 群聊命令\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "📝 订单管理:\n"
        "/create - 读取群名创建新订单\n"
        "/order - 查看当前订单信息\n\n"
        "⚡ 快捷金额操作:\n"
        "+<金额> - 记录利息收入\n"
        "+<金额>b - 减少本金\n"
        "  示例: +1000 或 +500b\n\n"
        "🔄 订单状态:\n"
        "/normal - 设为正常状态\n"
        "/overdue - 设为逾期状态\n"
        "/breach - 设为违约状态\n"
        "/end - 标记为完成\n"
        "/breach_end - 违约完成\n\n"
        "📢 播报提醒:\n"
        "/broadcast - 播报付款提醒\n\n"
        "↩️ 撤销操作:\n"
        "/undo - 撤销上一个操作（最多连续3次）\n"
    ).format(financial_data["liquid_funds"])

    keyboard = [
        [
            InlineKeyboardButton("📊 私聊命令", callback_data="start_page_private"),
            InlineKeyboardButton("💳 支付账户", callback_data="start_page_payment"),
        ],
    ]

    user_id = update.effective_user.id if update.effective_user else None

    if user_id and user_id in ADMIN_IDS:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "⚙️ 管理员命令", callback_data="start_show_admin_commands"
                )
            ]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(group_commands, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"编辑消息失败: {e}", exc_info=True)
        await query.answer("显示失败", show_alert=True)


async def handle_start_show_admin_commands(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """显示管理员命令"""
    from callbacks.start_admin_message import build_admin_commands_message
    from callbacks.start_admin_send import send_admin_commands_message
    from callbacks.start_admin_validate import validate_admin_access

    # 验证管理员权限
    is_valid, error_msg = await validate_admin_access(update, query)
    if not is_valid:
        await query.answer(error_msg, show_alert=True)
        return

    await query.answer()

    # 构建消息
    message = await build_admin_commands_message()

    # 发送消息
    await send_admin_commands_message(query, message)


async def handle_start_hide_admin_commands(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """隐藏管理员命令"""
    user_id = update.effective_user.id if update.effective_user else None
    if not user_id or user_id not in ADMIN_IDS:
        await query.answer("❌ 此功能仅限管理员使用", show_alert=True)
        return

    await query.answer()

    # 获取财务数据
    financial_data = await get_financial_data_for_callback()

    # 只显示员工命令
    employee_commands = (
        "📋 订单管理系统\n\n"
        "💰 当前流动资金: {:.2f}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💬 群聊命令\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "📝 订单管理:\n"
        "/create - 读取群名创建新订单\n"
        "/associate - 关联现有订单到当前群组\n"
        "/order - 查看当前订单信息\n\n"
        "⚡ 快捷金额操作:\n"
        "+<金额> - 记录利息收入\n"
        "+<金额>b - 减少本金\n"
        "  示例: +1000 或 +500b\n\n"
        "🔄 订单状态:\n"
        "/normal - 设为正常状态\n"
        "/overdue - 设为逾期状态\n"
        "/breach - 设为违约状态\n"
        "/end - 标记为完成\n"
        "/breach_end - 违约完成\n\n"
        "📢 播报提醒:\n"
        "/broadcast - 播报付款提醒\n\n"
        "↩️ 撤销操作:\n"
        "/undo - 撤销上一个操作（最多连续3次）\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💼 私聊命令\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "📊 报表查询:\n"
        "/report [归属ID] - 查看报表\n"
        "/myreport - 查看我的报表（限有权限的归属ID）\n"
        "/ordertable - 查看订单总表（管理员）\n\n"
        "🔍 订单搜索:\n"
        "/search <类型> <值> - 搜索订单\n"
        "  类型: order_id/group_id/customer/state/date/group\n"
        "  示例: /search order_id A241225001\n\n"
        "📢 定时播报:\n"
        "/schedule - 管理定时播报任务（最多3个）\n\n"
        "💳 支付账户:\n"
        "/accounts - 查看所有账户表格\n"
        "/gcash - 查看GCASH账号\n"
        "/paymaya - 查看PayMaya账号\n"
        "/balance_history - 查看余额历史记录\n\n"
        "📋 数据查询:\n"
        "/valid_amount - 查看有效金额统计\n"
        "/daily_operations - 查看每日操作记录（管理员）\n"
        "/daily_operations_summary - 查看每日操作汇总（管理员）\n"
        "/daily_changes - 查看每日数据变更表（管理员）\n\n"
        "↩️ 撤销操作:\n"
        "/undo - 撤销上一个操作（最多连续3次）\n"
    ).format(financial_data["liquid_funds"])

    # 使用内联按钮显示管理员命令
    keyboard = [
        [
            InlineKeyboardButton(
                "🔧 显示管理员命令", callback_data="start_show_admin_commands"
            )
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(employee_commands, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"编辑消息失败: {e}", exc_info=True)
        await query.answer("隐藏失败", show_alert=True)
