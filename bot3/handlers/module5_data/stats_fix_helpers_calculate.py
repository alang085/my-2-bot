"""统计修复辅助函数 - 计算模块

包含收入汇总计算的逻辑。
"""

from typing import Any, Dict, List


def calculate_income_summary_from_records(
    income_records: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """从收入记录计算收入汇总

    Args:
        income_records: 收入记录列表

    Returns:
        Dict: 包含 income_summary, daily_income, global_income
    """
    # 计算收入明细汇总
    income_summary: Dict[str, Any] = {
        "interest": 0.0,
        "completed_amount": 0.0,
        "breach_end_amount": 0.0,
        "completed_count": 0,
        "breach_end_count": 0,
    }

    # 按日期和归属ID分组统计
    daily_income: Dict[str, Dict[str, Dict[str, Any]]] = (
        {}
    )  # {date: {group_id: {type: amount}}}
    global_income: Dict[str, Any] = {}  # {type: amount}

    for record in income_records:
        record_type = record.get("type", "")
        amount = record.get("amount", 0.0) or 0.0
        date = record.get("date", "")
        group_id = record.get("group_id")

        if record_type == "interest":
            from handlers.module5_data.interest_record_data import \
                InterestRecordParams

            interest_params = InterestRecordParams(
                record=record,
                amount=amount,
                date=date,
                group_id=group_id,
                income_summary=income_summary,
                daily_income=daily_income,
                global_income=global_income,
            )
            _process_interest_record(interest_params)
        elif record_type == "completed":
            _process_completed_record(
                record,
                amount,
                date,
                group_id,
                income_summary,
                daily_income,
                global_income,
            )
        elif record_type == "breach_end":
            _process_breach_end_record(
                record,
                amount,
                date,
                group_id,
                income_summary,
                daily_income,
                global_income,
            )

    return {
        "income_summary": income_summary,
        "daily_income": daily_income,
        "global_income": global_income,
    }


def _process_interest_record(params: "InterestRecordParams") -> None:
    """处理利息收入记录

    Args:
        params: 利息记录参数
    """
    from handlers.module5_data.interest_record_data import InterestRecordParams

    params.income_summary["interest"] += params.amount
    params.global_income["interest"] = (
        params.global_income.get("interest", 0.0) + params.amount
    )
    if params.date not in params.daily_income:
        params.daily_income[params.date] = {}
    if params.group_id not in params.daily_income[params.date]:
        params.daily_income[params.date][params.group_id] = {}
    params.daily_income[params.date][params.group_id]["interest"] = (
        params.daily_income[params.date][params.group_id].get("interest", 0.0)
        + params.amount
    )


def _process_completed_record(
    record: Dict[str, Any],
    amount: float,
    date: str,
    group_id: str,
    income_summary: Dict[str, Any],
    daily_income: Dict[str, Dict[str, Dict[str, Any]]],
    global_income: Dict[str, Any],
) -> None:
    """处理完成订单记录"""
    income_summary["completed_amount"] += amount
    income_summary["completed_count"] += 1
    global_income["completed_amount"] = (
        global_income.get("completed_amount", 0.0) + amount
    )
    global_income["completed_count"] = global_income.get("completed_count", 0) + 1
    if date not in daily_income:
        daily_income[date] = {}
    if group_id not in daily_income[date]:
        daily_income[date][group_id] = {}
    daily_income[date][group_id]["completed_amount"] = (
        daily_income[date][group_id].get("completed_amount", 0.0) + amount
    )
    daily_income[date][group_id]["completed_count"] = (
        daily_income[date][group_id].get("completed_count", 0) + 1
    )


def _process_breach_end_record(
    record: Dict[str, Any],
    amount: float,
    date: str,
    group_id: str,
    income_summary: Dict[str, Any],
    daily_income: Dict[str, Dict[str, Dict[str, Any]]],
    global_income: Dict[str, Any],
) -> None:
    """处理违约完成记录"""
    income_summary["breach_end_amount"] += amount
    income_summary["breach_end_count"] += 1
    global_income["breach_end_amount"] = (
        global_income.get("breach_end_amount", 0.0) + amount
    )
    global_income["breach_end_count"] = global_income.get("breach_end_count", 0) + 1
    if date not in daily_income:
        daily_income[date] = {}
    if group_id not in daily_income[date]:
        daily_income[date][group_id] = {}
    daily_income[date][group_id]["breach_end_amount"] = (
        daily_income[date][group_id].get("breach_end_amount", 0.0) + amount
    )
    daily_income[date][group_id]["breach_end_count"] = (
        daily_income[date][group_id].get("breach_end_count", 0) + 1
    )
