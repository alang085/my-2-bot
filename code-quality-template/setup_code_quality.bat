@echo off
REM 代码质量工具快速设置脚本 (Windows)
REM 自动检测项目结构并生成配置文件

echo ========================================
echo 代码质量工具快速设置
echo ========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 未检测到 Python
    echo 请先安装 Python 3.9 或更高版本
    pause
    exit /b 1
)

echo [OK] Python 已安装
python --version
echo.

REM 检查是否在项目根目录
if not exist "requirements.txt" (
    echo [WARNING] 未找到 requirements.txt
    echo 请确保在项目根目录运行此脚本
    echo.
)

REM 复制模板文件
echo [1/4] 复制配置文件模板...
if not exist "pyproject.toml" (
    copy "code-quality-template\pyproject.toml.template" "pyproject.toml" >nul
    echo   [OK] 已创建 pyproject.toml
) else (
    echo   [SKIP] pyproject.toml 已存在
)

if not exist "requirements-dev.txt" (
    copy "code-quality-template\requirements-dev.txt.template" "requirements-dev.txt" >nul
    echo   [OK] 已创建 requirements-dev.txt
) else (
    echo   [SKIP] requirements-dev.txt 已存在
)

if not exist "check_code_quality.bat" (
    copy "code-quality-template\check_code_quality.bat.template" "check_code_quality.bat" >nul
    echo   [OK] 已创建 check_code_quality.bat
) else (
    echo   [SKIP] check_code_quality.bat 已存在
)

echo.
echo [2/4] 安装开发工具依赖...
pip install -r requirements-dev.txt

echo.
echo [3/4] 检测项目结构...
echo   正在分析项目结构...

REM 检测 Python 模块目录
set MODULES=
if exist "src\" (
    set MODULES=src
) else if exist "app\" (
    set MODULES=app
) else (
    REM 查找包含 __init__.py 的目录
    for /d %%d in (*) do (
        if exist "%%d\__init__.py" (
            if defined MODULES (
                set MODULES=!MODULES! %%d
            ) else (
                set MODULES=%%d
            )
        )
    )
)

if defined MODULES (
    echo   [OK] 检测到模块: %MODULES%
    echo.
    echo   [提示] 请在 pyproject.toml 中更新 known_first_party 配置
    echo   当前检测到的模块: %MODULES%
) else (
    echo   [INFO] 未检测到标准模块结构，将使用默认配置
)

echo.
echo [4/4] 完成设置！
echo.
echo ========================================
echo 下一步操作：
echo ========================================
echo.
echo 1. 编辑 pyproject.toml，修改以下配置：
echo    - known_first_party: 你的项目模块名
echo    - mypy.overrides: 你的第三方库
echo.
echo 2. 编辑 check_code_quality.bat，修改 pylint 检查路径
echo.
echo 3. 运行检查: check_code_quality.bat
echo.
pause

