"""命令发现模块

包含从main.py中提取和发现命令的相关功能。
"""

# 标准库
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def extract_imported_functions(content: str) -> Dict[str, str]:
    """从 main.py 中提取所有导入的函数名及其来源模块

    Args:
        content: main.py 文件内容

    Returns:
        字典：{函数名: 模块路径}
    """
    imported = {}

    # 匹配 from ... import ... 格式
    from_pattern = r"from\s+([\w.]+)\s+import\s+([^#\n]+)"
    for match in re.finditer(from_pattern, content):
        module_path = match.group(1)
        imports_str = match.group(2).strip()

        # 解析导入的函数名（支持 as 别名）
        for item in imports_str.split(","):
            item = item.strip()
            if " as " in item:
                func_name = item.split(" as ")[1].strip()
                original_name = item.split(" as ")[0].strip()
                imported[func_name] = f"{module_path}.{original_name}"
            else:
                func_name = item.strip()
                imported[func_name] = f"{module_path}.{func_name}"

    # 匹配 import ... 格式（较少使用）
    import_pattern = r"import\s+([\w.]+)(?:\s+as\s+(\w+))?"
    for match in re.finditer(import_pattern, content):
        module_path = match.group(1)
        alias = match.group(2) if match.group(2) else module_path.split(".")[-1]
        imported[alias] = module_path

    return imported


def _get_known_decorators() -> set:
    """获取已知的装饰器列表

    Returns:
        装饰器集合
    """
    return {
        "error_handler",
        "authorized_required",
        "admin_required",
        "private_chat_only",
        "group_chat_only",
    }


def _extract_from_stack_parsing(expr: str, known_decorators: set) -> Optional[str]:
    """通过栈解析提取函数名

    Args:
        expr: 表达式字符串
        known_decorators: 已知装饰器集合

    Returns:
        函数名，如果未找到则返回None
    """
    stack = []
    i = 0
    while i < len(expr):
        if expr[i] == "(":
            j = i - 1
            while j >= 0 and (expr[j].isalnum() or expr[j] == "_"):
                j -= 1
            func_name = expr[j + 1 : i].strip()
            if func_name:
                stack.append((func_name, i))
            i += 1
        elif expr[i] == ")":
            if stack:
                func_name, pos = stack.pop()
                if func_name not in known_decorators:
                    return func_name
            i += 1
        else:
            i += 1

    if stack:
        return stack[-1][0]
    return None


def _extract_from_regex_matching(expr: str, known_decorators: set) -> Optional[str]:
    """通过正则表达式匹配提取函数名

    Args:
        expr: 表达式字符串
        known_decorators: 已知装饰器集合

    Returns:
        函数名，如果未找到则返回None
    """
    all_matches = re.findall(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", expr)
    for match in reversed(all_matches):
        if match not in known_decorators:
            return match

    match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)", expr)
    if match:
        return match.group(1)

    return expr.split("(")[0].strip() if "(" in expr else None


def extract_handler_name_from_expr(
    handler_expr: str, imported_functions: Dict[str, str]
) -> str:
    """从处理表达式提取函数名（新方法，支持装饰器链）

    Args:
        handler_expr: 处理函数表达式，如 "error_handler(authorized_required(show_gcash))"
        imported_functions: 导入的函数映射

    Returns:
        函数名
    """
    expr = handler_expr.strip()
    known_decorators = _get_known_decorators()

    result = _extract_from_stack_parsing(expr, known_decorators)
    if result:
        return result

    result = _extract_from_regex_matching(expr, known_decorators)
    if result:
        return result

    return expr.split("(")[0].strip()


def extract_handler_name_old(handler_expr: str) -> str:
    """从处理表达式提取函数名（旧方法，用于向后兼容）

    Args:
        handler_expr: 处理函数表达式

    Returns:
        函数名
    """
    expr = handler_expr.strip()

    # 移除所有装饰器调用
    while True:
        match = re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*\s*\((.*)\)$", expr)
        if not match:
            break
        expr = match.group(1).strip()

    # 提取函数名
    match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)", expr)
    if match:
        return match.group(1)

    return expr


def extract_decorators(handler_expr: str) -> List[str]:
    """从处理表达式提取装饰器列表

    Args:
        handler_expr: 处理函数表达式

    Returns:
        装饰器列表
    """
    decorators = []
    expr = handler_expr.strip()

    # 提取所有装饰器函数名
    # 例如: error_handler(authorized_required(private_chat_only(show_gcash)))
    # 应该提取: ['error_handler', 'authorized_required', 'private_chat_only']
    while True:
        match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*)\)$", expr)
        if not match:
            break

        decorator_name = match.group(1)
        decorators.append(decorator_name)
        expr = match.group(2).strip()

    return decorators


def find_handler_file(handler_name: str, handlers_dir: Path) -> Optional[Path]:
    """查找处理函数所在的文件

    Args:
        handler_name: 处理函数名
        handlers_dir: handlers目录路径

    Returns:
        文件路径，如果未找到则返回None
    """
    # 在 handlers 目录下搜索
    if not handlers_dir.exists():
        return None

    for py_file in handlers_dir.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue

        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
                # 检查是否包含函数定义
                if re.search(
                    rf"^(async\s+)?def\s+{handler_name}\s*\(", content, re.MULTILINE
                ):
                    return py_file
        except Exception:
            continue

    return None


def _extract_command_handlers_from_content(content: str) -> List[re.Match]:
    """从内容中提取CommandHandler匹配

    Args:
        content: 文件内容

    Returns:
        匹配对象列表
    """
    pattern = r'CommandHandler\s*\(\s*["\']([^"\']+)["\']\s*,\s*([^)]+)\)'
    return list(re.finditer(pattern, content))


def _process_command_match(
    match: re.Match, imported_functions: Dict[str, str], handlers_dir: Path
) -> Dict[str, Any]:
    """处理单个命令匹配

    Args:
        match: 正则匹配对象
        imported_functions: 导入函数映射
        handlers_dir: handlers目录路径

    Returns:
        命令字典
    """
    command_name = match.group(1)
    handler_expr = match.group(2).strip()

    handler_name = extract_handler_name_from_expr(handler_expr, imported_functions)
    decorators = extract_decorators(handler_expr)
    file_path = find_handler_file(handler_name, handlers_dir)

    return {
        "name": command_name,
        "handler_name": handler_name,
        "handler_expr": handler_expr,
        "decorators": decorators,
        "file_path": file_path,
    }


def discover_commands(main_py: Path, handlers_dir: Path) -> List[Dict[str, Any]]:
    """从 main.py 中提取所有注册的命令

    Args:
        main_py: main.py 文件路径
        handlers_dir: handlers目录路径

    Returns:
        命令列表，每个命令包含：name, handler_func, decorators, file_path
    """
    if not main_py.exists():
        logger.error(f"main.py 不存在: {main_py}")
        return []

    commands = []
    try:
        with open(main_py, "r", encoding="utf-8") as f:
            content = f.read()

        imported_functions = extract_imported_functions(content)
        matches = _extract_command_handlers_from_content(content)

        for match in matches:
            cmd = _process_command_match(match, imported_functions, handlers_dir)
            commands.append(cmd)

    except Exception as e:
        logger.error(f"提取命令失败: {e}", exc_info=True)

    return commands
