"""收入高级查询分页 - 按钮模块

包含构建分页按钮的逻辑。
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def build_income_page_buttons(
    page: int,
    total_pages: int,
    final_type: str | None,
    final_group: str | None,
    start_date: str,
    end_date: str,
) -> InlineKeyboardMarkup:
    """构建分页按钮

    Args:
        page: 当前页码
        total_pages: 总页数
        final_type: 类型
        final_group: 归属ID
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        InlineKeyboardMarkup: 按钮标记
    """
    keyboard = []
    page_buttons = []

    if page > 1:
        page_data = (
            f"{final_type or 'all'}|"
            f"{final_group or 'all' if final_group else 'all'}|"
            f"{start_date}|{end_date}"
        )
        page_buttons.append(
            InlineKeyboardButton(
                "◀️ 上一页", callback_data=f"income_adv_page_{page_data}|{page - 1}"
            )
        )

    if page < total_pages:
        page_data = (
            f"{final_type or 'all'}|"
            f"{final_group or 'all' if final_group else 'all'}|"
            f"{start_date}|{end_date}"
        )
        page_buttons.append(
            InlineKeyboardButton(
                "下一页 ▶️", callback_data=f"income_adv_page_{page_data}|{page + 1}"
            )
        )

    if page_buttons:
        keyboard.append(page_buttons)

    keyboard.append(
        [InlineKeyboardButton("🔙 返回高级查询", callback_data="income_advanced_query")]
    )

    return InlineKeyboardMarkup(keyboard)
