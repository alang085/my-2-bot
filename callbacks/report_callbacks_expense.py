"""报表开销相关回调处理"""

import logging
from datetime import datetime

import pytz
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from callbacks.report_callbacks_base import check_expense_permission
from handlers.data_access import get_expense_records_for_callback
from utils.date_helpers import get_daily_period_date

logger = logging.getLogger(__name__)


async def handle_expense_company_today(query, user_id: int, context: ContextTypes.DEFAULT_TYPE):
    """处理公司开销今日回调"""
    logger.debug(f"handle_expense_company_today: processing for user {user_id}")
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"handle_expense_company_today: query.answer() failed: {e}")

    try:
        date = get_daily_period_date()
        records = await get_expense_records_for_callback(date, date, expense_type="company")
    except Exception as e:
        logger.error(
            f"handle_expense_company_today: failed to get expense records: {e}", exc_info=True
        )
        try:
            await query.answer("❌ 获取开销记录失败", show_alert=True)
        except Exception:
            pass
        return

    msg = f"🏢 公司开销今日 ({date}):\n\n"
    if not records:
        msg += "无记录\n"
    else:
        total = 0
        for i, r in enumerate(records, 1):
            msg += f"{i}. {r['amount']:.2f} - {r['note'] or '无备注'}\n"
            total += r["amount"]
        msg += f"\n总计: {total:.2f}\n"

    keyboard = []

    # 只有有权限的用户才显示添加开销按钮
    if await check_expense_permission(user_id):
        keyboard.append(
            [InlineKeyboardButton("➕ 添加开销", callback_data="report_add_expense_company")]
        )

    keyboard.extend(
        [
            [
                InlineKeyboardButton("📅 本月", callback_data="report_expense_month_company"),
                InlineKeyboardButton("📆 查询", callback_data="report_expense_query_company"),
            ],
            [InlineKeyboardButton("🔙 返回", callback_data="report_view_today_ALL")],
        ]
    )
    try:
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
        logger.info("handle_expense_company_today: successfully edited message")
    except Exception as e:
        logger.error(f"编辑公司开销消息失败: {e}", exc_info=True)
        try:
            if query.message:
                await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
                logger.info("handle_expense_company_today: successfully sent new message")
            else:
                await query.answer("❌ 显示开销记录失败（消息不存在）", show_alert=True)
        except Exception as e2:
            logger.error(f"发送公司开销消息失败: {e2}", exc_info=True)
            try:
                await query.answer("❌ 显示开销记录失败", show_alert=True)
            except Exception:
                pass


async def handle_expense_company_month(query, context: ContextTypes.DEFAULT_TYPE):
    """处理公司开销本月回调"""
    await query.answer()
    tz = pytz.timezone("Asia/Shanghai")
    now = datetime.now(tz)
    start_date = now.replace(day=1).strftime("%Y-%m-%d")
    end_date = get_daily_period_date()

    records = await get_expense_records_for_callback(start_date, end_date, expense_type="company")

    msg = f"🏢 公司开销本月 ({start_date} 至 {end_date}):\n\n"
    if not records:
        msg += "无记录\n"
    else:
        # 限制显示数量，防止消息过长（显示最新的20条）
        display_records = records[:20] if len(records) > 20 else records

        for r in display_records:
            msg += f"[{r['date']}] {r['amount']:.2f} - {r['note'] or '无备注'}\n"

        # 计算总额（所有记录）
        real_total = sum(r["amount"] for r in records)
        if len(records) > 20:
            msg += f"\n... (共 {len(records)} 条记录，显示最近20条)\n"
        msg += f"\n总计: {real_total:.2f}\n"

    keyboard = [[InlineKeyboardButton("🔙 返回", callback_data="report_record_company")]]
    try:
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        logger.error(f"编辑消息失败: {e}", exc_info=True)
        try:
            if query.message:
                await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                await query.answer("❌ 显示失败（消息不存在）", show_alert=True)
        except Exception as e:
            logger.error(f"发送消息失败: {e}", exc_info=True)
            try:
                await query.answer("❌ 显示失败", show_alert=True)
            except Exception:
                pass


async def handle_expense_company_query(query, context: ContextTypes.DEFAULT_TYPE):
    """处理公司开销查询回调"""
    await query.answer()
    try:
        if query.message:
            await query.message.reply_text(
                "🏢 请输入日期范围：\n"
                "格式1 (单日): 2024-01-01\n"
                "格式2 (范围): 2024-01-01 2024-01-31\n"
                "输入 'cancel' 取消"
            )
        else:
            await query.answer("请输入日期范围", show_alert=True)
    except Exception as e:
        logger.error(f"发送日期范围提示失败: {e}", exc_info=True)
        await query.answer("请输入日期范围", show_alert=True)
    context.user_data["state"] = "QUERY_EXPENSE_COMPANY"


async def handle_expense_company_add(query, user_id: int, context: ContextTypes.DEFAULT_TYPE):
    """处理添加公司开销回调"""
    await query.answer()
    # 检查权限：只有管理员或授权员工可以录入开销
    if not user_id:
        await query.answer("❌ 无法获取用户信息", show_alert=True)
        return

    if not await check_expense_permission(user_id):
        await query.answer("❌ 您没有权限录入开销（仅限员工和管理员）", show_alert=True)
        return

    try:
        if query.message:
            await query.message.reply_text(
                "🏢 请输入金额和备注：\n" "格式: 金额 备注\n" "示例: 100 服务器费用"
            )
        else:
            await query.answer("请输入金额和备注", show_alert=True)
    except Exception as e:
        logger.error(f"发送金额备注提示失败: {e}", exc_info=True)
        await query.answer("请输入金额和备注", show_alert=True)
    context.user_data["state"] = "WAITING_EXPENSE_COMPANY"


async def handle_expense_other_today(query, user_id: int, context: ContextTypes.DEFAULT_TYPE):
    """处理其他开销今日回调"""
    logger.debug(f"handle_expense_other_today: processing for user {user_id}")
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"handle_expense_other_today: query.answer() failed: {e}")

    try:
        date = get_daily_period_date()
        records = await get_expense_records_for_callback(date, date, expense_type="other")
    except Exception as e:
        logger.error(
            f"handle_expense_other_today: failed to get expense records: {e}", exc_info=True
        )
        try:
            await query.answer("❌ 获取开销记录失败", show_alert=True)
        except Exception:
            pass
        return

    msg = f"📝 其他开销今日 ({date}):\n\n"
    if not records:
        msg += "无记录\n"
    else:
        total = 0
        for i, r in enumerate(records, 1):
            msg += f"{i}. {r['amount']:.2f} - {r['note'] or '无备注'}\n"
            total += r["amount"]
        msg += f"\n总计: {total:.2f}\n"

    keyboard = []

    # 只有有权限的用户才显示添加开销按钮
    if await check_expense_permission(user_id):
        keyboard.append(
            [InlineKeyboardButton("➕ 添加开销", callback_data="report_add_expense_other")]
        )

    keyboard.extend(
        [
            [
                InlineKeyboardButton("📅 本月", callback_data="report_expense_month_other"),
                InlineKeyboardButton("📆 查询", callback_data="report_expense_query_other"),
            ],
            [InlineKeyboardButton("🔙 返回", callback_data="report_view_today_ALL")],
        ]
    )
    try:
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
        logger.info("handle_expense_other_today: successfully edited message")
    except Exception as e:
        logger.error(f"编辑其他开销消息失败: {e}", exc_info=True)
        try:
            if query.message:
                await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
                logger.info("handle_expense_other_today: successfully sent new message")
            else:
                await query.answer("❌ 显示开销记录失败（消息不存在）", show_alert=True)
        except Exception as e2:
            logger.error(f"发送其他开销消息失败: {e2}", exc_info=True)
            try:
                await query.answer("❌ 显示开销记录失败", show_alert=True)
            except Exception:
                pass


async def handle_expense_other_month(query, context: ContextTypes.DEFAULT_TYPE):
    """处理其他开销本月回调"""
    await query.answer()
    tz = pytz.timezone("Asia/Shanghai")
    now = datetime.now(tz)
    start_date = now.replace(day=1).strftime("%Y-%m-%d")
    end_date = get_daily_period_date()

    records = await get_expense_records_for_callback(start_date, end_date, expense_type="other")

    msg = f"📝 其他开销本月 ({start_date} 至 {end_date}):\n\n"
    if not records:
        msg += "无记录\n"
    else:
        # 显示最新的20条记录
        display_records = records[:20] if len(records) > 20 else records
        for r in display_records:
            msg += f"[{r['date']}] {r['amount']:.2f} - {r['note'] or '无备注'}\n"

        real_total = sum(r["amount"] for r in records)
        if len(records) > 20:
            msg += f"\n... (共 {len(records)} 条记录，显示最近20条)\n"
        msg += f"\n总计: {real_total:.2f}\n"

    keyboard = [[InlineKeyboardButton("🔙 返回", callback_data="report_record_other")]]
    try:
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        logger.error(f"编辑消息失败: {e}", exc_info=True)
        try:
            if query.message:
                await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                await query.answer("❌ 显示失败（消息不存在）", show_alert=True)
        except Exception as e:
            logger.error(f"发送消息失败: {e}", exc_info=True)
            try:
                await query.answer("❌ 显示失败", show_alert=True)
            except Exception:
                pass


async def handle_expense_other_query(query, context: ContextTypes.DEFAULT_TYPE):
    """处理其他开销查询回调"""
    await query.answer()
    try:
        if query.message:
            await query.message.reply_text(
                "📝 请输入日期范围：\n"
                "格式1 (单日): 2024-01-01\n"
                "格式2 (范围): 2024-01-01 2024-01-31\n"
                "输入 'cancel' 取消"
            )
        else:
            await query.answer("请输入日期范围", show_alert=True)
    except Exception as e:
        logger.error(f"发送日期范围提示失败: {e}", exc_info=True)
        await query.answer("请输入日期范围", show_alert=True)
    context.user_data["state"] = "QUERY_EXPENSE_OTHER"


async def handle_expense_other_add(query, user_id: int, context: ContextTypes.DEFAULT_TYPE):
    """处理添加其他开销回调"""
    await query.answer()
    # 检查权限：只有管理员或授权员工可以录入开销
    if not user_id:
        await query.answer("❌ 无法获取用户信息", show_alert=True)
        return

    if not await check_expense_permission(user_id):
        await query.answer("❌ 您没有权限录入开销（仅限员工和管理员）", show_alert=True)
        return

    try:
        if query.message:
            await query.message.reply_text(
                "📝 请输入金额和备注：\n" "格式: 金额 备注\n" "示例: 50 办公用品"
            )
        else:
            await query.answer("请输入金额和备注", show_alert=True)
    except Exception as e:
        logger.error(f"发送金额备注提示失败: {e}", exc_info=True)
        await query.answer("请输入金额和备注", show_alert=True)
    context.user_data["state"] = "WAITING_EXPENSE_OTHER"
