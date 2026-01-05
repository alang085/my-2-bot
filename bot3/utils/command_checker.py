"""命令全面检查工具（向后兼容层）

此文件保留用于向后兼容，实际功能已拆分到：
- command_discovery.py - 命令发现
- command_checks.py - 各种检查方法
- command_report.py - 报告生成
"""

# 标准库
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 本地模块
from utils.command_checks import (check_decorators, check_import,
                                  check_service_usage, check_syntax,
                                  check_type_hints)
from utils.command_discovery import discover_commands
from utils.command_report import generate_report

logger = logging.getLogger(__name__)


class CommandChecker:
    """命令检查器"""

    def __init__(self, project_root: Optional[Path] = None):
        """初始化检查器

        Args:
            project_root: 项目根目录，如果为 None 则自动检测
        """
        if project_root is None:
            # 自动检测项目根目录
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent

        self.project_root = project_root
        self.main_py = project_root / "main.py"
        self.handlers_dir = project_root / "handlers"
        self.commands: List[Dict[str, Any]] = []
        self.issues: List[Dict[str, Any]] = []

    def discover_commands(self) -> List[Dict[str, Any]]:
        """从 main.py 中提取所有注册的命令

        Returns:
            命令列表，每个命令包含：name, handler_func, decorators, file_path
        """
        commands = discover_commands(self.main_py, self.handlers_dir)
        self.commands = commands
        return commands

    def check_syntax(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """检查文件语法"""
        return check_syntax(file_path)

    def check_import(
        self, handler_name: str, file_path: Optional[Path]
    ) -> Tuple[bool, Optional[str]]:
        """检查函数是否可以导入"""
        return check_import(handler_name, file_path, self.project_root)

    def check_decorators(
        self, file_path: Path, handler_name: str, expected_decorators: List[str]
    ) -> Tuple[bool, List[str]]:
        """检查装饰器"""
        return check_decorators(file_path, handler_name, expected_decorators)

    def check_type_hints(
        self, file_path: Path, handler_name: str
    ) -> Tuple[bool, List[str]]:
        """检查类型注解"""
        return check_type_hints(file_path, handler_name)

    def check_service_usage(
        self, file_path: Path, handler_name: str
    ) -> Tuple[bool, List[str]]:
        """检查是否使用 Service 层"""
        return check_service_usage(file_path, handler_name)

    def _run_all_checks_for_command(
        self, cmd: Dict, cmd_result: Dict, results: Dict[str, Any]
    ) -> Tuple[Dict, Dict[str, Any]]:
        """为单个命令运行所有检查

        Args:
            cmd: 命令字典
            cmd_result: 命令检查结果
            results: 总体检查结果

        Returns:
            (更新后的命令检查结果, 更新后的总体检查结果)
        """
        from utils.command_checker_decorators import check_command_decorators
        from utils.command_checker_import import check_command_import
        from utils.command_checker_service import check_command_service_usage
        from utils.command_checker_status import update_command_status
        from utils.command_checker_syntax import check_command_syntax
        from utils.command_checker_type_hints import check_command_type_hints

        file_path = cmd["file_path"]

        syntax_ok, cmd_result, results = check_command_syntax(
            self, file_path, cmd, cmd_result, results
        )

        import_ok, cmd_result, results = check_command_import(
            self, cmd, file_path, cmd_result, results
        )

        _, cmd_result, results = check_command_decorators(
            self, file_path, cmd, syntax_ok, import_ok, cmd_result, results
        )

        _, cmd_result, results = check_command_type_hints(
            self, file_path, cmd, syntax_ok, cmd_result, results
        )

        _, cmd_result, results = check_command_service_usage(
            self, file_path, cmd, syntax_ok, cmd_result, results
        )

        results = update_command_status(cmd_result, results)
        results["commands"].append(cmd_result)

        return cmd_result, results

    def check_all(self) -> Dict[str, Any]:
        """执行所有检查

        Returns:
            检查结果字典
        """
        from utils.command_checker_init import (init_check_results,
                                                init_command_result)

        commands = self.discover_commands()
        logger.info(f"发现 {len(commands)} 个命令")

        results = init_check_results(commands)

        for cmd in commands:
            cmd_result = init_command_result(cmd)
            _, results = self._run_all_checks_for_command(cmd, cmd_result, results)

        return results

    def generate_report(self, results: Dict[str, Any]) -> str:
        """生成检查报告"""
        return generate_report(results)


def main():
    """主函数"""
    import sys
    from pathlib import Path

    # 设置项目根目录
    project_root = Path(__file__).parent.parent

    # 创建检查器
    checker = CommandChecker(project_root)

    # 执行检查
    print("🔍 开始检查所有命令...")
    results = checker.check_all()

    # 生成报告
    report = checker.generate_report(results)
    print(report)

    # 返回退出码
    if results["errors"] > 0:
        sys.exit(1)
    elif results["warnings"] > 0:
        sys.exit(0)  # 有警告但不退出
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
