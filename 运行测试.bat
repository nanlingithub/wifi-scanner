@echo off
chcp 65001 >nul
REM WiFi专业工具 - 自动化测试启动脚本
REM 版本: 1.0

echo.
echo ============================================================
echo   WiFi专业工具 - 自动化测试系统
echo ============================================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

REM 显示菜单
:MENU
echo.
echo 请选择测试模式:
echo.
echo   [1] 运行所有测试 (推荐)
echo   [2] 快速测试 (跳过慢速测试)
echo   [3] 仅生成覆盖率报告
echo   [4] CI模式 (完整测试+报告)
echo   [5] 显示测试摘要
echo   [6] 列出所有测试
echo   [7] 重新运行失败的测试
echo   [8] 自定义命令
echo   [0] 退出
echo.

set /p choice="请输入选项 (0-8): "

if "%choice%"=="1" goto ALL_TESTS
if "%choice%"=="2" goto QUICK_TESTS
if "%choice%"=="3" goto COVERAGE
if "%choice%"=="4" goto CI_MODE
if "%choice%"=="5" goto SUMMARY
if "%choice%"=="6" goto LIST_TESTS
if "%choice%"=="7" goto FAILED_TESTS
if "%choice%"=="8" goto CUSTOM
if "%choice%"=="0" goto END

echo [错误] 无效选项，请重新选择
goto MENU

:ALL_TESTS
echo.
echo [信息] 正在运行所有测试...
python run_tests.py
goto RESULT

:QUICK_TESTS
echo.
echo [信息] 正在运行快速测试...
python run_tests.py --quick
goto RESULT

:COVERAGE
echo.
echo [信息] 正在生成覆盖率报告...
python run_tests.py --coverage-only
goto RESULT

:CI_MODE
echo.
echo [信息] 正在运行CI模式...
python run_tests.py --ci
goto RESULT

:SUMMARY
echo.
python run_tests.py --summary
pause
goto MENU

:LIST_TESTS
echo.
python run_tests.py --list
pause
goto MENU

:FAILED_TESTS
echo.
echo [信息] 重新运行失败的测试...
python run_tests.py --failed
goto RESULT

:CUSTOM
echo.
echo 可用参数:
echo   --quick           快速测试
echo   --marker [name]   按标记运行 (integration, performance, slow, admin_required)
echo   --file [name]     运行特定文件
echo   --no-coverage     不生成覆盖率
echo   --no-html         不生成HTML报告
echo.
set /p custom_args="请输入pytest参数: "
python run_tests.py %custom_args%
goto RESULT

:RESULT
echo.
if errorlevel 1 (
    echo.
    echo [失败] 测试未通过，请检查错误信息
) else (
    echo.
    echo [成功] 测试通过 ✓
)
echo.

set /p continue="是否继续测试? (Y/N): "
if /i "%continue%"=="Y" goto MENU
if /i "%continue%"=="y" goto MENU

:END
echo.
echo 感谢使用WiFi专业工具测试系统！
echo.
pause
