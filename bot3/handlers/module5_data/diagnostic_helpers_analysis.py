"""诊断辅助函数 - 数据分析模块

包含数据分析的逻辑。
"""

from typing import Any, Dict, List, Tuple


def _initialize_income_type_dicts() -> (
    Tuple[Dict[str, float], Dict[str, float], Dict[str, float]]
):
    """初始化收入类型字典

    Returns:
        (所有类型字典, 有效类型字典, 已撤销类型字典)
    """
    base_dict = {
        "interest": 0.0,
        "completed": 0.0,
        "breach_end": 0.0,
        "principal_reduction": 0.0,
        "adjustment": 0.0,
    }
    return base_dict.copy(), base_dict.copy(), base_dict.copy()


def _process_income_records(
    all_records: List[Dict[str, Any]],
    all_by_type: Dict[str, float],
    valid_by_type: Dict[str, float],
    undone_by_type: Dict[str, float],
) -> None:
    """处理收入记录统计

    Args:
        all_records: 所有记录列表
        all_by_type: 所有类型字典
        valid_by_type: 有效类型字典
        undone_by_type: 已撤销类型字典
    """
    for record in all_records:
        record_type = record.get("type", "")
        amount = record.get("amount", 0.0) or 0.0
        is_undone = record.get("is_undone", 0) == 1

        if record_type in all_by_type:
            all_by_type[record_type] += amount
            if not is_undone:
                valid_by_type[record_type] += amount
            else:
                undone_by_type[record_type] += amount


def analyze_income_records(
    all_records: List[Dict[str, Any]],
    valid_records: List[Dict[str, Any]],
    undone_records: List[Dict[str, Any]],
) -> Dict[str, Dict[str, float]]:
    """分析收入记录

    Args:
        all_records: 所有记录（包括已撤销的）
        valid_records: 有效记录（排除已撤销的）
        undone_records: 已撤销的记录

    Returns:
        Dict[str, Dict[str, float]]: 包含 all_by_type, valid_by_type, undone_by_type
    """
    all_by_type, valid_by_type, undone_by_type = _initialize_income_type_dicts()
    _process_income_records(all_records, all_by_type, valid_by_type, undone_by_type)

    return {
        "all_by_type": all_by_type,
        "valid_by_type": valid_by_type,
        "undone_by_type": undone_by_type,
    }


def get_date_range(all_records: List[Dict[str, Any]]) -> tuple[str | None, str | None]:
    """获取数据的时间范围

    Args:
        all_records: 所有记录

    Returns:
        tuple[str | None, str | None]: (min_date, max_date)
    """
    if not all_records:
        return None, None

    dates = [r.get("date", "") for r in all_records if r.get("date")]
    if not dates:
        return None, None

    return min(dates), max(dates)


def calculate_differences(
    financial_data: Dict[str, Any], valid_by_type: Dict[str, float]
) -> Dict[str, float]:
    """计算差异

    Args:
        financial_data: 全局财务数据
        valid_by_type: 有效记录按类型统计

    Returns:
        Dict[str, float]: 包含 interest_diff, completed_diff, breach_end_diff
    """
    interest_diff = financial_data.get("interest", 0.0) - valid_by_type["interest"]
    completed_diff = (
        financial_data.get("completed_amount", 0.0) - valid_by_type["completed"]
    )
    breach_end_diff = (
        financial_data.get("breach_end_amount", 0.0) - valid_by_type["breach_end"]
    )

    return {
        "interest_diff": interest_diff,
        "completed_diff": completed_diff,
        "breach_end_diff": breach_end_diff,
    }


def analyze_possible_reasons(
    interest_diff: float,
    completed_diff: float,
    breach_end_diff: float,
    undone_records: List[Dict[str, Any]],
    all_records: List[Dict[str, Any]],
) -> List[str]:
    """分析可能的原因

    Args:
        interest_diff: 利息收入差异
        completed_diff: 完成订单差异
        breach_end_diff: 违约完成差异
        undone_records: 已撤销的记录
        all_records: 所有记录

    Returns:
        List[str]: 可能的原因列表
    """
    reasons: List[str] = []

    if interest_diff > 1000 or completed_diff > 1000 or breach_end_diff > 1000:
        reasons.append(
            "1. 历史数据导入时，只更新了统计表，没有创建 income_records 记录"
        )

    if len(undone_records) > 0:
        reasons.append(
            f"2. 存在 {len(undone_records)} 条已撤销的记录，但统计数据可能未回滚"
        )

    if all_records:
        dates = [r.get("date", "") for r in all_records if r.get("date")]
        if dates and len(all_records) < 100:  # 假设应该有更多记录
            reasons.append("3. income_records 表可能被清理过，只保留了部分记录")

    if interest_diff > 0 or completed_diff > 0 or breach_end_diff > 0:
        reasons.append(
            "4. financial_data 包含历史累计数据，而 income_records 可能不完整"
        )

    return reasons
