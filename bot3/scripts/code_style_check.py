"""代码风格检查脚本

专门检查代码风格限制：
- 文件行数（≤500行）
- 函数行数（≤50行）
- 行长度（≤100字符）
生成详细报告，列出所有违规项。
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 颜色输出
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

# 代码风格限制
MAX_FILE_LINES = 500
MAX_FUNCTION_LINES = 50
MAX_LINE_LENGTH = 100


def count_file_lines(file_path: Path) -> int:
    """统计文件行数"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return len(f.readlines())
    except Exception:
        return 0


def check_line_length(file_path: Path) -> List[Tuple[int, str]]:
    """检查行长度，返回违规行列表"""
    violations = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                # 排除注释和空行
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    if len(line.rstrip("\n\r")) > MAX_LINE_LENGTH:
                        violations.append((lineno, line.rstrip("\n\r")[:80]))
    except Exception:
        pass
    return violations


def check_function_length(file_path: Path) -> List[Tuple[str, int, int]]:
    """检查函数长度，返回违规函数列表 (函数名, 行号, 行数)"""
    violations = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            tree = ast.parse(content, filename=str(file_path))

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # 计算函数行数
                func_lines = (
                    node.end_lineno - node.lineno + 1
                    if hasattr(node, "end_lineno")
                    else 0
                )
                if func_lines == 0:
                    # 如果没有end_lineno，尝试从源代码计算
                    lines = content.split("\n")
                    func_start = node.lineno - 1
                    # 简单估算：找到函数结束位置
                    indent_level = len(lines[func_start]) - len(
                        lines[func_start].lstrip()
                    )
                    func_lines = 1
                    for i in range(func_start + 1, len(lines)):
                        line = lines[i]
                        if line.strip() and not line.strip().startswith("#"):
                            current_indent = len(line) - len(line.lstrip())
                            if current_indent <= indent_level and line.strip():
                                break
                        func_lines += 1

                if func_lines > MAX_FUNCTION_LINES:
                    violations.append((node.name, node.lineno, func_lines))
    except Exception:
        pass
    return violations


def check_file_style(file_path: Path) -> Dict:
    """检查单个文件的代码风格"""
    rel_path = file_path.relative_to(project_root)
    file_lines = count_file_lines(file_path)
    long_lines = check_line_length(file_path)
    long_functions = check_function_length(file_path)

    issues = {
        "file": str(rel_path),
        "file_lines": file_lines,
        "file_too_long": file_lines > MAX_FILE_LINES,
        "long_lines": long_lines,
        "long_functions": long_functions,
    }

    return issues


def scan_project() -> Dict:
    """扫描整个项目"""
    print(f"{BLUE}开始代码风格检查...{RESET}\n")

    all_issues = {
        "long_files": [],
        "long_lines": [],
        "long_functions": [],
    }

    # 扫描所有Python文件
    python_files = []
    for pattern in [
        "handlers/**/*.py",
        "services/**/*.py",
        "db/**/*.py",
        "utils/**/*.py",
    ]:
        python_files.extend(project_root.glob(pattern))

    # 排除测试文件和特殊文件
    python_files = [
        f
        for f in python_files
        if "__pycache__" not in str(f)
        and "test" not in str(f).lower()
        and "conftest" not in str(f)
    ]

    print(f"扫描 {len(python_files)} 个文件...\n")

    for file_path in python_files:
        issues = check_file_style(file_path)

        # 检查文件长度
        if issues["file_too_long"]:
            all_issues["long_files"].append(
                {
                    "file": issues["file"],
                    "lines": issues["file_lines"],
                }
            )

        # 检查长行
        if issues["long_lines"]:
            for lineno, line_preview in issues["long_lines"]:
                all_issues["long_lines"].append(
                    {
                        "file": issues["file"],
                        "line": lineno,
                        "preview": line_preview,
                    }
                )

        # 检查长函数
        if issues["long_functions"]:
            for func_name, func_line, func_lines in issues["long_functions"]:
                all_issues["long_functions"].append(
                    {
                        "file": issues["file"],
                        "function": func_name,
                        "line": func_line,
                        "lines": func_lines,
                    }
                )

    return all_issues


def print_report(issues: Dict):
    """打印检查报告"""
    print("=" * 70)
    print("代码风格检查报告")
    print("=" * 70)

    # 文件长度检查
    print(f"\n{BLUE}[1] 文件长度检查（限制: ≤{MAX_FILE_LINES}行）{RESET}")
    if issues["long_files"]:
        print(f"  {RED}✗ 发现 {len(issues['long_files'])} 个超长文件：{RESET}")
        for item in sorted(
            issues["long_files"], key=lambda x: x["lines"], reverse=True
        ):
            print(f"    - {item['file']}: {item['lines']} 行")
    else:
        print(f"  {GREEN}✓ 所有文件符合长度要求{RESET}")

    # 行长度检查
    print(f"\n{BLUE}[2] 行长度检查（限制: ≤{MAX_LINE_LENGTH}字符）{RESET}")
    if issues["long_lines"]:
        print(f"  {YELLOW}⚠ 发现 {len(issues['long_lines'])} 个超长行：{RESET}")
        # 只显示前10个
        for item in issues["long_lines"][:10]:
            print(f"    - {item['file']}:{item['line']} - {item['preview']}...")
        if len(issues["long_lines"]) > 10:
            print(f"    ... 还有 {len(issues['long_lines']) - 10} 个超长行")
    else:
        print(f"  {GREEN}✓ 所有行符合长度要求{RESET}")

    # 函数长度检查
    print(f"\n{BLUE}[3] 函数长度检查（限制: ≤{MAX_FUNCTION_LINES}行）{RESET}")
    if issues["long_functions"]:
        print(f"  {YELLOW}⚠ 发现 {len(issues['long_functions'])} 个超长函数：{RESET}")
        # 只显示前10个
        for item in sorted(
            issues["long_functions"], key=lambda x: x["lines"], reverse=True
        )[:10]:
            print(
                f"    - {item['file']}:{item['line']} {item['function']}() - "
                f"{item['lines']} 行"
            )
        if len(issues["long_functions"]) > 10:
            print(f"    ... 还有 {len(issues['long_functions']) - 10} 个超长函数")
    else:
        print(f"  {GREEN}✓ 所有函数符合长度要求{RESET}")

    # 汇总
    print("\n" + "=" * 70)
    print("汇总")
    print("=" * 70)
    total_issues = (
        len(issues["long_files"])
        + len(issues["long_lines"])
        + len(issues["long_functions"])
    )
    if total_issues == 0:
        print(f"{GREEN}✓ 所有代码风格检查通过！{RESET}")
    else:
        print(f"{YELLOW}⚠ 共发现 {total_issues} 个代码风格问题{RESET}")
        print(f"  - 超长文件: {len(issues['long_files'])}")
        print(f"  - 超长行: {len(issues['long_lines'])}")
        print(f"  - 超长函数: {len(issues['long_functions'])}")


def main():
    """主函数"""
    issues = scan_project()
    print_report(issues)

    # 如果有问题，返回非零退出码
    total_issues = (
        len(issues["long_files"])
        + len(issues["long_lines"])
        + len(issues["long_functions"])
    )
    sys.exit(1 if total_issues > 0 else 0)


if __name__ == "__main__":
    main()
