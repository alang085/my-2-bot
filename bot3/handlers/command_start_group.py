"""启动命令 - 群组处理模块

包含处理群组聊天启动命令的逻辑。
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from utils.handler_helpers import is_admin_user


def _build_group_commands_message(liquid_funds: float) -> str:
    """构建群组命令消息

    Args:
        liquid_funds: 流动资金

    Returns:
        消息文本
    """
    return (
        "📋 Order Management System\n\n"
        "💰 Current Liquid Funds: {:.2f}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💬 Group Chat Commands\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "📝 Order Management:\n"
        "/create - Create new order from group title\n"
        "/order - View current order info\n\n"
        "⚡ Quick Amount Operations:\n"
        "+<amount> - Record interest income\n"
        "+<amount>b - Reduce principal\n"
        "  Example: +1000 or +500b\n\n"
        "🔄 Order States:\n"
        "/normal - Set to Normal\n"
        "/overdue - Set to Overdue\n"
        "/breach - Set to Breach\n"
        "/end - Mark as Completed\n"
        "/breach_end - Mark as Breach Completed\n\n"
        "📢 Broadcast Reminder:\n"
        "/broadcast - Broadcast payment reminder\n\n"
        "↩️ Undo Operation:\n"
        "/undo - Undo last operation (up to 3 consecutive times)\n\n"
        "💡 Tip: Click buttons below for more commands"
    ).format(liquid_funds)


def _build_start_group_keyboard(is_admin: bool) -> InlineKeyboardMarkup:
    """构建启动群组键盘

    Args:
        is_admin: 是否为管理员

    Returns:
        内联键盘
    """
    keyboard = [
        [
            InlineKeyboardButton(
                "📊 Private Commands", callback_data="start_page_private"
            ),
            InlineKeyboardButton(
                "💳 Payment Accounts", callback_data="start_page_payment"
            ),
        ],
    ]

    if is_admin:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "⚙️ Admin Commands", callback_data="start_show_admin_commands"
                )
            ]
        )
    else:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "📊 Private Commands", callback_data="start_page_private"
                )
            ]
        )

    return InlineKeyboardMarkup(keyboard)


async def handle_start_group(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    financial_data: dict,
    user_id: int,
) -> None:
    """处理群组聊天的启动命令

    Args:
        update: Telegram更新对象
        context: 上下文对象
        financial_data: 财务数据
        user_id: 用户ID
    """
    is_admin = is_admin_user(user_id)
    group_commands = _build_group_commands_message(financial_data["liquid_funds"])
    reply_markup = _build_start_group_keyboard(is_admin)
    await update.message.reply_text(group_commands, reply_markup=reply_markup)
