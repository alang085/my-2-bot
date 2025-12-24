@echo off
REM Windows Service 安装脚本（使用 NSSM）
REM 需要先安装 NSSM: https://nssm.cc/download

echo ==========================================
echo 安装 Loan Bot Windows Service
echo ==========================================
echo.

REM 检查 NSSM 是否安装
where nssm >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [错误] NSSM 未安装或不在 PATH 中
    echo.
    echo 请先安装 NSSM:
    echo 1. 下载: https://nssm.cc/download
    echo 2. 解压到 C:\nssm
    echo 3. 将 C:\nssm\win64 添加到 PATH 环境变量
    echo.
    pause
    exit /b 1
)

REM 获取脚本所在目录
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

REM 设置服务名称
set SERVICE_NAME=LoanBot

echo [信息] 服务名称: %SERVICE_NAME%
echo [信息] 项目路径: %PROJECT_ROOT%
echo.

REM 检查服务是否已存在
nssm status %SERVICE_NAME% >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [警告] 服务已存在
    echo.
    set /p CONFIRM="是否删除现有服务并重新安装? (Y/N): "
    if /i "%CONFIRM%" NEQ "Y" (
        echo 取消安装
        pause
        exit /b 0
    )
    echo [信息] 停止并删除现有服务...
    nssm stop %SERVICE_NAME%
    nssm remove %SERVICE_NAME% confirm
    timeout /t 2 >nul
)

echo [信息] 安装服务...
nssm install %SERVICE_NAME% python "%PROJECT_ROOT%\main.py"

echo [信息] 配置服务参数...
nssm set %SERVICE_NAME% AppDirectory "%PROJECT_ROOT%"
nssm set %SERVICE_NAME% AppStdout "%PROJECT_ROOT%\logs\loan-bot.log"
nssm set %SERVICE_NAME% AppStderr "%PROJECT_ROOT%\logs\loan-bot-error.log"
nssm set %SERVICE_NAME% AppRotateFiles 1
nssm set %SERVICE_NAME% AppRotateOnline 1
nssm set %SERVICE_NAME% AppRotateSeconds 86400
nssm set %SERVICE_NAME% AppRotateBytes 10485760

echo [信息] 设置启动类型为自动...
nssm set %SERVICE_NAME% Start SERVICE_AUTO_START

echo.
echo ==========================================
echo 服务安装完成！
echo ==========================================
echo.
echo 请设置环境变量（在系统环境变量中设置）:
echo   BOT_TOKEN=your_bot_token_here
echo   ADMIN_USER_IDS=your_admin_ids_here
echo   DATA_DIR=C:\data
echo   DEBUG=0
echo.
echo 常用命令:
echo   启动服务:   nssm start %SERVICE_NAME%
echo   停止服务:   nssm stop %SERVICE_NAME%
echo   重启服务:   nssm restart %SERVICE_NAME%
echo   查看状态:   nssm status %SERVICE_NAME%
echo   查看日志:   type "%PROJECT_ROOT%\logs\loan-bot.log"
echo.
echo 或使用 Windows 服务管理器:
echo   services.msc
echo.
pause

