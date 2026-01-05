"""代码质量检查脚本

整合了功能检测、代码质量检测和质量检查的所有功能。
运行所有代码质量检查工具，生成质量报告。
"""

import ast
import asyncio
import importlib
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 颜色输出
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def run_command(cmd: list, description: str) -> tuple[bool, str]:
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=300,
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, f"命令超时: {description}"
    except Exception as e:
        return False, f"执行失败: {e}"


def check_code_formatting() -> dict:
    """检查代码格式"""
    print(f"{BLUE}[1] 代码格式检查（black）{RESET}")
    success, output = run_command(
        ["python3", "-m", "black", "--check", "."], "代码格式检查"
    )
    if success:
        print(f"  {GREEN}✓ 代码格式正确{RESET}")
    else:
        lines = output.split("\n")
        error_count = sum(1 for line in lines if "would reformat" in line)
        print(f"  {YELLOW}⚠ 发现 {error_count} 个文件需要格式化{RESET}")
    return {"tool": "black", "success": success, "output": output}


def check_import_sorting() -> dict:
    """检查导入排序"""
    print(f"\n{BLUE}[2] 导入排序检查（isort）{RESET}")
    success, output = run_command(
        ["python3", "-m", "isort", "--check", "."], "导入排序检查"
    )
    if success:
        print(f"  {GREEN}✓ 导入排序正确{RESET}")
    else:
        lines = output.split("\n")
        error_count = sum(
            1 for line in lines if "ERROR" in line or "would reformat" in line
        )
        print(f"  {YELLOW}⚠ 发现 {error_count} 个文件需要整理导入{RESET}")
    return {"tool": "isort", "success": success, "output": output}


def check_type_hints() -> dict:
    """检查类型注解"""
    print(f"\n{BLUE}[3] 类型注解检查（mypy）{RESET}")
    try:
        success, output = run_command(["python3", "-m", "mypy", "."], "类型注解检查")
        if success:
            print(f"  {GREEN}✓ 类型注解检查通过{RESET}")
        else:
            error_count = output.count("error:")
            print(f"  {YELLOW}⚠ 发现 {error_count} 个类型错误{RESET}")
        return {"tool": "mypy", "success": success, "output": output, "available": True}
    except Exception:
        print(f"  {YELLOW}⚠ mypy未安装{RESET}")
        return {
            "tool": "mypy",
            "success": False,
            "output": "mypy未安装",
            "available": False,
        }


def check_code_quality() -> dict:
    """检查代码质量"""
    print(f"\n{BLUE}[4] 代码质量检查（pylint）{RESET}")
    try:
        success, output = run_command(
            ["python3", "-m", "pylint", "handlers/", "services/", "--disable=C0111"],
            "代码质量检查",
        )
        if success:
            print(f"  {GREEN}✓ 代码质量检查通过{RESET}")
        else:
            error_count = output.count(": error")
            print(f"  {YELLOW}⚠ 发现 {error_count} 个代码质量问题{RESET}")
        return {
            "tool": "pylint",
            "success": success,
            "output": output,
            "available": True,
        }
    except Exception:
        print(f"  {YELLOW}⚠ pylint未安装{RESET}")
        return {
            "tool": "pylint",
            "success": False,
            "output": "pylint未安装",
            "available": False,
        }


def check_security() -> dict:
    """安全检查"""
    print(f"\n{BLUE}[5] 安全检查（bandit）{RESET}")
    try:
        success, output = run_command(
            ["python3", "-m", "bandit", "-r", ".", "-f", "json"], "安全检查"
        )
        if success:
            print(f"  {GREEN}✓ 安全检查通过{RESET}")
        else:
            # 解析bandit输出
            import json

            try:
                issues = json.loads(output)
                high_issues = sum(
                    1
                    for item in issues.get("results", [])
                    if item.get("issue_severity") == "HIGH"
                )
                print(f"  {YELLOW}⚠ 发现 {high_issues} 个高风险安全问题{RESET}")
            except Exception:
                print(f"  {YELLOW}⚠ 安全检查发现问题{RESET}")
        return {
            "tool": "bandit",
            "success": success,
            "output": output,
            "available": True,
        }
    except Exception:
        print(f"  {YELLOW}⚠ bandit未安装{RESET}")
        return {
            "tool": "bandit",
            "success": False,
            "output": "bandit未安装",
            "available": False,
        }


def check_test_coverage() -> dict:
    """检查测试覆盖率"""
    print(f"\n{BLUE}[6] 测试覆盖率检查{RESET}")
    success, output = run_command(
        ["python3", "-m", "pytest", "--cov=.", "--cov-report=term", "-q"],
        "测试覆盖率检查",
    )

    # 解析覆盖率
    coverage = 0.0
    for line in output.split("\n"):
        if "TOTAL" in line and "%" in line:
            import re

            match = re.search(r"(\d+)%", line)
            if match:
                coverage = float(match.group(1))
                break

    if coverage >= 80:
        print(f"  {GREEN}✓ 测试覆盖率: {coverage:.2f}%{RESET}")
    elif coverage >= 60:
        print(f"  {YELLOW}⚠ 测试覆盖率: {coverage:.2f}%（建议达到80%+）{RESET}")
    else:
        print(f"  {RED}✗ 测试覆盖率: {coverage:.2f}%（需要提升）{RESET}")

    return {
        "tool": "coverage",
        "success": success,
        "coverage": coverage,
        "output": output,
    }


def check_import(module_path: str) -> tuple[bool, str]:
    """检查模块是否可以导入"""
    try:
        importlib.import_module(module_path)
        return True, ""
    except Exception as e:
        return False, str(e)


def check_syntax(file_path: Path) -> tuple[bool, str]:
    """检查文件语法"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            ast.parse(f.read())
        return True, ""
    except SyntaxError as e:
        return False, f"语法错误: {e.msg} at line {e.lineno}"


def check_duplicate_functions() -> int:
    """检测重复的函数定义"""
    print(f"\n{BLUE}[7] 重复函数检测{RESET}")
    function_bodies = defaultdict(list)

    for py_file in project_root.rglob("*.py"):
        if "__pycache__" in str(py_file) or "test" in str(py_file).lower():
            continue

        try:
            with open(py_file, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(py_file))

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.body:
                        try:
                            # 获取函数体的前几行作为签名
                            body_str = ast.dump(node.body[:3])
                            key = f"{node.name}:{body_str[:100]}"
                            function_bodies[key].append(
                                (py_file, node.name, node.lineno)
                            )
                        except Exception:
                            pass
        except Exception:
            pass

    duplicate_count = 0
    for key, occurrences in function_bodies.items():
        if len(occurrences) > 1:
            duplicate_count += len(occurrences) - 1
            if duplicate_count <= 5:  # 只显示前5个
                print(f"  {YELLOW}⚠ 发现重复函数: {occurrences[0][1]}{RESET}")
                for file_path, func_name, lineno in occurrences:
                    rel_path = file_path.relative_to(project_root)
                    print(f"    - {rel_path}:{lineno}")

    if duplicate_count == 0:
        print(f"  {GREEN}✓ 未发现重复函数{RESET}")
    else:
        print(f"  {YELLOW}⚠ 共发现 {duplicate_count} 个可能的重复函数{RESET}")

    return duplicate_count


def check_unused_imports() -> int:
    """检测未使用的导入"""
    print(f"\n{BLUE}[8] 未使用导入检测{RESET}")
    # 使用vulture检测未使用的代码
    try:
        success, output = run_command(
            ["python3", "-m", "vulture", ".", "--min-confidence", "80"], "Vulture检测"
        )
        unused_count = output.count("unused")
        if unused_count == 0:
            print(f"  {GREEN}✓ 未发现未使用的导入{RESET}")
        else:
            print(f"  {YELLOW}⚠ 发现 {unused_count} 个可能的未使用项{RESET}")
        return unused_count
    except Exception:
        print(f"  {YELLOW}⚠ vulture未安装，跳过检测{RESET}")
        return 0


def check_todo_comments() -> int:
    """检测TODO/FIXME注释"""
    print(f"\n{BLUE}[9] TODO/FIXME注释检测{RESET}")
    todo_count = 0
    for py_file in project_root.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                for lineno, line in enumerate(f, 1):
                    if "TODO" in line.upper() or "FIXME" in line.upper():
                        todo_count += 1
                        if todo_count <= 5:  # 只显示前5个
                            rel_path = py_file.relative_to(project_root)
                            print(
                                f"  {YELLOW}⚠ {rel_path}:{lineno} - {line.strip()[:60]}{RESET}"
                            )
        except Exception:
            pass

    if todo_count == 0:
        print(f"  {GREEN}✓ 未发现TODO/FIXME注释{RESET}")
    else:
        print(f"  {YELLOW}⚠ 共发现 {todo_count} 个TODO/FIXME注释{RESET}")

    return todo_count


async def check_core_modules():
    """检查核心模块导入"""
    print(f"\n{BLUE}[10] 核心模块导入检查{RESET}")
    core_modules = [
        ("config", True),  # 允许BOT_TOKEN未设置错误
        ("constants", False),
        ("decorators", False),
        ("init_db", False),
        ("db.base", False),
        ("utils.date_helpers", False),
        ("utils.amount_helpers", False),
        ("utils.order_helpers", False),
        ("utils.chat_helpers", False),
    ]

    errors = []
    for module, allow_config_error in core_modules:
        success, error = check_import(module)
        if success:
            print(f"  {GREEN}✓ {module}{RESET}")
        elif allow_config_error and "BOT_TOKEN" in error:
            print(f"  {YELLOW}⚠ {module}: 需要配置BOT_TOKEN（正常）{RESET}")
        else:
            print(f"  {RED}✗ {module}: {error}{RESET}")
            errors.append(f"{module}: {error}")

    return len(errors) == 0


def check_file_syntax():
    """检查文件语法"""
    print(f"\n{BLUE}[11] 文件语法检查{RESET}")
    python_files = list(project_root.rglob("*.py"))
    python_files = [f for f in python_files if "__pycache__" not in str(f)]

    syntax_errors = 0
    for file_path in python_files:
        success, error = check_syntax(file_path)
        if not success:
            rel_path = file_path.relative_to(project_root)
            print(f"  {RED}✗ {rel_path}: {error}{RESET}")
            syntax_errors += 1

    if syntax_errors == 0:
        print(f"  {GREEN}✓ 所有文件语法正确 ({len(python_files)} 个文件){RESET}")
    else:
        print(f"  {RED}✗ 发现 {syntax_errors} 个语法错误{RESET}")

    return syntax_errors == 0


def generate_quality_report() -> dict:
    """生成质量报告"""
    print("=" * 70)
    print("开始代码质量检查...")
    print("=" * 70)

    results = {
        "formatting": check_code_formatting(),
        "import_sorting": check_import_sorting(),
        "type_hints": check_type_hints(),
        "code_quality": check_code_quality(),
        "security": check_security(),
        "test_coverage": check_test_coverage(),
    }

    # 额外的检查
    duplicate_count = check_duplicate_functions()
    unused_imports = check_unused_imports()
    todo_count = check_todo_comments()

    # 异步检查
    asyncio.run(check_core_modules())
    syntax_ok = check_file_syntax()

    print("\n" + "=" * 70)
    print("质量检查结果汇总")
    print("=" * 70)

    for name, result in results.items():
        status = "✅" if result["success"] else "❌"
        tool = result.get("tool", name)
        print(f"{status} {tool}: ", end="")

        if "coverage" in result:
            print(f"覆盖率 {result['coverage']:.2f}%")
        elif not result.get("available", True):
            print("工具未安装")
        else:
            print("通过" if result["success"] else "失败")

    print(f"\n重复函数: {duplicate_count}")
    print(f"未使用导入: {unused_imports}")
    print(f"TODO/FIXME注释: {todo_count}")
    print(f"文件语法: {'通过' if syntax_ok else '失败'}")

    # 添加额外指标到结果字典
    results["duplicate_functions"] = duplicate_count
    results["unused_imports"] = unused_imports
    results["todo_comments"] = todo_count
    results["syntax_ok"] = syntax_ok

    return results


def main():
    """主函数"""
    results = generate_quality_report()

    # 检查是否有失败的检查
    failed_checks = [
        name
        for name, result in results.items()
        if isinstance(result, dict)
        and not result.get("success", True)
        and result.get("available", True)
    ]

    if failed_checks:
        print(f"\n⚠️ 以下检查失败: {', '.join(failed_checks)}")
        sys.exit(1)
    else:
        print("\n✅ 所有质量检查完成")
        sys.exit(0)


if __name__ == "__main__":
    main()
