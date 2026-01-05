"""诊断辅助函数 - 数据汇总

包含数据汇总计算的逻辑。
"""

from typing import Any, Dict, List


def calculate_income_summary(income_records: List[Dict[str, Any]]) -> Dict[str, float]:
    """计算收入明细汇总

    Args:
        income_records: 收入记录列表

    Returns:
        Dict[str, float]: 收入汇总字典
    """
    income_summary = {
        "interest": 0.0,
        "completed_amount": 0.0,
        "breach_end_amount": 0.0,
        "principal_reduction": 0.0,
        "adjustment": 0.0,
    }

    for record in income_records:
        record_type = record.get("type", "")
        amount = record.get("amount", 0.0) or 0.0
        if record_type == "interest":
            income_summary["interest"] += amount
        elif record_type == "completed":
            income_summary["completed_amount"] += amount
        elif record_type == "breach_end":
            income_summary["breach_end_amount"] += amount
        elif record_type == "principal_reduction":
            income_summary["principal_reduction"] += amount
        elif record_type == "adjustment":
            income_summary["adjustment"] += amount

    return income_summary
