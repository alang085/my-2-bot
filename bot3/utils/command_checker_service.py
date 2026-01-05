"""命令检查器 - Service层使用检查模块

包含Service层使用检查的逻辑。
"""

from typing import Any, Dict, Tuple


def check_command_service_usage(
    self,
    file_path: str,
    cmd: Dict[str, Any],
    syntax_ok: bool,
    cmd_result: Dict[str, Any],
    results: Dict[str, Any],
) -> Tuple[bool, Dict[str, Any], Dict[str, Any]]:
    """检查命令Service层使用

    Args:
        self: CommandChecker 实例
        file_path: 文件路径
        cmd: 命令信息
        syntax_ok: 语法检查是否通过
        cmd_result: 命令结果字典
        results: 结果字典

    Returns:
        Tuple[bool, Dict, Dict]: (Service层使用检查通过, 更新后的cmd_result, 更新后的results)
    """
    service_ok = True
    if syntax_ok:
        service_ok, service_issues = self.check_service_usage(
            file_path, cmd["handler_name"]
        )
        if not service_ok:
            if cmd_result["status"] == "unknown":
                cmd_result["status"] = "warning"
            for issue in service_issues:
                cmd_result["issues"].append(
                    {
                        "category": "service_usage",
                        "message": issue,
                        "severity": "warning",
                    }
                )
                results["issues_by_category"]["service_usage"].append(
                    {
                        "command": cmd["name"],
                        "handler": cmd["handler_name"],
                        "file": str(file_path) if file_path else "unknown",
                        "message": issue,
                    }
                )

    return service_ok, cmd_result, results
