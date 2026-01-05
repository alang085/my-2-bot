"""统计修复辅助函数 - 消息生成模块

包含结果消息生成的逻辑。
"""

from typing import Any, Dict, List


def build_fix_result_message(
    fixed_items: List[str], daily_fixed_count: int, income_summary: Dict[str, Any]
) -> str:
    """构建修复结果消息

    Args:
        fixed_items: 修复项列表
        daily_fixed_count: 日结修复记录数
        income_summary: 收入汇总

    Returns:
        str: 结果消息
    """
    if fixed_items or daily_fixed_count > 0:
        result_msg = "✅ 收入统计数据修复完成！\n\n"
        if fixed_items:
            result_msg += "修复的全局统计:\n"
            for item in fixed_items:
                result_msg += f"  • {item}\n"
        if daily_fixed_count > 0:
            result_msg += f"\n修复的日结统计: {daily_fixed_count} 条记录\n"
        result_msg += f"\n📊 修复后的汇总:\n"
        result_msg += f"  利息收入: {income_summary['interest']:.2f}\n"
        completed_count = income_summary["completed_count"]
        completed_amount = income_summary["completed_amount"]
        result_msg += f"  完成订单: {completed_count} 笔, {completed_amount:.2f}\n"
        breach_end_count = income_summary["breach_end_count"]
        breach_end_amount = income_summary["breach_end_amount"]
        result_msg += f"  违约完成: {breach_end_count} 笔, {breach_end_amount:.2f}\n"
    else:
        result_msg = "✅ 收入统计数据一致，无需修复。"

    return result_msg
