"""命令检查器 - 状态更新模块

包含状态更新和统计的逻辑。
"""

from typing import Any, Dict


def update_command_status(
    cmd_result: Dict[str, Any], results: Dict[str, Any]
) -> Dict[str, Any]:
    """更新命令状态和统计

    Args:
        cmd_result: 命令结果字典
        results: 结果字典

    Returns:
        Dict: 更新后的results
    """
    # 更新状态
    if cmd_result["status"] == "unknown":
        cmd_result["status"] = "passed"
        results["passed"] += 1
    elif cmd_result["status"] == "error":
        results["errors"] += 1
    elif cmd_result["status"] == "warning":
        results["warnings"] += 1

    return results
