"""财务相关文本输入辅助函数"""

# 标准库
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# 第三方库
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

# 本地模块
import db_operations
from utils.date_helpers import get_daily_period_date
from utils.error_messages import ErrorMessages

logger = logging.getLogger(__name__)


async def _validate_admin_access(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> bool:
    """验证管理员权限

    Args:
        update: Telegram 更新对象
        context: 上下文对象

    Returns:
        是否有权限
    """
    from config import ADMIN_IDS

    user_id = update.effective_user.id if update.effective_user else None
    if not user_id or user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ 此功能仅限管理员使用")
        context.user_data["state"] = None
        return False
    return True


def _parse_and_validate_date_input(text: str) -> Tuple[Optional[str], Optional[str]]:
    """解析并验证日期输入

    Args:
        text: 输入的文本

    Returns:
        (日期字符串, 错误消息)
    """
    dates = text.split()
    if len(dates) == 1:
        date_str = dates[0]
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return date_str, None
        except ValueError:
            return None, ErrorMessages.invalid_date_format()
    elif len(dates) == 2:
        start_date = dates[0]
        end_date = dates[1]
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
            datetime.strptime(end_date, "%Y-%m-%d")
            return f"{start_date} {end_date}", None
        except ValueError:
            return None, ErrorMessages.invalid_date_format()
    else:
        error_msg = (
            "❌ 格式错误。请使用：\n格式1 (单日): 2025-12-02\n"
            "格式2 (范围): 2025-12-01 2025-12-31"
        )
        return None, error_msg


def _build_income_type_keyboard(date_str: str) -> InlineKeyboardMarkup:
    """构建收入类型选择键盘

    Args:
        date_str: 日期字符串

    Returns:
        内联键盘对象
    """
    keyboard = [
        [
            InlineKeyboardButton(
                "订单完成", callback_data=f"income_query_type_completed_{date_str}"
            ),
            InlineKeyboardButton(
                "违约完成", callback_data=f"income_query_type_breach_end_{date_str}"
            ),
        ],
        [
            InlineKeyboardButton(
                "利息收入", callback_data=f"income_query_type_interest_{date_str}"
            ),
            InlineKeyboardButton(
                "本金减少",
                callback_data=f"income_query_type_principal_reduction_{date_str}",
            ),
        ],
        [
            InlineKeyboardButton(
                "全部类型", callback_data=f"income_query_type_all_{date_str}"
            )
        ],
        [InlineKeyboardButton("🔙 取消", callback_data="income_advanced_query")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def _handle_income_query_date(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str
):
    """处理高级查询的日期输入"""
    if not await _validate_admin_access(update, context):
        return

    try:
        date_str, error_msg = _parse_and_validate_date_input(text)
        if date_str is None:
            await update.message.reply_text(error_msg)
            return

        context.user_data["income_query"] = context.user_data.get("income_query", {})
        context.user_data["income_query"]["date"] = date_str
        context.user_data["state"] = None

        keyboard = _build_income_type_keyboard(date_str)
        await update.message.reply_text(
            f"📅 已选择日期: {date_str}\n\n" "🔍 请选择收入类型：",
            reply_markup=keyboard,
        )

    except Exception as e:
        logger.error(f"处理日期输入出错: {e}", exc_info=True)
        await update.message.reply_text(f"⚠️ 错误: {e}")
        context.user_data["state"] = None


def _parse_expense_query_dates(text: str) -> Tuple[Optional[str], Optional[str]]:
    """解析开销查询日期

    Args:
        text: 输入文本

    Returns:
        (开始日期, 结束日期) 或 (None, None)
    """
    dates = text.split()
    if len(dates) == 1:
        return dates[0], dates[0]
    elif len(dates) == 2:
        return dates[0], dates[1]
    else:
        return None, None


def _build_expense_query_message(
    expense_type: str, start_date: str, end_date: str, records: List[Dict]
) -> str:
    """构建开销查询消息

    Args:
        expense_type: 开销类型
        start_date: 开始日期
        end_date: 结束日期
        records: 记录列表

    Returns:
        消息文本
    """
    title = "Company Expense" if expense_type == "company" else "Other Expense"
    msg = f"🔍 {title} Query ({start_date} to {end_date}):\n\n"

    if not records:
        msg += "No records found.\n"
    else:
        display_records = records[:20] if len(records) > 20 else records
        real_total = sum(r["amount"] for r in records)

        for r in display_records:
            msg += f"[{r['date']}] {r['amount']:.2f} - {r['note'] or 'No Note'}\n"

        if len(records) > 20:
            msg += f"\n... (Total {len(records)} records, showing latest 20)\n"
        msg += f"\nTotal: {real_total:.2f}\n"

    return msg


async def _handle_expense_query(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, user_state: str
):
    """处理开销查询"""
    try:
        start_date, end_date = _parse_expense_query_dates(text)
        if not start_date or not end_date:
            await update.message.reply_text(
                "❌ Format Error. Use 'YYYY-MM-DD' or 'YYYY-MM-DD YYYY-MM-DD'"
            )
            return

        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")

        expense_type = "company" if user_state == "QUERY_EXPENSE_COMPANY" else "other"
        records = await db_operations.get_expense_records(
            start_date, end_date, expense_type
        )

        msg = _build_expense_query_message(expense_type, start_date, end_date, records)

        back_callback = (
            "report_record_company"
            if expense_type == "company"
            else "report_record_other"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data=back_callback)]]
        await update.message.reply_text(
            msg, reply_markup=InlineKeyboardMarkup(keyboard)
        )
        context.user_data["state"] = None

    except ValueError:
        await update.message.reply_text("❌ Invalid Date Format. Use YYYY-MM-DD")
    except Exception as e:
        logger.error(f"查询开销出错: {e}", exc_info=True)
        await update.message.reply_text(f"⚠️ Error: {e}")


async def _validate_expense_permission(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: Optional[int]
) -> bool:
    """验证开销录入权限

    Returns:
        是否有权限
    """
    if not user_id:
        await update.message.reply_text("❌ 无法获取用户信息")
        context.user_data["state"] = None
        return False

    from utils.handler_helpers import check_user_permissions

    is_admin, is_authorized, _ = await check_user_permissions(user_id)
    if not is_admin and not is_authorized:
        await update.message.reply_text("❌ 您没有权限录入开销（仅限员工和管理员）")
        context.user_data["state"] = None
        return False

    return True


def _parse_expense_input(text: str) -> tuple[float, str]:
    """解析开销输入

    Returns:
        (amount, note)
    """
    parts = text.strip().split(maxsplit=1)
    if len(parts) < 2:
        amount_str = parts[0]
        note = "No Note"
    else:
        amount_str, note = parts

    amount = float(amount_str)
    if amount <= 0:
        raise ValueError("Amount must be positive")

    return amount, note


async def _record_expense_operation(
    update: Update,
    user_id: int,
    expense_type: str,
    amount: float,
    note: str,
    date_str: str,
    expense_id: int,
) -> None:
    """记录开销操作历史"""
    current_chat_id = update.effective_chat.id if update.effective_chat else None
    if current_chat_id and user_id:
        await db_operations.record_operation(
            user_id=user_id,
            operation_type="expense",
            operation_data={
                "amount": amount,
                "type": expense_type,
                "note": note,
                "date": date_str,
                "expense_record_id": expense_id,
            },
            chat_id=current_chat_id,
        )


async def _send_expense_success_message(
    update: Update, expense_type: str, amount: float, note: str
) -> None:
    """发送开销记录成功消息"""
    financial_data = await db_operations.get_financial_data()
    type_name = "Company" if expense_type == "company" else "Other"
    await update.message.reply_text(
        f"✅ Expense Recorded\n"
        f"Type: {type_name}\n"
        f"Amount: {amount:.2f}\n"
        f"Note: {note}\n"
        f"Current Balance: {financial_data['liquid_funds']:.2f}"
    )


async def _handle_expense_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, user_state: str
):
    """处理开销输入"""
    user_id = update.effective_user.id if update.effective_user else None
    if not await _validate_expense_permission(update, context, user_id):
        return

    try:
        amount, note = _parse_expense_input(text)

        expense_type = "company" if user_state == "WAITING_EXPENSE_COMPANY" else "other"
        date_str = get_daily_period_date()

        expense_id = await db_operations.record_expense(
            date_str, expense_type, amount, note
        )

        from handlers.module5_data.undo_handlers import reset_undo_count

        await _record_expense_operation(
            update, user_id, expense_type, amount, note, date_str, expense_id
        )
        reset_undo_count(context, user_id)
        await _send_expense_success_message(update, expense_type, amount, note)
        context.user_data["state"] = None

    except ValueError:
        await update.message.reply_text(
            ErrorMessages.validation_error("格式", "示例: 100 Server Cost")
        )
    except Exception as e:
        logger.error(f"记录开销时出错: {e}", exc_info=True)
        await update.message.reply_text(f"⚠️ Error: {e}")
