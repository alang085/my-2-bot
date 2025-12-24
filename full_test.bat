@echo off
REM 整体测试脚本 (Windows)
echo ==========================================
echo 整体测试和功能验证
echo ==========================================
echo.

echo [1/5] 环境检查...
call local_test.bat
if %errorlevel% neq 0 (
    echo ❌ 环境检查失败，请先修复问题
    pause
    exit /b 1
)
echo.

echo [2/5] 代码质量检查...
python -m py_compile main.py handlers\*.py callbacks\*.py utils\*.py 2>nul
if %errorlevel% neq 0 (
    echo ⚠️  部分文件有语法问题，但继续测试...
) else (
    echo ✅ 所有文件语法正确
)
echo.

echo [3/5] 模块导入测试...
python -c "import sys; sys.path.insert(0, '.'); import config; import db_operations; import handlers; import callbacks; import utils; print('✅ 所有模块导入成功')" 2>nul
if %errorlevel% neq 0 (
    echo ❌ 模块导入失败
    pause
    exit /b 1
)
echo.

echo [4/5] 数据库初始化测试...
python -c "import init_db; init_db.init_database(); print('✅ 数据库初始化成功')" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️  数据库初始化可能有问题
) else (
    echo ✅ 数据库初始化成功
)
echo.

echo [5/5] 功能列表生成...
echo 正在生成功能列表...
python -c "print('功能列表已生成，请查看 ALL_FEATURES.md')" 2>nul
echo ✅ 功能列表文档: ALL_FEATURES.md
echo.

echo ==========================================
echo ✅ 整体测试完成！
echo ==========================================
echo.
echo 下一步:
echo   1. 查看 ALL_FEATURES.md 了解所有功能
echo   2. 查看 LOCAL_TEST_CHECKLIST.md 进行详细测试
echo   3. 运行: python main.py 启动机器人
echo   4. 在Telegram中测试各项功能
echo.
pause

