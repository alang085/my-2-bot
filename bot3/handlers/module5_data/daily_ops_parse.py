"""每日操作记录 - 参数解析模块

包含解析命令参数的逻辑。
"""

from datetime import datetime
from typing import Optional, Tuple

from utils.date_helpers import get_daily_period_date


def parse_date_args(args: list) -> Tuple[Optional[str], bool]:
    """解析日期参数

    Args:
        args: 命令参数列表

    Returns:
        Tuple: (日期字符串, 是否显示全部)
    """
    date = None
    show_all = False

    if args:
        # 检查是否有 "all" 参数
        if "all" in [arg.lower() for arg in args]:
            show_all = True
            # 从参数中提取日期
            date_args = [arg for arg in args if arg.lower() != "all"]
            if date_args:
                date_str = date_args[0]
                try:
                    datetime.strptime(date_str, "%Y-%m-%d")
                    date = date_str
                except ValueError:
                    return None, show_all
            else:
                date = get_daily_period_date()
        else:
            date_str = args[0]
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
                date = date_str
            except ValueError:
                return None, show_all
    else:
        date = get_daily_period_date()

    return date, show_all
