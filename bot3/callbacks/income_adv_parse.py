"""收入高级查询分页 - 参数解析模块

包含解析分页参数的逻辑。
"""

from telegram import CallbackQuery


async def parse_income_adv_page_params(
    data: str,
) -> tuple[bool, str, str, str, str, int]:
    """解析分页参数

    Args:
        data: 回调数据

    Returns:
        Tuple: (是否成功, type_key, group_key, start_date, end_date, page)
    """
    param_str = data.replace("income_adv_page_", "")
    if "|" in param_str:
        parts = param_str.split("|")
        if len(parts) >= 5:
            type_key = parts[0]
            group_key = parts[1]
            start_date = parts[2]
            end_date = parts[3]
            page = int(parts[4])
            return True, type_key, group_key, start_date, end_date, page
        else:
            return False, "", "", "", "", 0
    else:
        # 兼容旧格式
        parts = param_str.split("_")
        if len(parts) >= 6:
            page = int(parts[-1])
            end_date = parts[-2]
            start_date = parts[-3]
            group_key = parts[-4]
            type_key = parts[-5]
            return True, type_key, group_key, start_date, end_date, page
        else:
            return False, "", "", "", "", 0


def normalize_income_params(
    type_key: str, group_key: str
) -> tuple[str | None, str | None]:
    """规范化参数

    Args:
        type_key: 类型键
        group_key: 归属键

    Returns:
        Tuple: (final_type, final_group)
    """
    final_type = None if type_key == "all" else type_key

    # 处理 group_id
    if group_key == "all":
        final_group = None
    elif group_key == "NULL":
        final_group = "NULL_SPECIAL"
    else:
        final_group = group_key

    return final_type, final_group
