"""操作详情格式化 - 时间模块

包含格式化时间字符串的逻辑。
"""


def format_time_string(created_at: str) -> str:
    """格式化时间字符串

    Args:
        created_at: 创建时间字符串

    Returns:
        str: 格式化后的时间字符串
    """
    time_str = "无时间"
    if created_at:
        # 数据库存储的格式是 'YYYY-MM-DD HH:MM:SS'（已经是北京时间）
        # 直接使用，不进行时区转换
        if len(created_at) >= 19:
            time_str = created_at[:19]  # 取前19个字符（YYYY-MM-DD HH:MM:SS）
        elif " " in created_at:
            # 如果格式不完整，尝试提取日期和时间部分
            parts = created_at.split(" ")
            if len(parts) >= 2:
                time_str = (
                    f"{parts[0]} {parts[1][:8]}" if len(parts[1]) >= 8 else created_at
                )
            else:
                time_str = created_at
        else:
            time_str = created_at

    return time_str
