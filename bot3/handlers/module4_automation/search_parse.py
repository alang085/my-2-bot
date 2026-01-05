"""报表搜索 - 解析模块

包含解析搜索条件的逻辑。
"""

from typing import Dict


def _parse_weekday_group(part: str, criteria: Dict) -> bool:
    """解析星期分组

    Args:
        part: 输入部分
        criteria: 搜索条件字典

    Returns:
        是否匹配成功
    """
    if part in ["一", "二", "三", "四", "五", "六", "日"]:
        criteria["weekday_group"] = part
        return True
    elif (
        part.startswith("周")
        and len(part) == 2
        and part[1] in ["一", "二", "三", "四", "五", "六", "日"]
    ):
        criteria["weekday_group"] = part[1]
        return True
    return False


def _parse_order_state(part: str, criteria: Dict) -> bool:
    """解析订单状态

    Args:
        part: 输入部分
        criteria: 搜索条件字典

    Returns:
        是否匹配成功
    """
    valid_states = [
        "正常",
        "逾期",
        "违约",
        "完成",
        "违约完成",
        "normal",
        "overdue",
        "breach",
        "end",
        "breach_end",
    ]
    if part in valid_states:
        state_map = {
            "正常": "normal",
            "逾期": "overdue",
            "违约": "breach",
            "完成": "end",
            "违约完成": "breach_end",
        }
        criteria["state"] = state_map.get(part, part)
        return True
    return False


def _parse_group_id_or_customer(part: str, criteria: Dict) -> bool:
    """解析归属ID或客户类型

    Args:
        part: 输入部分
        criteria: 搜索条件字典

    Returns:
        是否匹配成功
    """
    if len(part) == 3 and part[0].isalpha() and part[1:].isdigit():
        criteria["group_id"] = part.upper()
        return True
    elif part.upper() in ["A", "B"]:
        criteria["customer"] = part.upper()
        return True
    return False


def parse_search_criteria(text: str) -> Dict:
    """解析搜索条件

    Args:
        text: 输入文本

    Returns:
        Dict: 搜索条件字典
    """
    criteria = {}
    parts = text.strip().split()

    for part in parts:
        part = part.strip()
        if _parse_weekday_group(part, criteria):
            continue
        if _parse_order_state(part, criteria):
            continue
        _parse_group_id_or_customer(part, criteria)

    return criteria
