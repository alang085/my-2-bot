@echo off
REM 一次性脚本：将2025-12-22的统计数据（除了延续性数据）全部归零
REM 执行方式：双击此文件或在命令行中运行

echo ========================================
echo 数据重置脚本
echo 目标日期: 2025-12-22
echo ========================================
echo.

REM 切换到脚本所在目录
cd /d "%~dp0\.."

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

REM 执行Python脚本
python scripts\reset_daily_data_2025_12_22.py

if errorlevel 1 (
    echo.
    echo 错误: 脚本执行失败
    pause
    exit /b 1
) else (
    echo.
    echo 脚本执行完成
    pause
)

