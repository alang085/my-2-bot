@echo off
REM 本地测试和细微级别检查脚本 (Windows)
echo ==========================================
echo 本地测试和细微级别检查
echo ==========================================
echo.

REM 检查Python版本
echo [1/10] 检查Python版本...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python未安装或不在PATH中
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do set py_version=%%i
echo ✅ %py_version%
echo.

REM 检查Python版本是否符合要求（3.9+）
python -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  警告: Python版本可能过低，建议使用3.9+
)
echo.

REM 检查必要文件
echo [2/10] 检查必要文件...
set missing_files=0
if not exist "main.py" (
    echo ❌ 缺少: main.py
    set /a missing_files+=1
)
if not exist "requirements.txt" (
    echo ❌ 缺少: requirements.txt
    set /a missing_files+=1
)
if not exist "init_db.py" (
    echo ❌ 缺少: init_db.py
    set /a missing_files+=1
)
if not exist "config.py" (
    echo ❌ 缺少: config.py
    set /a missing_files+=1
)
if %missing_files% equ 0 (
    echo ✅ 所有必要文件存在
) else (
    echo ❌ 缺少 %missing_files% 个必要文件
    pause
    exit /b 1
)
echo.

REM 检查配置文件
echo [3/10] 检查配置文件...
if exist "user_config.py" (
    echo ✅ user_config.py 存在
) else (
    echo ⚠️  user_config.py 不存在，将使用环境变量
    if "%BOT_TOKEN%"=="" (
        echo ❌ 环境变量 BOT_TOKEN 未设置
        echo    请创建 user_config.py 或设置环境变量
        pause
        exit /b 1
    )
)
echo.

REM 检查依赖安装
echo [4/10] 检查Python依赖...
python -c "import telegram" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  依赖未安装，正在安装...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
    echo ✅ 依赖安装完成
) else (
    echo ✅ 依赖已安装
)
echo.

REM 检查代码语法
echo [5/10] 检查代码语法...
python -m py_compile main.py >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ main.py 语法错误
    python -m py_compile main.py
    pause
    exit /b 1
)
echo ✅ main.py 语法正确
echo.

REM 检查数据库初始化
echo [6/10] 检查数据库初始化...
python -c "import init_db; init_db.init_database()" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  数据库初始化可能有问题，但继续测试...
) else (
    echo ✅ 数据库初始化成功
)
echo.

REM 检查导入
echo [7/10] 检查模块导入...
python -c "import sys; sys.path.insert(0, '.'); import config; import db_operations; import handlers; import callbacks; import utils" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 模块导入失败
    python -c "import sys; sys.path.insert(0, '.'); import config; import db_operations; import handlers; import callbacks; import utils"
    pause
    exit /b 1
)
echo ✅ 所有模块导入成功
echo.

REM 检查配置加载
echo [8/10] 检查配置加载...
python -c "import sys; sys.path.insert(0, '.'); from config import load_config; load_config()" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 配置加载失败
    echo    请检查 BOT_TOKEN 和 ADMIN_USER_IDS 是否设置
    python -c "import sys; sys.path.insert(0, '.'); from config import load_config; load_config()"
    pause
    exit /b 1
)
echo ✅ 配置加载成功
echo.

REM 检查数据库连接
echo [9/10] 检查数据库连接...
python -c "import sys; sys.path.insert(0, '.'); import db_operations; import asyncio; asyncio.run(db_operations.get_financial_data())" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  数据库连接可能有问题，但继续测试...
) else (
    echo ✅ 数据库连接正常
)
echo.

REM 检查代码质量（如果安装了工具）
echo [10/10] 检查代码质量...
python -m flake8 --version >nul 2>&1
if %errorlevel% equ 0 (
    echo 运行 flake8 检查...
    python -m flake8 --max-line-length=100 --ignore=E203,E501,W503 main.py config.py init_db.py 2>nul
    echo ✅ 代码质量检查完成
) else (
    echo ⚠️  flake8 未安装，跳过代码质量检查
    echo    安装命令: pip install flake8
)
echo.

echo ==========================================
echo ✅ 所有检查完成！
echo ==========================================
echo.
echo 下一步:
echo   1. 确保已设置 BOT_TOKEN 和 ADMIN_USER_IDS
echo   2. 运行: python main.py
echo   3. 在Telegram中测试机器人功能
echo.
pause

