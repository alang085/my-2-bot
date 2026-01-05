"""诊断辅助函数 - 报告生成

包含报告生成和格式化的逻辑。
"""

from typing import Any, Dict, List


def generate_report_header(
    start_date: str,
    end_date: str,
    income_summary: Dict[str, float],
    stats: Dict[str, Any],
    financial_data: Dict[str, Any],
) -> List[str]:
    """生成报告头部

    Args:
        start_date: 开始日期
        end_date: 结束日期
        income_summary: 收入汇总
        stats: 统计数据
        financial_data: 全局财务数据

    Returns:
        List[str]: 报告行列表
    """
    output_lines = []
    output_lines.append(f"📊 数据一致性检查报告")
    if start_date == end_date:
        output_lines.append(f"📅 检查日期: {start_date}")
    else:
        output_lines.append(f"📅 检查日期范围: {start_date} 至 {end_date}")
    output_lines.append("=" * 50)
    output_lines.append("")

    output_lines.append("📈 收入明细汇总（从income_records表）:")
    output_lines.append(f"  利息收入: {income_summary['interest']:.2f}")
    output_lines.append(f"  完成订单金额: {income_summary['completed_amount']:.2f}")
    output_lines.append(f"  违约完成金额: {income_summary['breach_end_amount']:.2f}")
    output_lines.append(f"  本金减少: {income_summary['principal_reduction']:.2f}")
    output_lines.append("")

    output_lines.append("📊 统计数据汇总（从daily_data表）:")
    output_lines.append(f"  利息收入: {stats.get('interest', 0.0):.2f}")
    output_lines.append(f"  完成订单金额: {stats.get('completed_amount', 0.0):.2f}")
    output_lines.append(f"  违约完成金额: {stats.get('breach_end_amount', 0.0):.2f}")
    output_lines.append("")

    output_lines.append("💰 全局统计数据（从financial_data表）:")
    output_lines.append(f"  利息收入: {financial_data.get('interest', 0.0):.2f}")
    output_lines.append(
        f"  完成订单金额: {financial_data.get('completed_amount', 0.0):.2f}"
    )
    output_lines.append(
        f"  违约完成金额: {financial_data.get('breach_end_amount', 0.0):.2f}"
    )
    output_lines.append("")
    output_lines.append("=" * 50)
    output_lines.append("")

    return output_lines


def generate_report_footer(mismatches: List[str]) -> List[str]:
    """生成报告尾部

    Args:
        mismatches: 不匹配项列表

    Returns:
        List[str]: 报告行列表
    """
    output_lines = []

    if not mismatches:
        output_lines.append("✅ 数据一致！所有统计数据与收入明细匹配。")
    else:
        output_lines.append("")
        output_lines.append(f"❌ 发现 {len(mismatches)} 项不一致:")
        for item in mismatches:
            output_lines.append(f"  - {item}")
        output_lines.append("")
        output_lines.append("💡 修复建议:")
        output_lines.append("  1. 检查收入明细是否正确记录")
        output_lines.append("  2. 使用 /fix_statistics 修复统计数据")
        output_lines.append("  3. 如果问题持续，请检查日志文件")

    output_lines.append("")
    output_lines.append("💡 提示：要查看统计收入的来源明细，请使用：")
    output_lines.append("  /report → 点击「💰 收入明细」按钮")

    return output_lines
