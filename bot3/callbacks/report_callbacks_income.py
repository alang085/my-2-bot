"""报表回调处理器 - 收入明细相关

包含收入明细查询相关的所有回调处理函数。
"""

# 标准库
import logging
from datetime import datetime

import pytz
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from config import ADMIN_IDS
from handlers.data_access import (get_all_group_ids_for_callback,
                                  get_income_records_for_callback)
from constants import INCOME_TYPES
from handlers.module2_finance.income_handlers import generate_income_report
from utils.callback_helpers import safe_edit_message_text
from utils.date_helpers import get_daily_period_date
from utils.income_helpers import get_income_type_mapping

logger = logging.getLogger(__name__)


async def handle_income_view_today(
    query, user_id: int, context: ContextTypes.DEFAULT_TYPE
):
    """处理今日收入明细回调"""
    if not user_id or user_id not in ADMIN_IDS:
        await query.answer("❌ 此功能仅限管理员使用", show_alert=True)
        return

    await query.answer()
    date = get_daily_period_date()
    records = await get_income_records_for_callback(date, date)

    report, has_more, total_pages, current_type = await generate_income_report(
        records, date, date, f"今日收入明细 ({date})", page=1, items_per_page=0
    )

    keyboard = []

    # 如果有分页，添加分页按钮
    if total_pages > 1:
        page_buttons = []
        type_for_callback = "None" if current_type is None else current_type
        if 1 < total_pages:
            page_buttons.append(
                InlineKeyboardButton(
                    "下一页 ▶️",
                    callback_data=f"income_page_{type_for_callback}|2|{date}|{date}",
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

    try:
        await safe_edit_message_text(
            query, report, reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"编辑收入明细消息失败: {e}", exc_info=True)
        try:
            if query.message:
                await query.message.reply_text(
                    report, reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await query.answer("❌ 显示失败（消息不存在）", show_alert=True)
        except Exception as e2:
            logger.error(f"发送报表消息失败: {e2}", exc_info=True)
            await query.answer("❌ 显示失败", show_alert=True)


async def handle_income_view_month(
    query, user_id: int, context: ContextTypes.DEFAULT_TYPE
):
    """处理本月收入明细回调"""
    if not user_id or user_id not in ADMIN_IDS:
        await query.answer("❌ 此功能仅限管理员使用", show_alert=True)
        return

    await query.answer()
    tz = pytz.timezone("Asia/Shanghai")
    now = datetime.now(tz)
    start_date = now.replace(day=1).strftime("%Y-%m-%d")
    end_date = get_daily_period_date()

    records = await get_income_records_for_callback(start_date, end_date)

    report, has_more, total_pages, current_type = await generate_income_report(
        records,
        start_date,
        end_date,
        f"本月收入明细 ({start_date} 至 {end_date})",
        page=1,
        items_per_page=0,
    )

    keyboard = []

    # 如果有分页，添加分页按钮
    if total_pages > 1:
        page_buttons = []
        type_for_callback = "None" if current_type is None else current_type
        if 1 < total_pages:
            page_buttons.append(
                InlineKeyboardButton(
                    "下一页 ▶️",
                    callback_data=f"income_page_{type_for_callback}|2|{start_date}|{end_date}",
                )
            )
        if page_buttons:
            keyboard.append(page_buttons)

    keyboard.extend(
        [
            [
                InlineKeyboardButton("📄 今日收入", callback_data="income_view_today"),
                InlineKeyboardButton("📆 日期查询", callback_data="income_view_query"),
            ],
            [
                InlineKeyboardButton(
                    "🔙 返回报表", callback_data="report_view_today_ALL"
                )
            ],
        ]
    )

    try:
        await safe_edit_message_text(
            query, report, reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"编辑收入明细消息失败: {e}", exc_info=True)
        try:
            if query.message:
                await query.message.reply_text(
                    report, reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await query.answer("❌ 显示失败（消息不存在）", show_alert=True)
        except Exception as e2:
            logger.error(f"发送报表消息失败: {e2}", exc_info=True)
            await query.answer("❌ 显示失败", show_alert=True)


async def handle_income_view_query(
    query, user_id: int, context: ContextTypes.DEFAULT_TYPE
):
    """处理收入明细日期查询回调"""
    if not user_id or user_id not in ADMIN_IDS:
        await query.answer("❌ 此功能仅限管理员使用", show_alert=True)
        return

    await query.answer()
    try:
        if query.message:
            await query.message.reply_text(
                "📆 请输入查询日期范围：\n"
                "格式1 (单日): 2024-01-01\n"
                "格式2 (范围): 2024-01-01 2024-01-31\n"
                "输入 'cancel' 取消"
            )
        else:
            await query.answer("请输入查询日期范围", show_alert=True)
    except Exception as e:
        logger.error(f"发送查询日期范围提示失败: {e}", exc_info=True)
        await query.answer("请输入查询日期范围", show_alert=True)
    context.user_data["state"] = "QUERY_INCOME"


async def handle_income_view_by_type(
    query, user_id: int, context: ContextTypes.DEFAULT_TYPE
):
    """处理按类型查看收入明细回调"""
    if not user_id or user_id not in ADMIN_IDS:
        await query.answer("❌ 此功能仅限管理员使用", show_alert=True)
        return

    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton("订单完成", callback_data="income_type_completed"),
            InlineKeyboardButton("违约完成", callback_data="income_type_breach_end"),
        ],
        [
            InlineKeyboardButton("利息收入", callback_data="income_type_interest"),
            InlineKeyboardButton(
                "本金减少", callback_data="income_type_principal_reduction"
            ),
        ],
        [InlineKeyboardButton("🔍 高级查询", callback_data="income_advanced_query")],
        [InlineKeyboardButton("🔙 返回", callback_data="income_view_today")],
    ]

    await safe_edit_message_text(
        query,
        "🔍 请选择要查询的收入类型：\n\n或者使用高级查询进行多条件筛选",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_income_advanced_query(
    query, user_id: int, context: ContextTypes.DEFAULT_TYPE
):
    """处理高级查询回调"""
    if not user_id or user_id not in ADMIN_IDS:
        await query.answer("❌ 此功能仅限管理员使用", show_alert=True)
        return

    await query.answer()
    # 初始化查询条件
    context.user_data["income_query"] = {"date": None, "type": None, "group_id": None}

    keyboard = [
        [InlineKeyboardButton("📅 选择日期", callback_data="income_query_step_date")],
        [InlineKeyboardButton("🔙 返回", callback_data="income_view_by_type")],
    ]

    await safe_edit_message_text(
        query,
        "🔍 高级查询\n\n"
        "请逐步选择查询条件：\n"
        "1️⃣ 日期（必选）\n"
        "2️⃣ 收入类型（可选）\n"
        "3️⃣ 归属ID/群名（可选）\n\n"
        "当前状态：未设置",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_income_query_step_date(
    query, user_id: int, context: ContextTypes.DEFAULT_TYPE
):
    """处理高级查询日期选择回调"""
    if not user_id or user_id not in ADMIN_IDS:
        await query.answer("❌ 此功能仅限管理员使用", show_alert=True)
        return

    await query.answer()
    try:
        if query.message:
            await query.message.reply_text(
                "📅 请输入查询日期：\n"
                "格式: YYYY-MM-DD\n"
                "示例: 2025-12-02\n"
                "输入 'cancel' 取消\n\n"
                "或输入日期范围（用空格分隔）：\n"
                "示例: 2025-12-01 2025-12-31"
            )
        else:
            await query.answer("请输入查询日期", show_alert=True)
    except Exception as e:
        logger.error(f"发送查询日期提示失败: {e}", exc_info=True)
        await query.answer("请输入查询日期", show_alert=True)
    context.user_data["state"] = "INCOME_QUERY_DATE"


async def handle_income_query_step_type(
    query, user_id: int, context: ContextTypes.DEFAULT_TYPE, data: str
):
    """处理高级查询类型选择回调"""
    if not user_id or user_id not in ADMIN_IDS:
        await query.answer("❌ 此功能仅限管理员使用", show_alert=True)
        return

    await query.answer()
    # 保存日期
    date_str = data.replace("income_query_step_type_", "")
    context.user_data["income_query"]["date"] = date_str

    # 选择类型
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
        [InlineKeyboardButton("🔙 返回", callback_data="income_advanced_query")],
    ]

    await safe_edit_message_text(
        query,
        f"📅 已选择日期: {date_str}\n\n" "🔍 请选择收入类型：",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_income_query_type(
    query, user_id: int, context: ContextTypes.DEFAULT_TYPE, data: str
):
    """处理高级查询类型选择回调"""
    if not user_id or user_id not in ADMIN_IDS:
        await query.answer("❌ 此功能仅限管理员使用", show_alert=True)
        return

    await query.answer()
    # 解析参数: income_query_type_{type}_{date}
    parts = data.replace("income_query_type_", "").split("_", 1)
    income_type = parts[0]
    date_str = (
        parts[1]
        if len(parts) > 1
        else context.user_data.get("income_query", {}).get("date")
    )

    # 保存类型（如果是 all，设为 None）
    if income_type == "all":
        context.user_data["income_query"]["type"] = None
        income_type = None
    else:
        context.user_data["income_query"]["type"] = income_type

    # 获取所有归属ID
    all_group_ids = await get_all_group_ids_for_callback()

    keyboard = []
    row = []
    for gid in sorted(all_group_ids):
        row.append(
            InlineKeyboardButton(
                gid,
                callback_data=f"income_query_group_{gid}_{income_type or 'all'}_{date_str}",
            )
        )
        if len(row) == 4:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    # 添加"全部"和"全局"选项
    keyboard.append(
        [
            InlineKeyboardButton(
                "全部归属ID",
                callback_data=f"income_query_group_all_{income_type or 'all'}_{date_str}",
            ),
            InlineKeyboardButton(
                "全局",
                callback_data=f"income_query_group_null_{income_type or 'all'}_{date_str}",
            ),
        ]
    )

    keyboard.append(
        [
            InlineKeyboardButton(
                "🔙 返回", callback_data=f"income_query_step_type_{date_str}"
            )
        ]
    )

    type_display = (
        {
            "completed": "订单完成",
            "breach_end": "违约完成",
            "interest": "利息收入",
            "principal_reduction": "本金减少",
        }.get(income_type, "全部类型")
        if income_type
        else "全部类型"
    )

    await safe_edit_message_text(
        query,
        f"📅 日期: {date_str}\n"
        f"🔍 类型: {type_display}\n\n"
        "📋 请选择归属ID/群名：",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_income_query_group(
    query, user_id: int, context: ContextTypes.DEFAULT_TYPE, data: str
):
    """处理高级查询归属ID选择回调"""
    if not user_id or user_id not in ADMIN_IDS:
        await query.answer("❌ 此功能仅限管理员使用", show_alert=True)
        return

    await query.answer()
    # 解析参数: income_query_group_{group_id}_{type}_{date}
    parts = data.replace("income_query_group_", "").split("_")
    group_id = parts[0]
    income_type = parts[1] if len(parts) > 1 else "all"
    date_str = (
        parts[2]
        if len(parts) > 2
        else context.user_data.get("income_query", {}).get("date")
    )

    # 处理 group_id
    if group_id == "all":
        final_group = None
    elif group_id == "null":
        final_group = "NULL_SPECIAL"
    else:
        final_group = group_id

    # 保存并执行查询
    final_type = None if income_type == "all" else income_type

    # 解析日期范围
    dates = date_str.split()
    if len(dates) == 1:
        start_date = end_date = dates[0]
    elif len(dates) == 2:
        start_date = dates[0]
        end_date = dates[1]
    else:
        start_date = end_date = get_daily_period_date()

    # 查询记录
    if final_group == "NULL_SPECIAL":
        all_records = await get_income_records_for_callback(
            start_date, end_date, income_type=final_type
        )
        records = [r for r in all_records if r.get("group_id") is None]
    else:
        records = await get_income_records_for_callback(
            start_date, end_date, income_type=final_type
        )

    type_name = INCOME_TYPES.get(final_type, "全部类型") if final_type else "全部类型"
    if final_group == "NULL_SPECIAL":
        group_name = "全局"
    elif final_group:
        group_name = final_group
    else:
        group_name = "全部"

    title = "收入明细查询"
    if start_date == end_date:
        title += f" ({start_date})"
    else:
        title += f" ({start_date} 至 {end_date})"
    title += f"\n类型: {type_name} | 归属ID: {group_name}"

    report, has_more, total_pages, current_type = await generate_income_report(
        records,
        start_date,
        end_date,
        title,
        page=1,
        items_per_page=0,
        income_type=final_type,
    )

    keyboard = []

    # 如果有分页，添加分页按钮
    if total_pages > 1:
        page_data = (
            f"{final_type or 'all'}|"
            f"{final_group or 'all' if final_group else 'all'}|"
            f"{start_date}|{end_date}"
        )
        keyboard.append(
            [
                InlineKeyboardButton(
                    "下一页 ▶️", callback_data=f"income_adv_page_{page_data}|2"
                )
            ]
        )

    keyboard.append(
        [InlineKeyboardButton("🔙 返回高级查询", callback_data="income_advanced_query")]
    )

    try:
        await safe_edit_message_text(
            query, report, reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"编辑收入明细消息失败: {e}", exc_info=True)
        try:
            if query.message:
                await query.message.reply_text(
                    report, reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await query.answer("❌ 显示失败（消息不存在）", show_alert=True)
        except Exception as e2:
            logger.error(f"发送报表消息失败: {e2}", exc_info=True)
            await query.answer("❌ 显示失败", show_alert=True)


async def handle_income_adv_page(
    query, user_id: int, context: ContextTypes.DEFAULT_TYPE, data: str
):
    """处理高级查询分页回调"""
    from callbacks.income_adv_buttons import build_income_page_buttons
    from callbacks.income_adv_parse import (normalize_income_params,
                                            parse_income_adv_page_params)
    from callbacks.income_adv_query import (build_income_title,
                                            query_income_records)
    from callbacks.income_adv_send import send_income_adv_page

    if not user_id or user_id not in ADMIN_IDS:
        await query.answer("❌ 此功能仅限管理员使用", show_alert=True)
        return

    await query.answer()

    # 解析参数
    success, type_key, group_key, start_date, end_date, page = (
        parse_income_adv_page_params(data)
    )
    if not success:
        await query.answer("❌ 分页参数错误", show_alert=True)
        return

    # 规范化参数
    final_type, final_group = normalize_income_params(type_key, group_key)

    # 查询记录
    records = await query_income_records(start_date, end_date, final_type, final_group)

    # 构建标题
    title = build_income_title(start_date, end_date, final_type, final_group)

    # 生成报表
    report, has_more_pages, total_pages, current_type = await generate_income_report(
        records,
        start_date,
        end_date,
        title,
        page=page,
        items_per_page=0,
        income_type=final_type,
    )

    # 构建按钮
    reply_markup = build_income_page_buttons(
        page, total_pages, final_type, final_group, start_date, end_date
    )

    # 发送消息
    await send_income_adv_page(query, report, reply_markup)


async def handle_income_type(
    query, user_id: int, context: ContextTypes.DEFAULT_TYPE, data: str
):
    """处理按类型查看收入明细回调"""
    if not user_id or user_id not in ADMIN_IDS:
        await query.answer("❌ 此功能仅限管理员使用", show_alert=True)
        return

    await query.answer()
    income_type = data.replace("income_type_", "")
    date = get_daily_period_date()
    records = await get_income_records_for_callback(date, date, income_type=income_type)

    type_mapping = get_income_type_mapping()
    type_name = type_mapping.get(income_type, income_type)
    report, has_more, total_pages, current_type = await generate_income_report(
        records,
        date,
        date,
        f"今日{type_name}收入 ({date})",
        page=1,
        items_per_page=0,
        income_type=income_type,
    )

    keyboard = []

    # 如果有分页，添加分页按钮
    if total_pages > 1:
        page_buttons = []
        if 1 < total_pages:
            page_buttons.append(
                InlineKeyboardButton(
                    "下一页 ▶️",
                    callback_data=f"income_page_{income_type}|2|{date}|{date}",
                )
            )
        if page_buttons:
            keyboard.append(page_buttons)

    keyboard.append(
        [InlineKeyboardButton("🔙 返回", callback_data="income_view_today")]
    )
    try:
        await safe_edit_message_text(
            query, report, reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"编辑收入明细消息失败: {e}", exc_info=True)
        try:
            if query.message:
                await query.message.reply_text(
                    report, reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await query.answer("❌ 显示失败（消息不存在）", show_alert=True)
        except Exception as e2:
            logger.error(f"发送报表消息失败: {e2}", exc_info=True)
            await query.answer("❌ 显示失败", show_alert=True)


async def handle_income_page(
    query, user_id: int, context: ContextTypes.DEFAULT_TYPE, data: str
):
    """处理收入明细分页回调"""
    if not user_id or user_id not in ADMIN_IDS:
        await query.answer("❌ 此功能仅限管理员使用", show_alert=True)
        return

    await query.answer()

    from callbacks.income_page_buttons import build_pagination_buttons
    from callbacks.income_page_parse import parse_pagination_params
    from callbacks.income_page_prepare import prepare_query_params

    # 解析分页参数
    params = parse_pagination_params(data)
    if params is None:
        await query.answer("❌ 分页参数错误", show_alert=True)
        return

    income_type, page, start_date, end_date = params

    # 准备查询参数
    records, type_name, title = await prepare_query_params(
        income_type, start_date, end_date
    )

    # 处理 income_type
    query_type = (
        None
        if (income_type == "None" or income_type == "" or income_type is None)
        else income_type
    )
    callback_type = "None" if query_type is None else income_type

    # 如果 page 为 0，表示显示全部（不分页）
    items_per_page = 0 if page == 0 else 20
    actual_page = 1 if page == 0 else page

    # 生成报告
    report, has_more, total_pages, current_type = await generate_income_report(
        records,
        start_date,
        end_date,
        title,
        page=actual_page,
        items_per_page=items_per_page,
        income_type=query_type,
    )

    # 构建分页按钮
    keyboard = build_pagination_buttons(
        page, total_pages, items_per_page, callback_type, start_date, end_date
    )

    # 发送消息
    try:
        await safe_edit_message_text(
            query, report, reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"编辑收入明细消息失败: {e}", exc_info=True)
