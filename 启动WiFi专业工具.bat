@echo off
chcp 65001 >nul
title WiFi专业工具 - 启动器

echo.
echo ========================================
echo   WiFi专业工具 v1.6.3 (EXE版)
echo   Developer: NL@China_SZ
echo ========================================
echo.

REM 检查管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  需要管理员权限！
    echo.
    echo 正在请求管理员权限...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit
)

echo ✅ 管理员权限已获取
echo.
echo 🚀 正在启动WiFi专业工具...
echo.

REM 进入程序目录
cd /d "%~dp0dist\WiFi专业工具"

REM 检查程序是否存在
if not exist "WiFi专业工具.exe" (
    echo ❌ 错误: 找不到 WiFi专业工具.exe
    echo.
    echo 请确保以下文件存在:
    echo   dist\WiFi专业工具\WiFi专业工具.exe
    echo.
    pause
    exit /b 1
)

REM 启动程序
start "" "WiFi专业工具.exe"

REM 等待2秒后关闭启动器
timeout /t 2 >nul

exit 
