"""命令检查器 - 导入检查模块

包含导入检查的逻辑。
"""

from typing import Any, Dict, Tuple


def check_command_import(
    self,
    cmd: Dict[str, Any],
    file_path: str,
    cmd_result: Dict[str, Any],
    results: Dict[str, Any],
) -> Tuple[bool, Dict[str, Any], Dict[str, Any]]:
    """检查命令导入

    Args:
        self: CommandChecker 实例
        cmd: 命令信息
        file_path: 文件路径
        cmd_result: 命令结果字典
        results: 结果字典

    Returns:
        Tuple[bool, Dict, Dict]: (导入检查通过, 更新后的cmd_result, 更新后的results)
    """
    import_ok, import_error = self.check_import(cmd["handler_name"], file_path)
    if not import_ok:
        cmd_result["status"] = "error"
        cmd_result["issues"].append(
            {
                "category": "import",
                "message": import_error,
                "severity": "error",
            }
        )
        results["issues_by_category"]["import"].append(
            {
                "command": cmd["name"],
                "handler": cmd["handler_name"],
                "file": str(file_path) if file_path else "unknown",
                "message": import_error,
            }
        )

    return import_ok, cmd_result, results
