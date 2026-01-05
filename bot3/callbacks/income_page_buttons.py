"""收入明细分页 - 按钮构建模块

包含构建分页按钮的逻辑。
"""

from telegram import InlineKeyboardButton


def build_pagination_buttons(
    page: int,
    total_pages: int,
    items_per_page: int,
    callback_type: str,
    start_date: str,
    end_date: str,
) -> list:
    """构建分页按钮

    Args:
        page: 当前页码
        total_pages: 总页数
        items_per_page: 每页项目数
        callback_type: 回调类型
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        list: 按钮列表
    """
    keyboard = []
    page_buttons = []

    callback_type_for_buttons = callback_type if callback_type != "" else "None"

    # 如果当前是分页模式，显示分页按钮和"显示全部"按钮
    if items_per_page > 0 and total_pages > 1:
        if page > 1:
            page_buttons.append(
                InlineKeyboardButton(
                    "◀️ 上一页",
                    callback_data=(
                        f"income_page_{callback_type_for_buttons}|"
                        f"{page - 1}|{start_date}|{end_date}"
                    ),
                )
            )

        if page < total_pages:
            page_buttons.append(
                InlineKeyboardButton(
                    "下一页 ▶️",
                    callback_data=(
                        f"income_page_{callback_type_for_buttons}|"
                        f"{page + 1}|{start_date}|{end_date}"
                    ),
                )
            )

        if page_buttons:
            keyboard.append(page_buttons)

        # 添加"显示全部"按钮
        keyboard.append(
            [
                InlineKeyboardButton(
                    "📋 显示全部",
                    callback_data=(
                        f"income_page_{callback_type_for_buttons}|"
                        f"0|{start_date}|{end_date}"
                    ),
                )
            ]
        )
    # 如果当前是显示全部模式，显示"分页显示"按钮
    elif items_per_page == 0:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "📄 分页显示",
                    callback_data=(
                        f"income_page_{callback_type_for_buttons}|"
                        f"1|{start_date}|{end_date}"
                    ),
                )
            ]
        )

    # 添加返回按钮
    keyboard.append(
        [InlineKeyboardButton("🔙 返回", callback_data="income_view_today")]
    )

    return keyboard
