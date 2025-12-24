@echo off
REM 检测未使用的代码（死代码检测）
echo ========================================
echo 检测未使用的代码
echo ========================================
echo.

echo [1/2] 安装 vulture（如果未安装）...
pip install vulture --quiet

echo.
echo [2/2] 运行死代码检测...
echo.

vulture . --min-confidence 80 --exclude venv,.venv,__pycache__,*.pyc,code-quality-template

echo.
echo ========================================
echo 检测完成！
echo ========================================
echo.
echo 说明：
echo - 高置信度（80%%以上）的结果通常是真正的死代码
echo - 低置信度可能是误报，需要人工检查
echo - 建议先处理高置信度的结果
echo.
pause

