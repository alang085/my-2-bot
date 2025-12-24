"""报表相关处理器"""

import logging
from datetime import datetime
from typing import Optional

import pytz
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

import db_operations
from config import ADMIN_IDS
from decorators import authorized_required, error_handler, private_chat_only
from utils.date_helpers import get_daily_period_date

logger = logging.getLogger(__name__)


async def generate_report_text(
    period_type: str,
    start_date: str,
    end_date: str,
    group_id: Optional[str] = None,
    show_expenses: bool = True,
) -> str:
    """生成报表文本

    报表数据来源说明：
    - 全局报表（group_id=None）：
      * current_data: financial_data表（全局统计数据）
      * stats: daily_data表按日期范围汇总，group_id=NULL（全局日结数据）

    - 归属报表（group_id有值）：
      * current_data: grouped_data表（该归属ID的累计统计数据）
      * stats: daily_data表按日期范围汇总，group_id=指定值（该归属ID的日结数据）
      * 开销数据：使用全局数据（开销不按归属ID存储）
      * 现金余额：使用全局数据（现金余额是全局的）

    数据一致性保证：
    - grouped_data的数据应该等于该归属ID在daily_data表中的数据累计
    - 所有统计数据应该与income_records表中的明细数据一致
    """
    # 获取当前状态数据（资金和有效订单）
    if group_id:
        # 归属报表：使用grouped_data表获取该归属ID的累计统计数据
        current_data = await db_operations.get_grouped_data(group_id)
        if not current_data:
            current_data = {"valid_orders": 0, "valid_amount": 0.0, "liquid_funds": 0.0}
        report_title = f"归属ID {group_id} 的报表"
    else:
        # 全局报表：使用financial_data表获取全局统计数据
        current_data = await db_operations.get_financial_data()
        if not current_data:
            current_data = {"valid_orders": 0, "valid_amount": 0.0, "liquid_funds": 0.0}
        report_title = "全局报表"

    # 获取周期统计数据（从daily_data表按日期范围和归属ID汇总）
    # 如果group_id为None，获取全局数据（group_id=NULL的记录）
    # 如果group_id有值，获取该归属ID的数据
    stats = await db_operations.get_stats_by_date_range(start_date, end_date, group_id)
    if not stats:
        stats = {
            "liquid_flow": 0.0,
            "new_clients": 0,
            "new_clients_amount": 0.0,
            "old_clients": 0,
            "old_clients_amount": 0.0,
            "interest": 0.0,
            "completed_orders": 0,
            "completed_amount": 0.0,
            "breach_orders": 0,
            "breach_amount": 0.0,
            "breach_end_orders": 0,
            "breach_end_amount": 0.0,
            "company_expenses": 0.0,
            "other_expenses": 0.0,
        }

    # 如果按归属ID查询，需要单独获取全局开销数据（开销是全局的，不按归属ID存储）
    if group_id:
        try:
            # 开销数据是全局的，需要从全局daily_data获取
            global_expense_stats = await db_operations.get_stats_by_date_range(
                start_date, end_date, None
            )
            if global_expense_stats:
                stats["company_expenses"] = global_expense_stats.get("company_expenses", 0.0)
                stats["other_expenses"] = global_expense_stats.get("other_expenses", 0.0)

            # 现金余额使用全局数据（现金余额是全局的，不是按归属ID存储的）
            global_financial_data = await db_operations.get_financial_data()
            if global_financial_data:
                current_data["liquid_funds"] = global_financial_data.get("liquid_funds", 0.0)
        except Exception as e:
            logger.error(f"获取全局数据失败: {e}", exc_info=True)
            # 使用默认值
            stats["company_expenses"] = stats.get("company_expenses", 0.0)
            stats["other_expenses"] = stats.get("other_expenses", 0.0)
            current_data["liquid_funds"] = current_data.get("liquid_funds", 0.0)

    # 格式化时间
    tz = pytz.timezone("Asia/Shanghai")
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M")

    period_display = ""
    if period_type == "today":
        period_display = f"今日数据 ({start_date})"
    elif period_type == "month":
        # 安全地截取年月部分
        try:
            period_display = f"本月数据 ({start_date[:7] if len(start_date) >= 7 else start_date})"
        except Exception:
            period_display = f"本月数据 ({start_date})"
    else:
        period_display = f"区间数据 ({start_date} 至 {end_date})"

    report = (
        f"=== {report_title} ===\n"
        f"📅 {now}\n"
        f"{'─' * 25}\n"
        f"💰 【当前状态】\n"
        f"有效订单数: {current_data.get('valid_orders', 0)}\n"
        f"有效订单金额: {current_data.get('valid_amount', 0.0):.2f}\n"
        f"{'─' * 25}\n"
        f"📈 【{period_display}】\n"
        f"流动资金: {stats.get('liquid_flow', 0.0):.2f}\n"
        f"新客户数: {stats.get('new_clients', 0)}\n"
        f"新客户金额: {stats.get('new_clients_amount', 0.0):.2f}\n"
        f"老客户数: {stats.get('old_clients', 0)}\n"
        f"老客户金额: {stats.get('old_clients_amount', 0.0):.2f}\n"
        f"利息收入: {stats.get('interest', 0.0):.2f}\n"
        f"完成订单数: {stats.get('completed_orders', 0)}\n"
        f"完成订单金额: {stats.get('completed_amount', 0.0):.2f}\n"
        f"违约订单数: {stats.get('breach_orders', 0)}\n"
        f"违约订单金额: {stats.get('breach_amount', 0.0):.2f}\n"
        f"违约完成订单数: {stats.get('breach_end_orders', 0)}\n"
        f"违约完成金额: {stats.get('breach_end_amount', 0.0):.2f}\n"
    )

    # 如果是归属报表，添加盈余计算
    # 盈余 = 利息收入 + 违约完成订单金额 - 违约订单金额
    if group_id:
        surplus = (
            stats.get("interest", 0.0)
            + stats.get("breach_end_amount", 0.0)
            - stats.get("breach_amount", 0.0)
        )
        # 格式化显示：添加千分位分隔符和符号
        surplus_str = f"{surplus:,.2f}"
        if surplus > 0:
            report += f"盈余: +{surplus_str}\n"
        elif surplus < 0:
            report += f"盈余: {surplus_str}\n"  # 负数自带负号
        else:
            report += f"盈余: {surplus_str}\n"

    # 如果要求显示开销与余额，则添加
    if show_expenses:
        report += (
            f"{'─' * 25}\n"
            f"💸 【开销与余额】\n"
            f"公司开销: {stats.get('company_expenses', 0.0):.2f}\n"
            f"其他开销: {stats.get('other_expenses', 0.0):.2f}\n"
            f"现金余额: {current_data.get('liquid_funds', 0.0):.2f}\n"
        )

    return report


@error_handler
@private_chat_only
@authorized_required
async def show_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """显示报表"""
    # 默认为今日报表
    period_type = "today"
    group_id = None

    # 处理参数
    if context.args:
        group_id = context.args[0]

    # 获取今日日期
    daily_date = get_daily_period_date()

    # 生成报表
    report_text = await generate_report_text(period_type, daily_date, daily_date, group_id)

    # 构建按钮（中文）
    keyboard = [
        [
            InlineKeyboardButton(
                "📅 月报", callback_data=f"report_view_month_{group_id if group_id else 'ALL'}"
            ),
            InlineKeyboardButton(
                "📆 日期查询", callback_data=f"report_view_query_{group_id if group_id else 'ALL'}"
            ),
        ]
    ]

    # 检查用户权限：只有管理员或授权员工可以录入开销
    user_id = update.effective_user.id if update.effective_user else None
    if user_id:
        is_admin = user_id in ADMIN_IDS
        is_authorized = await db_operations.is_user_authorized(user_id)
        if is_admin or is_authorized:
            keyboard.append(
                [
                    InlineKeyboardButton("🏢 公司开销", callback_data="report_record_company"),
                    InlineKeyboardButton("📝 其他开销", callback_data="report_record_other"),
                ]
            )

    # 如果是全局报表，显示归属查询和查找功能按钮
    if not group_id:
        keyboard.append(
            [
                InlineKeyboardButton("🔍 按归属查询", callback_data="report_menu_attribution"),
                InlineKeyboardButton("🔎 查找订单", callback_data="report_search_orders"),
            ]
        )
        # 仅管理员显示收入明细按钮
        if user_id and user_id in ADMIN_IDS:
            keyboard.append(
                [InlineKeyboardButton("💰 收入明细", callback_data="income_view_today")]
            )
    else:
        keyboard.append([InlineKeyboardButton("🔙 返回", callback_data="report_view_today_ALL")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Telegram消息最大长度限制为4096字符，如果报表太长则分段发送
    MAX_MESSAGE_LENGTH = 4096
    if len(report_text) > MAX_MESSAGE_LENGTH:
        # 分段发送
        chunks = []
        current_chunk = ""
        for line in report_text.split("\n"):
            if len(current_chunk) + len(line) + 1 > MAX_MESSAGE_LENGTH - 200:  # 留200字符余量
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = line + "\n"
            else:
                current_chunk += line + "\n"
        if current_chunk:
            chunks.append(current_chunk)

        # 发送第一段（带按钮）
        if chunks:
            first_chunk = chunks[0]
            if len(chunks) > 1:
                first_chunk += f"\n\n⚠️ 报表内容较长，已分段显示 ({len(chunks)}段)"
            await update.message.reply_text(first_chunk, reply_markup=reply_markup)

            # 发送剩余段
            for i, chunk in enumerate(chunks[1:], 2):
                await update.message.reply_text(f"[第 {i}/{len(chunks)} 段]\n\n{chunk}")
    else:
        await update.message.reply_text(report_text, reply_markup=reply_markup)


@error_handler
@private_chat_only
async def show_my_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """显示用户有权限查看的归属ID报表（仅限该归属ID）"""
    user_id = update.effective_user.id if update.effective_user else None
    if not user_id:
        await update.message.reply_text("❌ 无法获取用户信息")
        return

    # 获取用户有权限查看的归属ID
    group_id = await db_operations.get_user_group_id(user_id)
    if not group_id:
        await update.message.reply_text(
            "❌ 您没有权限查看任何归属ID的报表。\n" "请联系管理员为您分配归属ID权限。"
        )
        return

    # 默认为今日报表
    period_type = "today"
    daily_date = get_daily_period_date()

    # 生成报表（不显示开销与余额）
    report_text = await generate_report_text(
        period_type, daily_date, daily_date, group_id, show_expenses=False
    )

    # 构建按钮（简化版，不显示归属查询和查找功能）
    keyboard = [
        [
            InlineKeyboardButton("📅 月报", callback_data=f"report_view_month_{group_id}"),
            InlineKeyboardButton("📆 日期查询", callback_data=f"report_view_query_{group_id}"),
        ]
    ]

    # 检查用户权限：只有管理员或授权员工可以录入开销
    user_id = update.effective_user.id if update.effective_user else None
    if user_id:
        is_admin = user_id in ADMIN_IDS
        is_authorized = await db_operations.is_user_authorized(user_id)
        if is_admin or is_authorized:
            keyboard.append(
                [
                    InlineKeyboardButton("🏢 公司开销", callback_data="report_record_company"),
                    InlineKeyboardButton("📝 其他开销", callback_data="report_record_other"),
                ]
            )

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Telegram消息最大长度限制为4096字符，如果报表太长则分段发送
    MAX_MESSAGE_LENGTH = 4096
    if len(report_text) > MAX_MESSAGE_LENGTH:
        # 分段发送
        chunks = []
        current_chunk = ""
        for line in report_text.split("\n"):
            if len(current_chunk) + len(line) + 1 > MAX_MESSAGE_LENGTH - 200:  # 留200字符余量
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = line + "\n"
            else:
                current_chunk += line + "\n"
        if current_chunk:
            chunks.append(current_chunk)

        # 发送第一段（带按钮）
        if chunks:
            first_chunk = chunks[0]
            if len(chunks) > 1:
                first_chunk += f"\n\n⚠️ 报表内容较长，已分段显示 ({len(chunks)}段)"
            await update.message.reply_text(first_chunk, reply_markup=reply_markup)

            # 发送剩余段
            for i, chunk in enumerate(chunks[1:], 2):
                await update.message.reply_text(f"[第 {i}/{len(chunks)} 段]\n\n{chunk}")
    else:
        await update.message.reply_text(report_text, reply_markup=reply_markup)
