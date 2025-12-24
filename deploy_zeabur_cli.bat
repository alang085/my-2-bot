@echo off
REM Zeabur CLI 快速部署脚本 (Windows)
REM 使用 Zeabur CLI 直接部署，无需 Git 推送

echo ==========================================
echo Zeabur CLI 快速部署
echo ==========================================
echo.

REM 检查 Node.js 是否安装（支持多种路径）
set NODE_PATH=
if exist "C:\Program Files\nodejs\node.exe" (
    set "NODE_PATH=C:\Program Files\nodejs"
    goto :node_found
)
if exist "C:\Program Files (x86)\nodejs\node.exe" (
    set "NODE_PATH=C:\Program Files (x86)\nodejs"
    goto :node_found
)
where node >nul 2>&1
if %errorlevel% equ 0 (
    for /f "delims=" %%i in ('where node') do (
        set "NODE_FULL_PATH=%%i"
        for %%j in ("%%~dpi.") do set "NODE_PATH=%%~fj"
        goto :node_found
    )
)

:node_not_found
echo [ERROR] Node.js not detected
echo.
echo Please install Node.js first:
echo   1. Visit https://nodejs.org/
echo   2. Download and install LTS version
echo   3. Run this script again
echo.
pause
exit /b 1

:node_found
REM 设置 PATH 包含 Node.js 路径
set "PATH=%NODE_PATH%;%PATH%"

echo [OK] Node.js is installed
for /f "delims=" %%i in ('"%NODE_PATH%\node.exe" --version') do set node_version=%%i
echo    Version: %node_version%
echo.

REM Check required files
echo Checking required files...
if not exist "main.py" (
    echo [ERROR] Missing required file: main.py
    pause
    exit /b 1
)
if not exist "requirements.txt" (
    echo [ERROR] Missing required file: requirements.txt
    pause
    exit /b 1
)
if not exist "Dockerfile" (
    echo [ERROR] Missing required file: Dockerfile
    pause
    exit /b 1
)
if not exist "zeabur.json" (
    echo [ERROR] Missing required file: zeabur.json
    pause
    exit /b 1
)
echo [OK] Required files check passed
echo.

REM 检查是否已登录
echo Checking Zeabur login status...
"%NODE_PATH%\npx.cmd" --yes zeabur@latest auth whoami >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Not logged in to Zeabur
    echo.
    echo Opening browser for login...
    echo Please follow the browser prompts to complete login
    echo.
    "%NODE_PATH%\npx.cmd" --yes zeabur@latest auth login
    if %errorlevel% neq 0 (
        echo [ERROR] Login failed, please try again
        pause
        exit /b 1
    )
    echo [OK] Login successful
) else (
    echo [OK] Already logged in to Zeabur
)
echo.

REM 显示当前配置
echo Current deployment configuration:
echo   - Start command: python main.py
echo   - Builder: DOCKER
echo   - Restart policy: ON_FAILURE (max 10 times)
echo.

REM 确认部署
set /p confirm="Start deployment? (y/n): "
if /i not "%confirm%"=="y" (
    echo Deployment cancelled
    pause
    exit /b 0
)

echo.
echo ==========================================
echo Starting deployment...
echo ==========================================
echo.

REM 执行部署
"%NODE_PATH%\npx.cmd" --yes zeabur@latest deploy

if %errorlevel% equ 0 (
    echo.
    echo ==========================================
    echo [OK] Deployment successful!
    echo ==========================================
    echo.
    echo Notes:
    echo   - Configure environment variables in Zeabur Dashboard
    echo   - Required: BOT_TOKEN, ADMIN_USER_IDS, DATA_DIR
    echo   - Add Volume (mount path: /data)
    echo.
) else (
    echo.
    echo ==========================================
    echo [ERROR] Deployment failed
    echo ==========================================
    echo.
    echo Please check:
    echo   1. Network connection
    echo   2. Zeabur account permissions
    echo   3. Error messages above
    echo.
)

pause

