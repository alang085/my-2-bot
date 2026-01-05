"""启动命令 - 私聊处理模块

包含处理私聊启动命令的逻辑。
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from utils.handler_helpers import is_admin_user


def _build_private_commands_message(liquid_funds: float) -> str:
    """构建私聊命令消息

    Args:
        liquid_funds: 流动资金

    Returns:
        消息文本
    """
    return (
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
        "/undo - 撤销上一个操作（最多连续3次）\n\n"
        "💡 提示: 点击下方按钮查看更多命令"
    ).format(liquid_funds)


def _build_start_private_keyboard(is_admin: bool) -> InlineKeyboardMarkup:
    """构建启动私聊键盘

    Args:
        is_admin: 是否为管理员

    Returns:
        内联键盘
    """
    keyboard = [
        [
            InlineKeyboardButton("📊 私聊命令", callback_data="start_page_private"),
            InlineKeyboardButton("💳 支付账户", callback_data="start_page_payment"),
        ],
    ]

    if is_admin:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "⚙️ 管理员命令", callback_data="start_show_admin_commands"
                )
            ]
        )
    else:
        keyboard.append(
            [InlineKeyboardButton("📊 私聊命令", callback_data="start_page_private")]
        )

    return InlineKeyboardMarkup(keyboard)


async def handle_start_private(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    financial_data: dict,
    user_id: int,
) -> None:
    """处理私聊的启动命令

    Args:
        update: Telegram更新对象
        context: 上下文对象
        financial_data: 财务数据
        user_id: 用户ID
    """
    is_admin = is_admin_user(user_id)
    group_commands = _build_private_commands_message(financial_data["liquid_funds"])
    reply_markup = _build_start_private_keyboard(is_admin)
    await update.message.reply_text(group_commands, reply_markup=reply_markup)
