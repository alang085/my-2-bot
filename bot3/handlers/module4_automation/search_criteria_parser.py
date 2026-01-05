"""搜索条件解析策略

使用策略模式解析不同类型的搜索条件，简化复杂的if-elif链。
"""

from typing import Callable, Dict, Optional

from telegram.ext import ContextTypes

# 搜索类型解析策略映射
SEARCH_CRITERIA_PARSERS: Dict[
    str, Callable[[ContextTypes.DEFAULT_TYPE], Optional[Dict]]
] = {}


def _parse_order_id_criteria(context: ContextTypes.DEFAULT_TYPE) -> Optional[Dict]:
    """解析订单ID搜索条件"""
    if len(context.args) < 2:
        return None
    return {"order_id": context.args[1]}


def _parse_group_id_criteria(context: ContextTypes.DEFAULT_TYPE) -> Optional[Dict]:
    """解析归属ID搜索条件"""
    if len(context.args) < 2:
        return None
    return {"group_id": context.args[1]}


def _parse_customer_criteria(context: ContextTypes.DEFAULT_TYPE) -> Optional[Dict]:
    """解析客户类型搜索条件"""
    if len(context.args) < 2:
        return None
    return {"customer": context.args[1].upper()}


def _parse_state_criteria(context: ContextTypes.DEFAULT_TYPE) -> Optional[Dict]:
    """解析订单状态搜索条件"""
    if len(context.args) < 2:
        return None
    return {"state": context.args[1]}


def _parse_date_criteria(context: ContextTypes.DEFAULT_TYPE) -> Optional[Dict]:
    """解析日期范围搜索条件"""
    if len(context.args) < 3:
        return None
    return {"date_range": (context.args[1], context.args[2])}


def _parse_weekday_group_criteria(context: ContextTypes.DEFAULT_TYPE) -> Optional[Dict]:
    """解析星期分组搜索条件"""
    if len(context.args) < 2:
        return None
    val = context.args[1]
    if val.startswith("周") and len(val) == 2:
        val = val[1]
    return {"weekday_group": val}


# 注册解析策略
SEARCH_CRITERIA_PARSERS = {
    "order_id": _parse_order_id_criteria,
    "group_id": _parse_group_id_criteria,
    "customer": _parse_customer_criteria,
    "state": _parse_state_criteria,
    "date": _parse_date_criteria,
    "group": _parse_weekday_group_criteria,
}


def parse_search_criteria(context: ContextTypes.DEFAULT_TYPE) -> Optional[Dict]:
    """解析搜索条件（使用策略模式）

    Args:
        context: 上下文对象

    Returns:
        搜索条件字典，如果解析失败则返回None
    """
    if not context.args:
        return None

    search_type = context.args[0].lower()
    parser = SEARCH_CRITERIA_PARSERS.get(search_type)

    if parser:
        return parser(context)
    return None
