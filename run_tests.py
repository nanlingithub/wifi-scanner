#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WiFi专业工具 - 自动化测试运行器
v1.0 - 2026年2月5日

功能：
- 🧪 运行所有单元测试
- 📊 生成覆盖率报告
- 🎯 支持选择性测试（按标记筛选）
- 📝 生成HTML测试报告
- 🚀 持续集成模式
- ⚡ 快速测试模式（跳过慢速测试）
"""

import sys
import os
import argparse
import subprocess
import time
from pathlib import Path
from datetime import datetime

# ANSI颜色代码
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


class TestRunner:
    """自动化测试运行器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.tests_dir = self.project_root / "tests"
        self.reports_dir = self.project_root / "test_reports"
        self.coverage_dir = self.reports_dir / "coverage"
        
    def print_header(self, text: str):
        """打印标题"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{text.center(70)}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 70}{Colors.RESET}\n")
    
    def print_success(self, text: str):
        """打印成功消息"""
        print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")
    
    def print_error(self, text: str):
        """打印错误消息"""
        print(f"{Colors.RED}❌ {text}{Colors.RESET}")
    
    def print_warning(self, text: str):
        """打印警告消息"""
        print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")
    
    def print_info(self, text: str):
        """打印信息消息"""
        print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")
    
    def setup_environment(self):
        """设置测试环境"""
        self.print_info("正在设置测试环境...")
        
        # 创建报告目录
        self.reports_dir.mkdir(exist_ok=True)
        self.coverage_dir.mkdir(exist_ok=True)
        
        # 添加项目根目录到Python路径
        sys.path.insert(0, str(self.project_root))
        
        self.print_success("测试环境设置完成")
    
    def check_dependencies(self) -> bool:
        """检查测试依赖"""
        self.print_info("正在检查测试依赖...")
        
        required_packages = ['pytest', 'pytest-cov', 'pytest-html']
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            self.print_error(f"缺少依赖包: {', '.join(missing_packages)}")
            self.print_info(f"请运行: pip install {' '.join(missing_packages)}")
            return False
        
        self.print_success("所有依赖已安装")
        return True
    
    def run_pytest(self, args: list) -> int:
        """运行pytest"""
        cmd = [sys.executable, "-m", "pytest"] + args
        
        self.print_info(f"执行命令: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, cwd=self.project_root)
        return result.returncode
    
    def run_all_tests(self, verbose: bool = True, coverage: bool = True, html_report: bool = True):
        """运行所有测试"""
        self.print_header("运行所有测试")
        
        args = []
        
        # 详细输出
        if verbose:
            args.append("-v")
        
        # 覆盖率
        if coverage:
            args.extend([
                "--cov=core",
                "--cov=wifi_modules",
                "--cov-report=term-missing",
                f"--cov-report=html:{self.coverage_dir}",
                "--cov-report=xml"
            ])
        
        # HTML报告
        if html_report:
            report_path = self.reports_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            args.extend([
                f"--html={report_path}",
                "--self-contained-html"
            ])
        
        start_time = time.time()
        returncode = self.run_pytest(args)
        elapsed_time = time.time() - start_time
        
        print(f"\n{Colors.BOLD}测试耗时: {elapsed_time:.2f}秒{Colors.RESET}\n")
        
        if returncode == 0:
            self.print_success("所有测试通过 ✨")
        else:
            self.print_error(f"测试失败 (退出码: {returncode})")
        
        if coverage:
            self.print_info(f"覆盖率报告: {self.coverage_dir / 'index.html'}")
        
        return returncode
    
    def run_quick_tests(self):
        """快速测试（跳过慢速测试）"""
        self.print_header("快速测试模式")
        self.print_info("跳过标记为 'slow' 的测试")
        
        args = ["-v", "-m", "not slow"]
        
        start_time = time.time()
        returncode = self.run_pytest(args)
        elapsed_time = time.time() - start_time
        
        print(f"\n{Colors.BOLD}快速测试耗时: {elapsed_time:.2f}秒{Colors.RESET}\n")
        
        return returncode
    
    def run_by_marker(self, marker: str):
        """按标记运行测试"""
        self.print_header(f"运行标记为 '{marker}' 的测试")
        
        args = ["-v", "-m", marker]
        
        return self.run_pytest(args)
    
    def run_specific_test(self, test_path: str):
        """运行特定测试文件或测试函数"""
        self.print_header(f"运行测试: {test_path}")
        
        args = ["-v", test_path]
        
        return self.run_pytest(args)
    
    def run_failed_tests(self):
        """重新运行上次失败的测试"""
        self.print_header("重新运行失败的测试")
        
        args = ["-v", "--lf"]  # --lf = last failed
        
        return self.run_pytest(args)
    
    def run_coverage_only(self):
        """仅生成覆盖率报告（不运行测试）"""
        self.print_header("生成覆盖率报告")
        
        args = [
            "--cov=core",
            "--cov=wifi_modules",
            "--cov-report=term-missing",
            f"--cov-report=html:{self.coverage_dir}",
            "-v"
        ]
        
        returncode = self.run_pytest(args)
        
        if returncode == 0:
            self.print_success(f"覆盖率报告已生成: {self.coverage_dir / 'index.html'}")
        
        return returncode
    
    def list_tests(self):
        """列出所有测试"""
        self.print_header("列出所有测试")
        
        args = ["--collect-only", "-q"]
        
        return self.run_pytest(args)
    
    def run_ci_mode(self):
        """持续集成模式"""
        self.print_header("持续集成模式")
        self.print_info("运行完整测试套件，生成所有报告")
        
        args = [
            "-v",
            "--tb=short",
            "--strict-markers",
            "--cov=core",
            "--cov=wifi_modules",
            "--cov-report=term-missing",
            f"--cov-report=html:{self.coverage_dir}",
            "--cov-report=xml",
            f"--html={self.reports_dir / 'ci_report.html'}",
            "--self-contained-html",
            "--junitxml={self.reports_dir / 'junit.xml'}"
        ]
        
        start_time = time.time()
        returncode = self.run_pytest(args)
        elapsed_time = time.time() - start_time
        
        print(f"\n{Colors.BOLD}CI测试耗时: {elapsed_time:.2f}秒{Colors.RESET}\n")
        
        if returncode == 0:
            self.print_success("CI测试通过 ✅")
        else:
            self.print_error("CI测试失败 ❌")
        
        return returncode
    
    def show_test_summary(self):
        """显示测试文件摘要"""
        self.print_header("测试文件摘要")
        
        test_files = list(self.tests_dir.glob("test_*.py"))
        
        print(f"{Colors.BOLD}共找到 {len(test_files)} 个测试文件:{Colors.RESET}\n")
        
        for test_file in sorted(test_files):
            # 统计测试函数数量
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    test_count = content.count('def test_')
                
                print(f"  {Colors.GREEN}•{Colors.RESET} {test_file.name:<35} ({test_count} 个测试)")
            except Exception as e:
                print(f"  {Colors.RED}•{Colors.RESET} {test_file.name:<35} (读取失败)")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="WiFi专业工具 - 自动化测试运行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s                          # 运行所有测试（带覆盖率和HTML报告）
  %(prog)s --quick                   # 快速测试（跳过慢速测试）
  %(prog)s --marker integration      # 运行集成测试
  %(prog)s --file test_wifi6_analyzer.py  # 运行特定测试文件
  %(prog)s --failed                  # 重新运行失败的测试
  %(prog)s --ci                      # CI模式（完整报告）
  %(prog)s --list                    # 列出所有测试
  %(prog)s --summary                 # 显示测试摘要
        """
    )
    
    parser.add_argument(
        '--quick', '-q',
        action='store_true',
        help='快速测试模式（跳过慢速测试）'
    )
    
    parser.add_argument(
        '--marker', '-m',
        type=str,
        help='按标记运行测试 (admin_required, performance, integration, slow)'
    )
    
    parser.add_argument(
        '--file', '-f',
        type=str,
        help='运行特定测试文件或测试函数 (例: test_wifi6_analyzer.py 或 test_wifi6_analyzer.py::test_scan)'
    )
    
    parser.add_argument(
        '--failed', '-lf',
        action='store_true',
        help='重新运行上次失败的测试'
    )
    
    parser.add_argument(
        '--ci',
        action='store_true',
        help='持续集成模式（完整测试+所有报告）'
    )
    
    parser.add_argument(
        '--coverage-only',
        action='store_true',
        help='仅生成覆盖率报告'
    )
    
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='列出所有测试（不运行）'
    )
    
    parser.add_argument(
        '--summary', '-s',
        action='store_true',
        help='显示测试文件摘要'
    )
    
    parser.add_argument(
        '--no-coverage',
        action='store_true',
        help='不生成覆盖率报告'
    )
    
    parser.add_argument(
        '--no-html',
        action='store_true',
        help='不生成HTML报告'
    )
    
    args = parser.parse_args()
    
    # 创建测试运行器
    runner = TestRunner()
    
    # 显示欢迎信息
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}{'*' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.MAGENTA}{'WiFi专业工具 - 自动化测试系统 v1.0'.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.MAGENTA}{'*' * 70}{Colors.RESET}\n")
    
    # 显示测试摘要
    if args.summary:
        runner.show_test_summary()
        return 0
    
    # 设置环境
    runner.setup_environment()
    
    # 检查依赖
    if not runner.check_dependencies():
        return 1
    
    # 根据参数执行测试
    returncode = 0
    
    try:
        if args.list:
            returncode = runner.list_tests()
        
        elif args.ci:
            returncode = runner.run_ci_mode()
        
        elif args.quick:
            returncode = runner.run_quick_tests()
        
        elif args.marker:
            returncode = runner.run_by_marker(args.marker)
        
        elif args.file:
            test_path = args.file if args.file.startswith('tests/') else f'tests/{args.file}'
            returncode = runner.run_specific_test(test_path)
        
        elif args.failed:
            returncode = runner.run_failed_tests()
        
        elif args.coverage_only:
            returncode = runner.run_coverage_only()
        
        else:
            # 默认：运行所有测试
            returncode = runner.run_all_tests(
                verbose=True,
                coverage=not args.no_coverage,
                html_report=not args.no_html
            )
        
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}测试被用户中断{Colors.RESET}")
        returncode = 130
    
    except Exception as e:
        print(f"\n\n{Colors.RED}测试运行出错: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        returncode = 1
    
    # 显示结束信息
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}{'*' * 70}{Colors.RESET}")
    if returncode == 0:
        print(f"{Colors.BOLD}{Colors.GREEN}{'测试完成 ✨'.center(70)}{Colors.RESET}")
    else:
        print(f"{Colors.BOLD}{Colors.RED}{f'测试失败 (退出码: {returncode})'.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.MAGENTA}{'*' * 70}{Colors.RESET}\n")
    
    return returncode


if __name__ == "__main__":
    sys.exit(main())
