"""收入明细分页 - 参数解析模块

包含解析分页参数的逻辑。
"""

from utils.date_helpers import get_daily_period_date


def parse_pagination_params(data: str) -> tuple[str, int, str, str] | None:
    """解析分页参数

    Args:
        data: 回调数据字符串

    Returns:
        tuple: (income_type, page, start_date, end_date) 或 None（如果解析失败）
    """
    # 解析分页参数: income_page_{type}|{page}|{start_date}|{end_date}
    param_str = data.replace("income_page_", "")

    # 兼容旧格式和新格式
    if "|" in param_str:
        return _parse_new_format(param_str)
    else:
        return _parse_old_format(param_str)


def _parse_new_format(param_str: str) -> tuple[str, int, str, str] | None:
    """解析新格式参数

    Args:
        param_str: 参数字符串

    Returns:
        tuple: (income_type, page, start_date, end_date) 或 None
    """
    parts = param_str.split("|")
    if len(parts) < 2:
        return None

    income_type = parts[0]
    try:
        page = int(parts[1])
    except (ValueError, IndexError):
        return None

    if len(parts) >= 4:
        start_date = parts[2]
        end_date = parts[3]
    else:
        start_date = end_date = get_daily_period_date()

    return income_type, page, start_date, end_date


def _parse_old_format(param_str: str) -> tuple[str, int, str, str] | None:
    """解析旧格式参数

    Args:
        param_str: 参数字符串

    Returns:
        tuple: (income_type, page, start_date, end_date) 或 None
    """
    parts = param_str.split("_")
    if len(parts) < 2:
        return None

    income_type = parts[0]
    try:
        page = int(parts[1])
    except (ValueError, IndexError):
        return None

    if len(parts) >= 8:
        try:
            start_date = f"{parts[2]}-{parts[3].zfill(2)}-{parts[4].zfill(2)}"
            end_date = f"{parts[5]}-{parts[6].zfill(2)}-{parts[7].zfill(2)}"
        except (ValueError, IndexError):
            start_date = end_date = get_daily_period_date()
    elif len(parts) >= 4:
        try:
            start_date = parts[2] if len(parts[2]) == 10 else get_daily_period_date()
            end_date = parts[3] if len(parts[3]) == 10 else start_date
        except IndexError:
            start_date = end_date = get_daily_period_date()
    else:
        start_date = end_date = get_daily_period_date()

    return income_type, page, start_date, end_date
