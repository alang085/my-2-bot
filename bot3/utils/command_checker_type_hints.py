"""命令检查器 - 类型注解检查模块

包含类型注解检查的逻辑。
"""

from typing import Any, Dict, Tuple


def check_command_type_hints(
    self,
    file_path: str,
    cmd: Dict[str, Any],
    syntax_ok: bool,
    cmd_result: Dict[str, Any],
    results: Dict[str, Any],
) -> Tuple[bool, Dict[str, Any], Dict[str, Any]]:
    """检查命令类型注解

    Args:
        self: CommandChecker 实例
        file_path: 文件路径
        cmd: 命令信息
        syntax_ok: 语法检查是否通过
        cmd_result: 命令结果字典
        results: 结果字典

    Returns:
        Tuple[bool, Dict, Dict]: (类型注解检查通过, 更新后的cmd_result, 更新后的results)
    """
    type_ok = True
    if syntax_ok:
        type_ok, type_issues = self.check_type_hints(file_path, cmd["handler_name"])
        if not type_ok:
            if cmd_result["status"] == "unknown":
                cmd_result["status"] = "warning"
            for issue in type_issues:
                cmd_result["issues"].append(
                    {
                        "category": "type_hints",
                        "message": issue,
                        "severity": "warning",
                    }
                )
                results["issues_by_category"]["type_hints"].append(
                    {
                        "command": cmd["name"],
                        "handler": cmd["handler_name"],
                        "file": str(file_path) if file_path else "unknown",
                        "message": issue,
                    }
                )

    return type_ok, cmd_result, results
