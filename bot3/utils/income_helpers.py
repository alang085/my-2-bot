"""收入类型处理工具模块

统一处理收入类型相关的逻辑，包括：
- 收入类型分组
- 收入类型统计
- 收入类型映射
"""

from typing import Any, Dict, List, Optional

from constants import INCOME_TYPES


def get_income_type_name(income_type: str) -> str:
    """
    获取收入类型的中文名称

    Args:
        income_type: 收入类型代码（如 "completed", "breach_end"）

    Returns:
        收入类型的中文名称，如果不存在则返回原值
    """
    return INCOME_TYPES.get(income_type, income_type)


def get_income_type_order() -> List[str]:
    """
    获取收入类型的显示顺序

    Returns:
        收入类型代码列表，按显示顺序排列
    """
    return ["completed", "breach_end", "principal_reduction", "interest", "adjustment"]


def categorize_income_by_type(income_records: List[Dict]) -> Dict[str, float]:
    """
    统一处理收入类型分类，按类型汇总金额

    Args:
        income_records: 收入记录列表，每个记录包含 "type" 和 "amount" 字段

    Returns:
        按类型汇总的金额字典，包含：
        - "interest": 利息收入总额
        - "completed": 订单完成总额
        - "breach_end": 违约完成总额
        - "principal_reduction": 本金减少总额
        - "adjustment": 资金调整总额
        - "total": 总收入总额
    """
    result = {
        "interest": 0.0,
        "completed": 0.0,
        "breach_end": 0.0,
        "principal_reduction": 0.0,
        "adjustment": 0.0,
        "total": 0.0,
    }

    for record in income_records:
        income_type = record.get("type", "")
        amount = record.get("amount", 0.0) or 0.0

        if income_type in result:
            result[income_type] += amount
        result["total"] += amount

    return result


def group_income_records_by_type(income_records: List[Dict]) -> Dict[str, List[Dict]]:
    """
    按收入类型分组收入记录

    Args:
        income_records: 收入记录列表

    Returns:
        按类型分组的字典，键为收入类型代码，值为该类型的记录列表
    """
    by_type: Dict[str, List[Dict]] = {}
    for record in income_records:
        type_name = record.get("type", "")
        if type_name not in by_type:
            by_type[type_name] = []
        by_type[type_name].append(record)
    return by_type


def calculate_income_statistics(income_records: List[Dict]) -> Dict[str, Any]:
    """
    计算收入统计信息（用于db_operations中的统计逻辑）

    Args:
        income_records: 收入记录列表，每个记录包含 "type", "amount", "count" 字段

    Returns:
        统计信息字典，包含：
        - "total_interest": 利息收入总额
        - "interest_count": 利息收入笔数
        - "total_completed": 订单完成总额
        - "total_breach_end": 违约完成总额
        - "total_principal_reduction": 本金减少总额
        - "total_amount": 总收入总额
    """
    result = {
        "total_interest": 0.0,
        "interest_count": 0,
        "total_completed": 0.0,
        "total_breach_end": 0.0,
        "total_principal_reduction": 0.0,
        "total_amount": 0.0,
    }

    for record in income_records:
        income_type = record.get("type", "")
        amount = record.get("amount", 0.0) or 0.0
        count = record.get("count", 0) or 0

        if income_type == "interest":
            result["total_interest"] = amount
            result["interest_count"] = count
        elif income_type == "completed":
            result["total_completed"] = amount
        elif income_type == "breach_end":
            result["total_breach_end"] = amount
        elif income_type == "principal_reduction":
            result["total_principal_reduction"] = amount

        result["total_amount"] += amount

    return result


def get_income_type_mapping() -> Dict[str, str]:
    """
    获取收入类型映射字典（用于callbacks中的类型名称映射）

    Returns:
        收入类型代码到中文名称的映射字典
    """
    return {
        "completed": "订单完成",
        "breach_end": "违约完成",
        "interest": "利息收入",
        "principal_reduction": "本金减少",
        "adjustment": "资金调整",
    }
