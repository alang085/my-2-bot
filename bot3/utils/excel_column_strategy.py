"""Excel列解析策略

使用查找表简化列索引解析逻辑。
"""

# 列名到索引的映射表
COLUMN_NAME_MAP = {
    "order_id": 0,
    "date": 1,
    "customer": 2,
    "amount": 3,
    "state": 4,
    "group_id": 5,
    "weekday_group": 6,
}


def parse_column_index(column_name: str) -> int:
    """解析列名到索引（使用查找表）

    Args:
        column_name: 列名

    Returns:
        列索引，如果未找到则返回-1
    """
    return COLUMN_NAME_MAP.get(column_name.lower(), -1)


def get_all_column_names() -> list[str]:
    """获取所有支持的列名

    Returns:
        列名列表
    """
    return list(COLUMN_NAME_MAP.keys())
