@echo off
chcp 65001 >nul
echo ================================
echo WiFi专业工具 - 图标转换脚本
echo ================================
echo.

REM 检查是否存在图片文件
if not exist "wifi_icon.png" (
    echo [错误] 未找到 wifi_icon.png 文件
    echo 请将WiFi图标图片保存为 wifi_icon.png 放在当前目录
    echo.
    pause
    exit /b 1
)

echo [1/2] 正在转换图片为ICO格式...
py convert_icon.py wifi_icon.png wifi_icon.ico

if %errorlevel% neq 0 (
    echo [错误] 图标转换失败
    pause
    exit /b 1
)

echo.
echo [2/2] 验证ICO文件...
if exist "wifi_icon.ico" (
    echo ✅ 图标文件创建成功: wifi_icon.ico
    echo.
    echo 文件位置: %cd%\wifi_icon.ico
    echo.
    echo 下一步：重新运行 build_exe.bat 打包程序
) else (
    echo ❌ ICO文件未生成
)

echo.
pause
