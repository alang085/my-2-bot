"""命令检查器 - 装饰器检查模块

包含装饰器检查的逻辑。
"""

from typing import Any, Dict, List, Tuple


def check_command_decorators(
    self,
    file_path: str,
    cmd: Dict[str, Any],
    syntax_ok: bool,
    import_ok: bool,
    cmd_result: Dict[str, Any],
    results: Dict[str, Any],
) -> Tuple[bool, Dict[str, Any], Dict[str, Any]]:
    """检查命令装饰器

    Args:
        self: CommandChecker 实例
        file_path: 文件路径
        cmd: 命令信息
        syntax_ok: 语法检查是否通过
        import_ok: 导入检查是否通过
        cmd_result: 命令结果字典
        results: 结果字典

    Returns:
        Tuple[bool, Dict, Dict]: (装饰器检查通过, 更新后的cmd_result, 更新后的results)
    """
    decorator_ok = True
    if syntax_ok and import_ok:
        decorator_ok, decorator_issues = self.check_decorators(
            file_path, cmd["handler_name"], cmd["decorators"]
        )
        if not decorator_ok:
            cmd_result["status"] = (
                "warning" if cmd_result["status"] != "error" else "error"
            )
            for issue in decorator_issues:
                cmd_result["issues"].append(
                    {
                        "category": "decorators",
                        "message": issue,
                        "severity": "warning",
                    }
                )
                results["issues_by_category"]["decorators"].append(
                    {
                        "command": cmd["name"],
                        "handler": cmd["handler_name"],
                        "file": str(file_path) if file_path else "unknown",
                        "message": issue,
                    }
                )

    return decorator_ok, cmd_result, results
