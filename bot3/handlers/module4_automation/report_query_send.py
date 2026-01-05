"""报表查询 - 发送模块

包含发送报表结果的逻辑。
"""

from typing import List, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from handlers.module5_data.report_handlers import generate_report_text


def _build_report_query_keyboard(group_id: Optional[str]) -> InlineKeyboardMarkup:
    """构建报表查询键盘

    Args:
        group_id: 归属ID

    Returns:
        内联键盘
    """
    group_key = group_id if group_id else "ALL"
    keyboard = [
        [
            InlineKeyboardButton(
                "📄 今日报表", callback_data=f"report_view_today_{group_key}"
            ),
            InlineKeyboardButton(
                "📅 月报", callback_data=f"report_view_month_{group_key}"
            ),
        ],
        [
            InlineKeyboardButton(
                "📆 日期查询", callback_data=f"report_view_query_{group_key}"
            )
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def _split_report_text(report_text: str) -> List[str]:
    """将报表文本分段

    Args:
        report_text: 报表文本

    Returns:
        分段列表
    """
    MAX_MESSAGE_LENGTH = 4096
    if len(report_text) <= MAX_MESSAGE_LENGTH:
        return [report_text]

    chunks = []
    current_chunk = ""
    for line in report_text.split("\n"):
        if len(current_chunk) + len(line) + 1 > MAX_MESSAGE_LENGTH - 200:
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


async def send_report_query_result(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    start_date: str,
    end_date: str,
    group_id: Optional[str],
    show_expenses: bool,
) -> None:
    """发送报表查询结果

    Args:
        update: Telegram更新对象
        context: 上下文对象
        start_date: 开始日期
        end_date: 结束日期
        group_id: 归属ID
        show_expenses: 是否显示开销
    """
    report_text = await generate_report_text(
        "query", start_date, end_date, group_id, show_expenses=show_expenses
    )

    reply_markup = _build_report_query_keyboard(group_id)
    chunks = _split_report_text(report_text)

    if len(chunks) == 1:
        await update.message.reply_text(report_text, reply_markup=reply_markup)
    else:
        await _send_report_chunks(update, chunks, reply_markup)

    context.user_data["state"] = None
