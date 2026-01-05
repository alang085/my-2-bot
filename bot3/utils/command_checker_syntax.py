"""命令检查器 - 语法检查模块

包含语法检查的逻辑。
"""

from typing import Any, Dict, Tuple


def check_command_syntax(
    self,
    file_path: str,
    cmd: Dict[str, Any],
    cmd_result: Dict[str, Any],
    results: Dict[str, Any],
) -> Tuple[bool, Dict[str, Any], Dict[str, Any]]:
    """检查命令语法

    Args:
        self: CommandChecker 实例
        file_path: 文件路径
        cmd: 命令信息
        cmd_result: 命令结果字典
        results: 结果字典

    Returns:
        Tuple[bool, Dict, Dict]: (语法检查通过, 更新后的cmd_result, 更新后的results)
    """
    syntax_ok, syntax_error = (
        self.check_syntax(file_path) if file_path else (False, "文件不存在")
    )
    if not syntax_ok:
        cmd_result["status"] = "error"
        cmd_result["issues"].append(
            {
                "category": "syntax",
                "message": syntax_error,
                "severity": "error",
            }
        )
        results["issues_by_category"]["syntax"].append(
            {
                "command": cmd["name"],
                "handler": cmd["handler_name"],
                "file": str(file_path) if file_path else "unknown",
                "message": syntax_error,
            }
        )

    return syntax_ok, cmd_result, results
