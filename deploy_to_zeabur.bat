@echo off
REM Zeabur 部署脚本 (Windows)
REM 用于准备和推送代码到 Git 仓库，触发 Zeabur 自动部署

echo ==========================================
echo Zeabur 部署准备脚本
echo ==========================================
echo.

REM 检查 Git 是否初始化
if not exist ".git" (
    echo ⚠️  Git 未初始化，正在初始化...
    git init
    echo ✅ Git 初始化完成
)

REM 检查是否有未提交的更改
git status --porcelain >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  没有需要提交的更改
    set /p continue="是否继续？(y/n): "
    if /i not "%continue%"=="y" exit /b 0
)

REM 显示当前状态
echo.
echo 当前 Git 状态：
git status --short
echo.

REM 检查敏感文件
echo 检查敏感文件...
git ls-files config.py user_config.py loan_bot.db >nul 2>&1
if %errorlevel% equ 0 (
    echo ❌ 发现敏感文件在 Git 跟踪中！
    echo 请确保以下文件在 .gitignore 中：
    echo   - config.py
    echo   - user_config.py
    echo   - *.db
    echo   - temp/
    exit /b 1
)
echo ✅ 敏感文件检查通过

REM 检查必要的文件
echo.
echo 检查必要文件...
if not exist "main.py" (
    echo ❌ 缺少必要文件: main.py
    exit /b 1
)
if not exist "init_db.py" (
    echo ❌ 缺少必要文件: init_db.py
    exit /b 1
)
if not exist "requirements.txt" (
    echo ❌ 缺少必要文件: requirements.txt
    exit /b 1
)
if not exist "Procfile" (
    echo ❌ 缺少必要文件: Procfile
    exit /b 1
)
if not exist "Dockerfile" (
    echo ❌ 缺少必要文件: Dockerfile
    exit /b 1
)
echo ✅ 必要文件检查通过

REM 询问提交信息
echo.
set /p commit_msg="请输入提交信息 (默认: Update code for Zeabur deployment): "
if "%commit_msg%"=="" set commit_msg=Update code for Zeabur deployment

REM 添加所有更改
echo.
echo 添加文件到 Git...
git add .
echo ✅ 文件已添加

REM 提交更改
echo.
echo 提交更改...
git commit -m "%commit_msg%"
echo ✅ 更改已提交

REM 检查远程仓库
echo.
git remote | findstr /C:"origin" >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('git remote get-url origin') do set remote_url=%%i
    echo 远程仓库: %remote_url%
    set /p push="是否推送到远程仓库？(y/n): "
    if /i "%push%"=="y" (
        echo.
        echo 推送到远程仓库...
        for /f "tokens=*" %%i in ('git branch --show-current') do set branch=%%i
        git push origin %branch%
        echo ✅ 代码已推送到远程仓库
        echo.
        echo ==========================================
        echo ✅ 部署准备完成！
        echo ==========================================
        echo.
        echo Zeabur 会自动检测代码更新并重新部署。
        echo 请在 Zeabur Dashboard 查看部署状态。
    )
) else (
    echo ⚠️  未配置远程仓库
    echo.
    set /p add_remote="是否添加远程仓库？(y/n): "
    if /i "%add_remote%"=="y" (
        set /p remote_url="请输入远程仓库地址: "
        git remote add origin %remote_url%
        echo ✅ 远程仓库已添加
        echo.
        set /p push_now="是否立即推送？(y/n): "
        if /i "%push_now%"=="y" (
            for /f "tokens=*" %%i in ('git branch --show-current') do set branch=%%i
            git push -u origin %branch%
            echo ✅ 代码已推送到远程仓库
        )
    )
)

echo.
echo ==========================================
echo 完成！
echo ==========================================
pause

