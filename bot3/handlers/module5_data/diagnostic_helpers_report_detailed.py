"""诊断辅助函数 - 详细报告生成模块

包含详细诊断报告生成的逻辑。
"""

from typing import Any, Dict, List


def generate_income_records_analysis_section(
    all_records: List[Dict[str, Any]],
    valid_records: List[Dict[str, Any]],
    undone_records: List[Dict[str, Any]],
    all_by_type: Dict[str, float],
    valid_by_type: Dict[str, float],
    undone_by_type: Dict[str, float],
) -> List[str]:
    """生成收入记录分析部分

    Args:
        all_records: 所有记录
        valid_records: 有效记录
        undone_records: 已撤销的记录
        all_by_type: 所有记录按类型统计
        valid_by_type: 有效记录按类型统计
        undone_by_type: 已撤销记录按类型统计

    Returns:
        List[str]: 报告行列表
    """
    output_lines: List[str] = []
    output_lines.append("📋 【income_records 表分析】")
    output_lines.append("")
    output_lines.append(f"总记录数: {len(all_records)}")
    output_lines.append(f"有效记录数: {len(valid_records)}")
    output_lines.append(f"已撤销记录数: {len(undone_records)}")
    output_lines.append("")

    output_lines.append("📊 按类型统计（所有记录，包括已撤销）:")
    output_lines.append(f"  利息收入: {all_by_type['interest']:.2f}")
    output_lines.append(f"  完成订单: {all_by_type['completed']:.2f}")
    output_lines.append(f"  违约完成: {all_by_type['breach_end']:.2f}")
    output_lines.append("")

    output_lines.append("✅ 按类型统计（仅有效记录，排除已撤销）:")
    output_lines.append(f"  利息收入: {valid_by_type['interest']:.2f}")
    output_lines.append(f"  完成订单: {valid_by_type['completed']:.2f}")
    output_lines.append(f"  违约完成: {valid_by_type['breach_end']:.2f}")
    output_lines.append("")

    if len(undone_records) > 0:
        output_lines.append("❌ 已撤销记录统计:")
        output_lines.append(f"  利息收入: {undone_by_type['interest']:.2f}")
        output_lines.append(f"  完成订单: {undone_by_type['completed']:.2f}")
        output_lines.append(f"  违约完成: {undone_by_type['breach_end']:.2f}")
        output_lines.append("")

    return output_lines


def generate_date_range_section(
    min_date: str | None, max_date: str | None
) -> List[str]:
    """生成日期范围部分

    Args:
        min_date: 最早日期
        max_date: 最新日期

    Returns:
        List[str]: 报告行列表
    """
    output_lines: List[str] = []
    if min_date and max_date:
        output_lines.append("📅 数据时间范围:")
        output_lines.append(f"  最早记录: {min_date}")
        output_lines.append(f"  最新记录: {max_date}")
        output_lines.append("")
    return output_lines


def generate_statistics_comparison_section(
    financial_data: Dict[str, Any],
    valid_by_type: Dict[str, float],
    interest_diff: float,
    completed_diff: float,
    breach_end_diff: float,
) -> List[str]:
    """生成统计数据对比部分

    Args:
        financial_data: 全局财务数据
        valid_by_type: 有效记录按类型统计
        interest_diff: 利息收入差异
        completed_diff: 完成订单差异
        breach_end_diff: 违约完成差异

    Returns:
        List[str]: 报告行列表
    """
    output_lines: List[str] = []
    output_lines.append("💰 【统计数据对比】")
    output_lines.append("")

    # 对比 financial_data
    output_lines.append("🌐 全局统计数据 (financial_data):")
    output_lines.append(f"  利息收入: {financial_data.get('interest', 0.0):.2f}")
    output_lines.append(
        f"  完成订单: {financial_data.get('completed_amount', 0.0):.2f}"
    )
    output_lines.append(
        f"  违约完成: {financial_data.get('breach_end_amount', 0.0):.2f}"
    )
    output_lines.append("")

    output_lines.append("📈 收入明细汇总 (income_records - 仅有效记录):")
    output_lines.append(f"  利息收入: {valid_by_type['interest']:.2f}")
    output_lines.append(f"  完成订单: {valid_by_type['completed']:.2f}")
    output_lines.append(f"  违约完成: {valid_by_type['breach_end']:.2f}")
    output_lines.append("")

    output_lines.append("🔍 差异分析:")
    output_lines.append(f"  利息收入差异: {interest_diff:+,.2f}")
    output_lines.append(f"  完成订单差异: {completed_diff:+,.2f}")
    output_lines.append(f"  违约完成差异: {breach_end_diff:+,.2f}")
    output_lines.append("")

    return output_lines


def generate_reasons_section(reasons: List[str]) -> List[str]:
    """生成原因分析部分

    Args:
        reasons: 可能的原因列表

    Returns:
        List[str]: 报告行列表
    """
    output_lines: List[str] = []
    output_lines.append("💡 【可能的原因分析】")
    output_lines.append("")

    if reasons:
        for reason in reasons:
            output_lines.append(f"  {reason}")
    else:
        output_lines.append("  未发现明显原因，建议检查数据导入历史")

    output_lines.append("")
    return output_lines


def generate_fix_suggestions_section() -> List[str]:
    """生成修复建议部分

    Returns:
        List[str]: 报告行列表
    """
    output_lines: List[str] = []
    output_lines.append("🔧 【修复建议】")
    output_lines.append("")
    output_lines.append("1. 如果差异是历史数据导致的（正常情况）:")
    output_lines.append("   - 使用 /fix_income_statistics 命令修复统计数据")
    output_lines.append("   - 该命令会根据 income_records 重新计算统计")
    output_lines.append("")
    output_lines.append("2. 如果 income_records 数据不完整:")
    output_lines.append("   - 检查是否有历史数据备份")
    output_lines.append("   - 考虑从统计表反向生成 income_records（需谨慎）")
    output_lines.append("")
    output_lines.append("3. 如果存在已撤销记录但统计未回滚:")
    output_lines.append("   - 检查撤销操作的日志")
    output_lines.append("   - 手动修复统计数据")
    output_lines.append("")

    return output_lines
