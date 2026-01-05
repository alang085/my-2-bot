"""报表相关处理器"""

import logging
from typing import List, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

import db_operations
from config import ADMIN_IDS
from decorators import authorized_required, error_handler, private_chat_only
from services.module5_data.report_service import ReportService
from utils.date_helpers import get_daily_period_date

logger = logging.getLogger(__name__)


# generate_report_text函数已迁移到ReportService，保留此函数作为向后兼容的包装
async def generate_report_text(
    period_type: str,
    start_date: str,
    end_date: str,
    group_id: Optional[str] = None,
    show_expenses: bool = True,
) -> str:
    """生成报表文本（已迁移到ReportService，此函数为向后兼容包装）"""
    return await ReportService.generate_report_text(
        period_type, start_date, end_date, group_id, show_expenses
    )


@error_handler
@authorized_required
@private_chat_only
async def show_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """显示报表（员工命令，不需要归属ID参数）"""
    from handlers.module5_data.report_handlers_keyboard import \
        build_report_keyboard
    from handlers.module5_data.report_handlers_send import send_report_message

    # 默认为今日报表
    period_type = "today"
    group_id = None

    # 处理参数（可选，支持日期查询）
    # 注意：不需要归属ID参数，这是员工命令
    if context.args:
        # 如果第一个参数是日期格式，则作为日期查询
        # 否则忽略（不要求归属ID）
        first_arg = context.args[0]
        # 简单检查是否为日期格式（YYYY-MM-DD）
        if len(first_arg) == 10 and first_arg.count("-") == 2:
            # 这是日期参数，暂时不支持，保持默认今日报表
            pass

    # 获取今日日期
    daily_date = get_daily_period_date()

    # 生成报表（使用ReportService）
    report_text = await ReportService.generate_report_text(
        period_type, daily_date, daily_date, group_id
    )

    # 构建按钮
    reply_markup = await build_report_keyboard(update, context, group_id)

    # 发送报表消息
    await send_report_message(update, context, report_text, reply_markup)


@error_handler
@private_chat_only
async def _validate_user_for_report(
    update: Update,
) -> tuple[bool, Optional[int], Optional[str]]:
    """验证用户权限并获取归属ID

    Returns:
        (is_valid, user_id, group_id)
    """
    user_id = update.effective_user.id if update.effective_user else None
    if not user_id:
        await update.message.reply_text("❌ 无法获取用户信息")
        return False, None, None

    group_id = await db_operations.get_user_group_id(user_id)
    if not group_id:
        await update.message.reply_text(
            "❌ 您没有权限查看任何归属ID的报表。\n" "请联系管理员为您分配归属ID权限。"
        )
        return False, None, None

    return True, user_id, group_id


async def _build_report_keyboard_async(
    group_id: str, user_id: Optional[int]
) -> InlineKeyboardMarkup:
    """构建报表操作键盘（异步版本）

    Args:
        group_id: 归属ID
        user_id: 用户ID

    Returns:
        内联键盘
    """
    keyboard = [
        [
            InlineKeyboardButton(
                "📅 月报", callback_data=f"report_view_month_{group_id}"
            ),
            InlineKeyboardButton(
                "📆 日期查询", callback_data=f"report_view_query_{group_id}"
            ),
        ]
    ]

    if user_id:
        from utils.handler_helpers import check_user_permissions

        is_admin, is_authorized, _ = await check_user_permissions(user_id)
        if is_admin or is_authorized:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "🏢 公司开销", callback_data="report_record_company"
                    ),
                    InlineKeyboardButton(
                        "📝 其他开销", callback_data="report_record_other"
                    ),
                ]
            )

    return InlineKeyboardMarkup(keyboard)


def _split_report_text(report_text: str) -> List[str]:
    """将报表文本分段

    Args:
        report_text: 报表文本

    Returns:
        分段列表
    """
    from constants import TELEGRAM_MESSAGE_MAX_LENGTH

    if len(report_text) <= TELEGRAM_MESSAGE_MAX_LENGTH:
        return [report_text]

    chunks = []
    current_chunk = ""
    for line in report_text.split("\n"):
        if len(current_chunk) + len(line) + 1 > TELEGRAM_MESSAGE_MAX_LENGTH - 200:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = line + "\n"
        else:
            current_chunk += line + "\n"
    if current_chunk:
        chunks.append(current_chunk)

    return chunks


async def _send_report_chunks(
    update: Update, chunks: List[str], reply_markup: InlineKeyboardMarkup
) -> None:
    """发送分段报表

    Args:
        update: Telegram更新对象
        chunks: 分段列表
        reply_markup: 内联键盘
    """
    if not chunks:
        return

    first_chunk = chunks[0]
    if len(chunks) > 1:
        first_chunk += f"\n\n⚠️ 报表内容较长，已分段显示 ({len(chunks)}段)"
    await update.message.reply_text(first_chunk, reply_markup=reply_markup)

    for i, chunk in enumerate(chunks[1:], 2):
        await update.message.reply_text(f"[第 {i}/{len(chunks)} 段]\n\n{chunk}")


async def show_my_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """显示用户有权限查看的归属ID报表（仅限该归属ID）"""
    is_valid, user_id, group_id = await _validate_user_for_report(update)
    if not is_valid:
        return

    period_type = "today"
    daily_date = get_daily_period_date()

    report_text = await ReportService.generate_report_text(
        period_type, daily_date, daily_date, group_id, show_expenses=False
    )

    reply_markup = await _build_report_keyboard_async(group_id, user_id)
    chunks = _split_report_text(report_text)

    if len(chunks) == 1:
        await update.message.reply_text(report_text, reply_markup=reply_markup)
    else:
        await _send_report_chunks(update, chunks, reply_markup)
