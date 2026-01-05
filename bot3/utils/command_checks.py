"""命令检查模块

包含各种检查方法：语法、导入、装饰器、类型注解、Service层使用等。
"""

# 标准库
import ast
import importlib
import logging
import py_compile
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


def check_syntax(file_path: Path) -> Tuple[bool, Optional[str]]:
    """检查文件语法

    Args:
        file_path: 文件路径

    Returns:
        Tuple[success, error_message]
    """
    if not file_path or not file_path.exists():
        return False, "文件不存在"

    try:
        py_compile.compile(str(file_path), doraise=True)
        return True, None
    except py_compile.PyCompileError as e:
        return False, str(e)
    except Exception as e:
        return False, f"语法检查失败: {str(e)}"


def check_import(
    handler_name: str, file_path: Optional[Path], project_root: Path
) -> Tuple[bool, Optional[str]]:
    """检查函数是否可以导入

    Args:
        handler_name: 处理函数名
        file_path: 文件路径
        project_root: 项目根目录

    Returns:
        Tuple[success, error_message]
    """
    if not file_path or not file_path.exists():
        return False, "文件不存在"

    try:
        # 确保项目根目录在 sys.path 中
        project_root_str = str(project_root)
        if project_root_str not in sys.path:
            sys.path.insert(0, project_root_str)

        # 计算模块路径
        # 例如: handlers/payment_handlers.py -> handlers.payment_handlers
        relative_path = file_path.relative_to(project_root)
        module_path = (
            str(relative_path.with_suffix("")).replace("/", ".").replace("\\", ".")
        )

        # 导入模块
        module = importlib.import_module(module_path)

        # 检查函数是否存在
        if not hasattr(module, handler_name):
            return False, f"函数 {handler_name} 不存在于模块 {module_path}"

        # 检查函数是否可调用
        func = getattr(module, handler_name)
        if not callable(func):
            return False, f"{handler_name} 不是可调用对象"

        return True, None

    except ImportError as e:
        return False, f"导入失败: {str(e)}"
    except Exception as e:
        return False, f"检查导入时出错: {str(e)}"


def _find_handler_function(
    tree: ast.AST, handler_name: str
) -> Optional[ast.FunctionDef]:
    """查找处理函数定义

    Args:
        tree: AST树
        handler_name: 函数名

    Returns:
        函数定义节点，如果未找到则返回None
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            if node.name == handler_name:
                return node
    return None


def _extract_decorators(handler_func: ast.FunctionDef) -> List[str]:
    """提取函数装饰器列表

    Args:
        handler_func: 函数定义节点

    Returns:
        装饰器名称列表
    """
    actual_decorators = []
    for decorator in handler_func.decorator_list:
        if isinstance(decorator, ast.Name):
            actual_decorators.append(decorator.id)
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                actual_decorators.append(decorator.func.id)
    return actual_decorators


def _check_decorator_order(actual_decorators: List[str]) -> List[str]:
    """检查装饰器顺序

    Args:
        actual_decorators: 实际装饰器列表

    Returns:
        问题列表
    """
    issues = []
    if "error_handler" in actual_decorators:
        error_handler_idx = actual_decorators.index("error_handler")
        if error_handler_idx != 0:
            issues.append(
                f"装饰器顺序错误: @error_handler 应该在最外层（当前在第 {error_handler_idx + 1} 层）"
            )
    return issues


def _check_required_decorators(actual_decorators: List[str]) -> List[str]:
    """检查必需的装饰器

    Args:
        actual_decorators: 实际装饰器列表

    Returns:
        问题列表
    """
    issues = []
    if "error_handler" not in actual_decorators:
        issues.append("缺少 @error_handler 装饰器")
    return issues


def check_decorators(
    file_path: Path, handler_name: str, expected_decorators: List[str]
) -> Tuple[bool, List[str]]:
    """检查装饰器

    Args:
        file_path: 文件路径
        handler_name: 处理函数名
        expected_decorators: 从 main.py 提取的装饰器列表

    Returns:
        Tuple[success, issues]
    """
    if not file_path or not file_path.exists():
        return False, ["文件不存在"]

    issues = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content, filename=str(file_path))
        handler_func = _find_handler_function(tree, handler_name)

        if not handler_func:
            issues.append(f"未找到函数 {handler_name}")
            return False, issues

        actual_decorators = _extract_decorators(handler_func)
        issues.extend(_check_decorator_order(actual_decorators))
        issues.extend(_check_required_decorators(actual_decorators))

        return len(issues) == 0, issues

    except SyntaxError as e:
        issues.append(f"语法错误: {str(e)}")
        return False, issues
    except Exception as e:
        issues.append(f"检查装饰器时出错: {str(e)}")
        return False, issues


def _find_handler_function(
    tree: ast.AST, handler_name: str
) -> Optional[ast.FunctionDef]:
    """查找处理函数定义

    Args:
        tree: AST树
        handler_name: 函数名

    Returns:
        函数节点或None
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            if node.name == handler_name:
                return node
    return None


def _check_function_type_annotations(handler_func: ast.FunctionDef) -> List[str]:
    """检查函数类型注解

    Args:
        handler_func: 函数节点

    Returns:
        问题列表
    """
    issues = []

    if handler_func.returns is None:
        issues.append("缺少返回类型注解（应添加 -> None 或具体类型）")

    for arg in handler_func.args.args:
        if arg.annotation is None and arg.arg != "self":
            if arg.arg not in ["update", "context"]:
                issues.append(f"参数 {arg.arg} 缺少类型注解")

    return issues


def check_type_hints(file_path: Path, handler_name: str) -> Tuple[bool, List[str]]:
    """检查类型注解

    Args:
        file_path: 文件路径
        handler_name: 处理函数名

    Returns:
        Tuple[success, issues]
    """
    if not file_path or not file_path.exists():
        return False, ["文件不存在"]

    issues = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content, filename=str(file_path))
        handler_func = _find_handler_function(tree, handler_name)

        if not handler_func:
            issues.append(f"未找到函数 {handler_name}")
            return False, issues

        issues.extend(_check_function_type_annotations(handler_func))
        return len(issues) == 0, issues

    except SyntaxError as e:
        issues.append(f"语法错误: {str(e)}")
        return False, issues
    except Exception as e:
        issues.append(f"检查类型注解时出错: {str(e)}")
        return False, issues


def _extract_function_content(content: str, handler_name: str) -> str:
    """提取函数内容

    Args:
        content: 文件内容
        handler_name: 函数名

    Returns:
        函数内容字符串
    """
    lines = content.split("\n")
    in_function = False
    function_lines = []

    for i, line in enumerate(lines):
        if re.match(rf"^(async\s+)?def\s+{handler_name}\s*\(", line):
            in_function = True
            function_lines.append((i + 1, line))
        elif in_function:
            if re.match(
                r"^(async\s+)?def\s+|^class\s+", line
            ) and not line.strip().startswith("#"):
                break
            function_lines.append((i + 1, line))

    return "\n".join([line for _, line in function_lines])


def _check_direct_db_operations(function_content: str) -> List[str]:
    """检查直接调用 db_operations

    Args:
        function_content: 函数内容

    Returns:
        问题列表
    """
    issues = []
    db_ops_patterns = [
        r"await\s+db_operations\.(update_|create_|delete_|get_.*\(.*\)(?!.*record_operation))",
        r"db_operations\.(update_|create_|delete_|get_.*\(.*\)(?!.*record_operation))",
    ]

    for pattern in db_ops_patterns:
        matches = re.finditer(pattern, function_content)
        for match in matches:
            call_expr = match.group(0)
            if "record_operation" not in call_expr:
                issues.append(f"直接调用 db_operations: {call_expr.strip()[:50]}")

    return issues


def _check_service_usage(function_content: str) -> bool:
    """检查是否使用了 Service 层

    Args:
        function_content: 函数内容

    Returns:
        是否使用了 Service
    """
    service_patterns = [
        r"PaymentService\.",
        r"OrderService\.",
        r"GroupMessageService\.",
        r"AmountService\.",
        r"UndoService\.",
        r"StatsService\.",
    ]
    return any(re.search(pattern, function_content) for pattern in service_patterns)


def check_service_usage(file_path: Path, handler_name: str) -> Tuple[bool, List[str]]:
    """检查是否使用 Service 层

    Args:
        file_path: 文件路径
        handler_name: 处理函数名

    Returns:
        Tuple[success, issues] - success 表示使用了 Service 层
    """
    if not file_path or not file_path.exists():
        return True, []

    issues = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        function_content = _extract_function_content(content, handler_name)
        issues = _check_direct_db_operations(function_content)
        uses_service = _check_service_usage(function_content)

        if issues and not uses_service:
            issues.append("建议使用 Service 层替代直接调用 db_operations")

        return len(issues) == 0, issues

    except Exception as e:
        issues.append(f"检查 Service 使用时出错: {str(e)}")
        return False, issues
