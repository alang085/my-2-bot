"""诊断辅助函数 - 一致性检查

包含数据一致性检查的逻辑。
"""

from typing import Dict, List

from utils.handler_helpers import check_data_consistency


def _check_stats_consistency(
    stats: Dict,
    income_summary: Dict[str, float],
    mismatches: List[str],
    output_lines: List[str],
) -> None:
    """检查统计表与收入明细的一致性

    Args:
        stats: 统计数据
        income_summary: 收入汇总
        mismatches: 不匹配项列表（会被修改）
        output_lines: 输出行列表（会被修改）
    """
    from utils.data_consistency_data import DataConsistencyParams

    check_data_consistency(
        DataConsistencyParams(
            field_name="利息收入",
            stats_value=stats.get("interest", 0.0),
            income_value=income_summary["interest"],
            mismatches=mismatches,
            output_lines=output_lines,
            stats_label="统计表(daily_data)",
            income_label="明细表(income_records)",
        )
    )

    check_data_consistency(
        DataConsistencyParams(
            field_name="完成订单金额",
            stats_value=stats.get("completed_amount", 0.0),
            income_value=income_summary["completed_amount"],
            mismatches=mismatches,
            output_lines=output_lines,
            stats_label="统计表(daily_data)",
            income_label="明细表(income_records)",
        )
    )

    check_data_consistency(
        DataConsistencyParams(
            field_name="违约完成金额",
            stats_value=stats.get("breach_end_amount", 0.0),
            income_value=income_summary["breach_end_amount"],
            mismatches=mismatches,
            output_lines=output_lines,
            stats_label="统计表(daily_data)",
            income_label="明细表(income_records)",
        )
    )


def _check_global_consistency(
    financial_data: Dict,
    income_summary: Dict[str, float],
    mismatches: List[str],
    output_lines: List[str],
) -> None:
    """检查全局统计数据与收入明细的一致性

    Args:
        financial_data: 全局财务数据
        income_summary: 收入汇总
        mismatches: 不匹配项列表（会被修改）
        output_lines: 输出行列表（会被修改）
    """
    from utils.data_consistency_data import DataConsistencyParams

    check_data_consistency(
        DataConsistencyParams(
            field_name="全局利息收入",
            stats_value=financial_data.get("interest", 0.0),
            income_value=income_summary["interest"],
            mismatches=mismatches,
            output_lines=output_lines,
            stats_label="全局统计(financial_data)",
            income_label="明细表(income_records)",
        )
    )

    check_data_consistency(
        DataConsistencyParams(
            field_name="全局完成订单金额",
            stats_value=financial_data.get("completed_amount", 0.0),
            income_value=income_summary["completed_amount"],
            mismatches=mismatches,
            output_lines=output_lines,
            stats_label="全局统计(financial_data)",
            income_label="明细表(income_records)",
        )
    )

    check_data_consistency(
        DataConsistencyParams(
            field_name="全局违约完成金额",
            stats_value=financial_data.get("breach_end_amount", 0.0),
            income_value=income_summary["breach_end_amount"],
            mismatches=mismatches,
            output_lines=output_lines,
            stats_label="全局统计(financial_data)",
            income_label="明细表(income_records)",
        )
    )


def check_all_consistencies(
    stats: Dict,
    financial_data: Dict,
    income_summary: Dict[str, float],
    output_lines: List[str],
) -> List[str]:
    """检查所有数据一致性

    Args:
        stats: 统计数据
        financial_data: 全局财务数据
        income_summary: 收入汇总
        output_lines: 输出行列表

    Returns:
        List[str]: 不匹配项列表
    """
    mismatches = []
    _check_stats_consistency(stats, income_summary, mismatches, output_lines)
    _check_global_consistency(financial_data, income_summary, mismatches, output_lines)
    return mismatches
