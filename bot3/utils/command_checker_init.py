"""命令检查器 - 初始化模块

包含初始化结果字典的逻辑。
"""

from typing import Any, Dict, List


def init_check_results(commands: List[Dict[str, Any]]) -> Dict[str, Any]:
    """初始化检查结果字典

    Args:
        commands: 命令列表

    Returns:
        Dict: 初始化的结果字典
    """
    return {
        "total": len(commands),
        "passed": 0,
        "warnings": 0,
        "errors": 0,
        "commands": [],
        "issues_by_category": {
            "syntax": [],
            "import": [],
            "decorators": [],
            "type_hints": [],
            "service_usage": [],
        },
    }


def init_command_result(cmd: Dict[str, Any]) -> Dict[str, Any]:
    """初始化命令结果字典

    Args:
        cmd: 命令信息

    Returns:
        Dict: 初始化的命令结果字典
    """
    return {
        "name": cmd["name"],
        "handler_name": cmd["handler_name"],
        "file_path": cmd["file_path"],
        "status": "unknown",
        "issues": [],
    }
