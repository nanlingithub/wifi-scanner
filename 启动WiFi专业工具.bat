@echo off
chcp 65001 >nul
echo ========================================
echo WiFi专业工具 v2.2
echo ========================================
echo.
cd /d %~dp0
echo 当前目录: %CD%
echo 正在启动...
echo.
py wifi_professional.py
if errorlevel 1 (
    echo.
    echo [错误] 启动失败，请检查Python环境
    pause
) else (
    echo.
    echo 程序已关闭
) 
