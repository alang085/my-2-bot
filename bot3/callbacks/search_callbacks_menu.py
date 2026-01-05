"""搜索回调菜单处理模块

包含搜索菜单相关的回调处理逻辑。
"""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from handlers.data_access import get_all_group_ids_for_callback

logger = logging.getLogger(__name__)


async def handle_search_start(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """显示搜索主菜单"""
    keyboard = [
        [
            InlineKeyboardButton("按状态", callback_data="search_menu_state"),
            InlineKeyboardButton("按归属ID", callback_data="search_menu_attribution"),
            InlineKeyboardButton("按星期分组", callback_data="search_menu_group"),
        ],
        [InlineKeyboardButton("按总有效金额", callback_data="search_menu_amount")],
    ]
    await query.edit_message_text(
        "🔍 查找方式:", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_search_menu_state(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """显示状态选择菜单"""
    keyboard = [
        [InlineKeyboardButton("正常", callback_data="search_do_state_normal")],
        [InlineKeyboardButton("逾期", callback_data="search_do_state_overdue")],
        [InlineKeyboardButton("违约", callback_data="search_do_state_breach")],
        [InlineKeyboardButton("完成", callback_data="search_do_state_end")],
        [InlineKeyboardButton("违约完成", callback_data="search_do_state_breach_end")],
        [InlineKeyboardButton("🔙 返回", callback_data="search_start")],
    ]
    await query.edit_message_text(
        "请选择状态:", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_search_menu_attribution(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """显示归属ID选择菜单"""
    group_ids = await get_all_group_ids_for_callback()
    if not group_ids:
        await query.edit_message_text(
            "⚠️ 无归属数据",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 返回", callback_data="search_start")]]
            ),
        )
        return

    keyboard = []
    row = []
    for gid in sorted(group_ids)[:40]:
        row.append(
            InlineKeyboardButton(gid, callback_data=f"search_do_attribution_{gid}")
        )
        if len(row) == 4:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔙 返回", callback_data="search_start")])
    await query.edit_message_text(
        "请选择归属ID:", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_search_menu_group(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """显示星期分组选择菜单"""
    keyboard = [
        [
            InlineKeyboardButton("周一", callback_data="search_do_group_一"),
            InlineKeyboardButton("周二", callback_data="search_do_group_二"),
            InlineKeyboardButton("周三", callback_data="search_do_group_三"),
        ],
        [
            InlineKeyboardButton("周四", callback_data="search_do_group_四"),
            InlineKeyboardButton("周五", callback_data="search_do_group_五"),
            InlineKeyboardButton("周六", callback_data="search_do_group_六"),
        ],
        [InlineKeyboardButton("周日", callback_data="search_do_group_日")],
        [InlineKeyboardButton("🔙 返回", callback_data="search_start")],
    ]
    await query.edit_message_text(
        "请选择星期分组:", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_search_menu_amount(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """显示金额搜索输入提示"""
    try:
        if query.message:
            await query.message.reply_text(
                "💰 按总有效金额查找\n\n"
                "请输入目标金额（支持'万'单位）：\n"
                "例如：\n"
                "• 20万（从周一到周日均匀选取总金额20万的订单）\n"
                "• 200000（直接输入数字）\n\n"
                "系统将从周一到周日的有效订单中，均匀地选择订单，使得总金额接近目标金额。\n\n"
                "请输入:（输入 'cancel' 取消）"
            )
        else:
            await query.answer("请输入目标金额（支持'万'单位）", show_alert=True)
    except Exception as e:
        logger.error(f"发送金额查找提示失败: {e}", exc_info=True)
        await query.answer("请输入目标金额", show_alert=True)
    context.user_data["state"] = "SEARCHING_AMOUNT"
    await query.answer()


async def handle_search_lock_start(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query
) -> None:
    """显示锁定搜索输入提示"""
    try:
        if query.message:
            await query.message.reply_text(
                "🔍 请输入查询条件（支持综合查询）：\n\n"
                "单一查询：\n"
                "• S01（按归属查询）\n"
                "• 三（按星期分组查询）\n"
                "• 正常（按状态查询）\n\n"
                "综合查询：\n"
                "• 三 正常（周三的正常订单）\n"
                "• S01 正常（S01的正常订单）\n\n"
                "请输入:",
                parse_mode="Markdown",
            )
        else:
            await query.answer("请输入查询条件", show_alert=True)
    except Exception as e:
        logger.error(f"发送查询条件提示失败: {e}", exc_info=True)
        await query.answer("请输入查询条件", show_alert=True)
    context.user_data["state"] = "SEARCHING"
    await query.answer()
