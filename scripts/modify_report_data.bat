@echo off
REM Windows 批处理脚本 - 直接修改运行服务上的报表数据

echo ==========================================
echo 修改报表数据工具
echo ==========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 未安装或未添加到 PATH
    echo 请先安装 Python 3.6+
    pause
    exit /b 1
)

REM 显示使用说明
if "%1"=="" (
    echo 使用方法:
    echo   modify_report_data.bat --type financial --field liquid_funds --value 100000 --mode set
    echo   modify_report_data.bat --type grouped --group_id S01 --field interest --value 5000 --mode add
    echo   modify_report_data.bat --type daily --date 2025-01-15 --field interest --value 1000 --mode set
    echo.
    echo 查看数据:
    echo   modify_report_data.bat --type financial --show
    echo   modify_report_data.bat --type grouped --group_id S01 --show
    echo   modify_report_data.bat --type daily --date 2025-01-15 --show
    echo.
    pause
    exit /b 0
)

REM 执行 Python 脚本
python scripts\modify_report_data.py %*

pause





