@echo off
:: WiFi专业工具 无控制台启动器
:: 使用 pythonw.exe 运行，不显示命令行窗口

:: ── 管理员权限检查与自动提权 ──────────────────────────────
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -WindowStyle Hidden -Command "Start-Process -FilePath '%~f0' -Verb RunAs -WindowStyle Hidden"
    exit /b
)

:: ── 查找 pythonw.exe（优先注册表，兼容所有安装路径）────────
set "PYDIR="
for /f "tokens=2*" %%a in ('reg query "HKLM\SOFTWARE\Python\PythonCore\3.11\InstallPath" /ve 2^>nul') do set "PYDIR=%%b"
if not defined PYDIR (
    for /f "tokens=2*" %%a in ('reg query "HKCU\SOFTWARE\Python\PythonCore\3.11\InstallPath" /ve 2^>nul') do set "PYDIR=%%b"
)
if not defined PYDIR (
    for /f "delims=" %%i in ('where pythonw.exe 2^>nul') do if not defined PYDIR set "PYDIR=%%~dpi"
)

:: ── 无控制台窗口启动主程序 ────────────────────────────────
if defined PYDIR (
    start "" "%PYDIR%pythonw.exe" "%~dp0wifi_professional.py"
) else (
    start "" pythonw.exe "%~dp0wifi_professional.py"
)
exit
