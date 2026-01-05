"""诊断辅助函数 - 日期参数处理

包含日期参数解析和验证的逻辑。
"""

from typing import List, Tuple


def parse_date_range(args: List[str]) -> Tuple[str, str]:
    """解析日期范围参数

    Args:
        args: 命令行参数列表

    Returns:
        Tuple[str, str]: (start_date, end_date)
    """
    if args and len(args) > 0:
        if len(args) == 1:
            # 单个日期
            return args[0], args[0]
        elif len(args) >= 2:
            # 日期范围
            return args[0], args[1]

    # 默认检查所有历史数据
    return "1970-01-01", "2099-12-31"
