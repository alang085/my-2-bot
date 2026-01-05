"""数据诊断命令处理器"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

import db_operations
from decorators import admin_required, error_handler, private_chat_only
from handlers.module5_data.diagnostic_helpers_consistency import \
    check_all_consistencies
from handlers.module5_data.diagnostic_helpers_date import parse_date_range
from handlers.module5_data.diagnostic_helpers_message import send_long_message
from handlers.module5_data.diagnostic_helpers_report import (
    generate_report_footer, generate_report_header)
from handlers.module5_data.diagnostic_helpers_summary import \
    calculate_income_summary

logger = logging.getLogger(__name__)


@error_handler
@admin_required
@private_chat_only
async def check_mismatch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """检查收入明细和统计数据的不一致问题（管理员命令）"""
    # 获取日期参数
    start_date, end_date = parse_date_range(context.args or [])

    # 发送开始消息
    msg = await update.message.reply_text("🔍 正在检查数据不一致问题，请稍候...")

    # 获取所有收入明细统计
    income_records = await db_operations.get_income_records(start_date, end_date)

    # 计算收入明细汇总
    income_summary = calculate_income_summary(income_records)

    # 获取统计数据
    stats = await db_operations.get_stats_by_date_range(start_date, end_date, None)
    financial_data = await db_operations.get_financial_data()

    # 生成报告头部
    output_lines = generate_report_header(
        start_date, end_date, income_summary, stats, financial_data
    )

    # 检查所有数据一致性
    mismatches = check_all_consistencies(
        stats, financial_data, income_summary, output_lines
    )

    # 生成报告尾部
    output_lines.extend(generate_report_footer(mismatches))

    # 发送报告
    output = "\n".join(output_lines)
    await send_long_message(update, msg, output)


@error_handler
@admin_required
@private_chat_only
async def _analyze_income_records_section(output_lines: list) -> dict:
    """分析收入记录部分，返回分析结果"""
    import db_operations
    from handlers.module5_data.diagnostic_helpers_analysis import \
        analyze_income_records
    from handlers.module5_data.diagnostic_helpers_report_detailed import \
        generate_income_records_analysis_section

    all_records = await db_operations.get_income_records(
        "1970-01-01", "2099-12-31", include_undone=True
    )
    valid_records = await db_operations.get_income_records(
        "1970-01-01", "2099-12-31", include_undone=False
    )
    undone_records = [r for r in all_records if r.get("is_undone", 0) == 1]

    analysis_result = analyze_income_records(all_records, valid_records, undone_records)
    all_by_type = analysis_result["all_by_type"]
    valid_by_type = analysis_result["valid_by_type"]
    undone_by_type = analysis_result["undone_by_type"]

    output_lines.extend(
        generate_income_records_analysis_section(
            all_records,
            valid_records,
            undone_records,
            all_by_type,
            valid_by_type,
            undone_by_type,
        )
    )

    return {
        "all_records": all_records,
        "valid_records": valid_records,
        "undone_records": undone_records,
        "valid_by_type": valid_by_type,
    }


async def _analyze_statistics_comparison(
    output_lines: list, valid_by_type: dict
) -> dict:
    """分析统计比较部分，返回差异数据"""
    import db_operations
    from handlers.module5_data.diagnostic_helpers_analysis import \
        calculate_differences
    from handlers.module5_data.diagnostic_helpers_report_detailed import \
        generate_statistics_comparison_section

    financial_data = await db_operations.get_financial_data()
    await db_operations.get_all_group_ids()

    differences = calculate_differences(financial_data, valid_by_type)
    interest_diff = differences["interest_diff"]
    completed_diff = differences["completed_diff"]
    breach_end_diff = differences["breach_end_diff"]

    output_lines.extend(
        generate_statistics_comparison_section(
            financial_data,
            valid_by_type,
            interest_diff,
            completed_diff,
            breach_end_diff,
        )
    )

    return {
        "interest_diff": interest_diff,
        "completed_diff": completed_diff,
        "breach_end_diff": breach_end_diff,
    }


async def diagnose_data_inconsistency(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """诊断数据不一致的详细原因（管理员命令）

    分析 income_records 与 financial_data/grouped_data 不一致的具体原因：
    1. 检查 income_records 表的完整情况（包括已撤销记录）
    2. 检查数据的时间范围
    3. 分析差异的具体来源
    4. 提供修复建议
    """
    from handlers.module5_data.diagnostic_helpers_analysis import (
        analyze_possible_reasons, get_date_range)
    from handlers.module5_data.diagnostic_helpers_report_detailed import (
        generate_date_range_section, generate_fix_suggestions_section,
        generate_reasons_section)

    msg = await update.message.reply_text("🔍 正在诊断数据不一致原因，请稍候...")

    output_lines: list[str] = []
    output_lines.append("🔬 数据不一致诊断报告")
    output_lines.append("=" * 60)
    output_lines.append("")

    analysis_data = await _analyze_income_records_section(output_lines)

    min_date, max_date = get_date_range(analysis_data["all_records"])
    output_lines.extend(generate_date_range_section(min_date, max_date))

    differences = await _analyze_statistics_comparison(
        output_lines, analysis_data["valid_by_type"]
    )

    reasons = analyze_possible_reasons(
        differences["interest_diff"],
        differences["completed_diff"],
        differences["breach_end_diff"],
        analysis_data["undone_records"],
        analysis_data["all_records"],
    )
    output_lines.extend(generate_reasons_section(reasons))
    output_lines.extend(generate_fix_suggestions_section())

    report = "\n".join(output_lines)
    await msg.edit_text(report)
