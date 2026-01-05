"""收入明细查询处理器（仅管理员权限）"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

import db_operations
from config import ADMIN_IDS
from decorators import error_handler, private_chat_only
from utils.date_helpers import (datetime_str_to_beijing_str,
                                get_daily_period_date)
from utils.error_messages import ErrorMessages
from utils.income_helpers import (get_income_type_name, get_income_type_order,
                                  group_income_records_by_type)

logger = logging.getLogger(__name__)


# 使用 handler_helpers 中的 is_admin_user 函数
from utils.handler_helpers import is_admin_user as _is_admin


async def format_income_detail(record: dict) -> str:
    """格式化单条收入明细 - 格式：时间 | 订单号 | 金额（对齐显示）

    Args:
        record: 收入记录字典

    Returns:
        格式化后的明细行
    """
    from handlers.module2_finance.income_format_helpers import (
        _extract_time_from_record, _format_amount_from_record,
        format_income_detail_line)

    # 提取时间字符串
    time_str = _extract_time_from_record(record)

    # 获取订单号
    order_id = record.get("order_id") or "无"

    # 格式化金额
    amount_str = _format_amount_from_record(record)

    # 格式化明细行
    return format_income_detail_line(time_str, order_id, amount_str)


def _build_income_report_header(title: str, start_date: str, end_date: str) -> str:
    """构建收入报表头部

    Args:
        title: 标题
        start_date: 起始日期
        end_date: 结束日期

    Returns:
        报表头部文本
    """
    report = f"💰 {title}\n"
    report += f"{'═' * 30}\n"
    report += f"📅 {start_date} 至 {end_date}\n"
    report += f"{'═' * 30}\n\n"
    return report


def _build_income_report_footer(total_amount: float) -> str:
    """构建收入报表尾部

    Args:
        total_amount: 总金额

    Returns:
        报表尾部文本
    """
    return f"{'═' * 30}\n" f"💰 总收入: {total_amount:,.2f}\n"


async def _generate_income_report_content(
    by_type: Dict,
    type_order: List[str],
    income_type: Optional[str],
    start_date: str,
    end_date: str,
    page: int,
    items_per_page: int,
) -> Tuple[str, bool, int, Optional[str]]:
    """生成收入报表内容

    Args:
        by_type: 按类型分组的记录
        type_order: 类型顺序
        income_type: 指定的收入类型
        start_date: 起始日期
        end_date: 结束日期
        page: 页码
        items_per_page: 每页项目数

    Returns:
        (报表内容, 是否有更多页, 总页数, 当前类型)
    """
    from handlers.module2_finance.income_report_all import \
        generate_all_types_report
    from handlers.module2_finance.income_report_single import \
        generate_single_type_report

    has_more_pages = False
    total_pages = 1
    current_type = None

    if income_type and income_type in by_type:
        type_records = by_type[income_type]
        type_report, has_more_pages, total_pages, current_type = (
            await generate_single_type_report(
                type_records, income_type, start_date, end_date, page, items_per_page
            )
        )
        return type_report, has_more_pages, total_pages, current_type
    else:
        all_report, current_type = await generate_all_types_report(by_type, type_order)
        return all_report, has_more_pages, total_pages, current_type


async def generate_income_report(
    records: list,
    start_date: str,
    end_date: str,
    title: str = "收入明细",
    page: int = 1,
    items_per_page: int = 20,
    income_type: Optional[str] = None,
) -> tuple:
    """
    生成收入明细报表（支持分页）

    返回: (report_text, has_more_pages, total_pages, current_type)
    """
    from handlers.module2_finance.income_handlers import get_income_type_order
    from handlers.module2_finance.income_report_prepare import \
        prepare_income_records

    if not records:
        return (
            f"💰 {title}\n\n{start_date} 至 {end_date}\n\n❌ 无记录",
            False,
            0,
            None,
        )

    filtered_records, by_type, total_amount = prepare_income_records(
        records, income_type
    )

    report = _build_income_report_header(title, start_date, end_date)

    type_order = get_income_type_order()
    if income_type:
        type_order = [income_type] if income_type in type_order else []

    content, has_more_pages, total_pages, current_type = (
        await _generate_income_report_content(
            by_type, type_order, income_type, start_date, end_date, page, items_per_page
        )
    )
    report += content

    report += _build_income_report_footer(total_amount)

    return (report, has_more_pages, total_pages, current_type)


@error_handler
@private_chat_only
def _build_income_detail_keyboard(
    total_pages: int, current_type: Optional[str], date: str
) -> List[List[InlineKeyboardButton]]:
    """构建收入明细键盘

    Args:
        total_pages: 总页数
        current_type: 当前类型
        date: 日期

    Returns:
        键盘按钮列表
    """
    keyboard = []

    if total_pages > 1:
        page_buttons = []
        if 1 < total_pages:
            page_buttons.append(
                InlineKeyboardButton(
                    "下一页 ▶️",
                    callback_data=f"income_page_{current_type}|2|{date}|{date}",
                )
            )
        if page_buttons:
            keyboard.append(page_buttons)

    keyboard.extend(
        [
            [InlineKeyboardButton("📆 日期查询", callback_data="income_view_query")],
            [
                InlineKeyboardButton(
                    "🔙 返回报表", callback_data="report_view_today_ALL"
                )
            ],
        ]
    )

    return keyboard


async def _send_income_detail_message(
    update: Update, report: str, keyboard: List[List[InlineKeyboardButton]]
) -> None:
    """发送收入明细消息

    Args:
        update: Telegram更新对象
        report: 报表文本
        keyboard: 键盘按钮列表
    """
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        if update.callback_query:
            await update.callback_query.edit_message_text(
                report, reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(report, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"显示收入明细失败: {e}", exc_info=True)
        if update.callback_query:
            await update.callback_query.message.reply_text(
                report, reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(report, reply_markup=reply_markup)


async def show_income_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """显示今日收入明细（仅管理员）"""
    user_id = update.effective_user.id if update.effective_user else None

    if not _is_admin(user_id):
        await update.message.reply_text("❌ 此功能仅限管理员使用")
        return

    date = get_daily_period_date()
    records = await db_operations.get_income_records(date, date)

    report, has_more, total_pages, current_type = await generate_income_report(
        records, date, date, f"今日收入明细 ({date})", page=1, items_per_page=0
    )

    keyboard = _build_income_detail_keyboard(total_pages, current_type, date)
    await _send_income_detail_message(update, report, keyboard)


@error_handler
async def handle_income_query_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str
):
    """处理收入明细查询输入"""
    user_id = update.effective_user.id if update.effective_user else None

    if not _is_admin(user_id):
        await update.message.reply_text("❌ 此功能仅限管理员使用")
        context.user_data["state"] = None
        return

    dates = text.split()
    if len(dates) == 1:
        start_date = end_date = dates[0]
    elif len(dates) == 2:
        start_date = dates[0]
        end_date = dates[1]
    else:
        await update.message.reply_text(
            ErrorMessages.invalid_date_format()
            + "\n格式1 (单日): 2024-01-01\n格式2 (范围): 2024-01-01 2024-01-31"
        )
        return

    # 验证日期格式
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        await update.message.reply_text(ErrorMessages.invalid_date_format())
        context.user_data["state"] = None
        return

    records = await db_operations.get_income_records(start_date, end_date)

    report, has_more, total_pages, current_type = await generate_income_report(
        records,
        start_date,
        end_date,
        f"收入明细 ({start_date} 至 {end_date})",
        page=1,
        items_per_page=0,
    )

    keyboard = []

    # 由于 items_per_page=0，不会分页，所以不显示分页按钮
    # 当前默认显示全部

    keyboard.append(
        [InlineKeyboardButton("🔙 返回", callback_data="income_view_today")]
    )
    await update.message.reply_text(report, reply_markup=InlineKeyboardMarkup(keyboard))
    context.user_data["state"] = None
