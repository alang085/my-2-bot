"""命令检查报告生成模块

包含检查报告的生成功能。
"""

# 标准库
from typing import Any, Dict, List

from utils.command_checks import (check_decorators, check_import,
                                  check_service_usage, check_syntax,
                                  check_type_hints)


def _build_report_header(results: Dict[str, Any]) -> List[str]:
    """构建报告头部

    Args:
        results: 检查结果

    Returns:
        报告行列表
    """
    report = []
    report.append("=" * 70)
    report.append("命令全面检查报告")
    report.append("=" * 70)
    report.append("")
    report.append("总体统计:")
    report.append(f"  总命令数: {results['total']}")
    report.append(f"  通过: {results['passed']}")
    report.append(f"  警告: {results['warnings']}")
    report.append(f"  错误: {results['errors']}")
    report.append("")
    return report


def _build_category_section(results: Dict[str, Any]) -> List[str]:
    """构建按类别分组的报告部分

    Args:
        results: 检查结果

    Returns:
        报告行列表
    """
    report = []
    report.append("按类别分组:")
    report.append("")

    categories = {
        "syntax": "语法错误",
        "import": "导入错误",
        "decorators": "装饰器问题",
        "type_hints": "类型注解缺失",
        "service_usage": "Service层使用",
    }

    for category, category_name in categories.items():
        issues = results["issues_by_category"][category]
        count = len(issues)

        if count == 0:
            report.append(f"{category_name} (0个)")
            report.append(f"  ✅ 无问题")
        else:
            report.append(f"{category_name} ({count}个)")
            for issue in issues[:10]:
                severity = "❌" if category in ["syntax", "import"] else "⚠️"
                report.append(
                    f"  {severity} {issue['command']} ({issue['handler']}) - "
                    f"{issue['message'][:60]}"
                )
            if count > 10:
                report.append(f"  ... 还有 {count - 10} 个问题")

        report.append("")

    return report


def _build_detail_section(results: Dict[str, Any]) -> List[str]:
    """构建详细问题列表

    Args:
        results: 检查结果

    Returns:
        报告行列表
    """
    report = []
    problem_commands = [cmd for cmd in results["commands"] if cmd["status"] != "passed"]
    if problem_commands:
        report.append("详细问题列表:")
        report.append("")
        for cmd in problem_commands:
            status_icon = "❌" if cmd["status"] == "error" else "⚠️"
            report.append(f"{status_icon} /{cmd['name']} ({cmd['handler_name']})")
            if cmd["file_path"]:
                report.append(f"   文件: {cmd['file_path']}")
            for issue in cmd["issues"]:
                report.append(f"   - [{issue['category']}] {issue['message']}")
            report.append("")
    return report


def generate_report(results: Dict[str, Any]) -> str:
    """生成检查报告

    Args:
        results: 检查结果

    Returns:
        格式化的报告字符串
    """
    report = []
    report.extend(_build_report_header(results))
    report.extend(_build_category_section(results))
    report.extend(_build_detail_section(results))
    report.append("=" * 70)
    return "\n".join(report)
