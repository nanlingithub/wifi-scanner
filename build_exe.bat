@echo off
chcp 65001 > nul
REM ==================================================
REM WiFi专业工具 - 打包脚本
REM 将Python程序打包为独立的exe可执行文件
REM ==================================================

echo ========================================
echo WiFi专业工具 - EXE打包工具 v1.6.3
echo ========================================
echo.

REM 检查Python环境
echo [1/6] 检查Python环境...
py --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python环境！
    echo 请确保已安装Python 3.11+
    pause
    exit /b 1
)
py --version
echo ✅ Python环境检查通过
echo.

REM 检查并安装PyInstaller
echo [2/6] 检查PyInstaller...
py -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo PyInstaller未安装，正在安装...
    py -m pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple
    if errorlevel 1 (
        echo ❌ PyInstaller安装失败！
        pause
        exit /b 1
    )
)
echo ✅ PyInstaller已就绪
echo.

REM 清理旧的构建文件
echo [3/6] 清理旧的构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo ✅ 清理完成
echo.

REM 执行打包
echo [4/6] 开始打包程序...
echo 这可能需要几分钟时间，请耐心等待...
echo.
py -m PyInstaller wifi_professional.spec --clean
if errorlevel 1 (
    echo.
    echo ❌ 打包失败！
    echo 请检查错误信息并重试。
    pause
    exit /b 1
)
echo.
echo ✅ 打包完成
echo.

REM 复制必要文件到dist目录
echo [5/6] 复制配置文件...
if exist config.json (
    copy /y config.json "dist\WiFi专业工具\"
    echo ✅ 已复制 config.json
)
if exist signal_history.json (
    copy /y signal_history.json "dist\WiFi专业工具\"
    echo ✅ 已复制 signal_history.json
)
if exist README.md (
    copy /y README.md "dist\WiFi专业工具\"
    echo ✅ 已复制 README.md
)
echo.

REM 创建快捷启动脚本
echo [6/6] 创建启动脚本...
(
echo @echo off
echo chcp 65001 ^> nul
echo start "" "WiFi专业工具.exe"
) > "dist\WiFi专业工具\启动WiFi专业工具.bat"
echo ✅ 已创建启动脚本
echo.

REM 显示结果
echo ========================================
echo 🎉 打包成功！
echo ========================================
echo.
echo 打包文件位置：
echo   %CD%\dist\WiFi专业工具\
echo.
echo 主程序：
echo   WiFi专业工具.exe
echo.
echo 可执行文件大小：
for %%A in ("dist\WiFi专业工具\WiFi专业工具.exe") do echo   %%~zA 字节 (约 %%~zA /1024/1024 MB)
echo.
echo ========================================
echo 使用说明：
echo ========================================
echo 1. 进入 dist\WiFi专业工具\ 目录
echo 2. 双击 WiFi专业工具.exe 或 启动WiFi专业工具.bat
echo 3. 程序将自动启动，无需Python环境
echo.
echo 注意：首次运行可能需要Windows防火墙授权
echo ========================================
echo.

REM 询问是否立即测试
set /p test="是否立即测试运行打包的程序？(Y/N): "
if /i "%test%"=="Y" (
    echo.
    echo 正在启动程序...
    cd "dist\WiFi专业工具"
    start "" "WiFi专业工具.exe"
    cd ..\..
)

echo.
echo 按任意键退出...
pause > nul
