@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

echo ========================================
echo Cleanup Unused Files
echo ========================================
echo.

REM 1. 删除重复的部署脚本（保留最新的）
echo [1/4] Removing duplicate deployment scripts...
if exist deploy_zeabur_cli_fixed.bat (
    echo   Deleting deploy_zeabur_cli_fixed.bat (duplicate)
    del /f /q deploy_zeabur_cli_fixed.bat
)
if exist deploy_to_zeabur.bat (
    echo   Deleting deploy_to_zeabur.bat (replaced by deploy_zeabur_cli.bat)
    del /f /q deploy_to_zeabur.bat
)
if exist deploy_to_zeabur.sh (
    echo   Deleting deploy_to_zeabur.sh (replaced by deploy_zeabur_cli.sh)
    del /f /q deploy_to_zeabur.sh
)
echo [OK] Duplicate deployment scripts removed
echo.

REM 2. 删除临时优化脚本（已经完成优化）
echo [2/4] Removing temporary optimization scripts...
if exist fix_imports.bat (
    echo   Deleting fix_imports.bat (optimization completed)
    del /f /q fix_imports.bat
)
if exist optimize_code.bat (
    echo   Deleting optimize_code.bat (optimization completed)
    del /f /q optimize_code.bat
)
echo [OK] Temporary scripts removed
echo.

REM 3. 删除已安装工具的安装脚本
echo [3/4] Removing tool installation scripts...
if exist install_code_quality_tools.bat (
    echo   Deleting install_code_quality_tools.bat (tools already installed)
    del /f /q install_code_quality_tools.bat
)
if exist install_code_quality_tools.sh (
    echo   Deleting install_code_quality_tools.sh (tools already installed)
    del /f /q install_code_quality_tools.sh
)
echo [OK] Installation scripts removed
echo.

REM 4. 检查并删除未使用的测试文件
echo [4/4] Checking for unused test files...
if exist full_test.bat (
    echo   Keeping full_test.bat (may be used)
)
if exist local_test.bat (
    echo   Keeping local_test.bat (may be used)
)
echo [OK] Test files checked
echo.

echo ========================================
echo Cleanup completed!
echo ========================================
echo.
echo Removed files:
echo   - Duplicate deployment scripts
echo   - Temporary optimization scripts
echo   - Tool installation scripts
echo.
echo Next steps:
echo   1. Review changes: git status
echo   2. Commit if satisfied: git add -A && git commit -m "Cleanup: remove unused scripts and files"
echo.
pause

