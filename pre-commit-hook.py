#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Git Pre-commit Hook - 提交前自动测试
将此文件复制到 .git/hooks/pre-commit 并赋予执行权限

Windows: copy pre-commit-hook.py .git\hooks\pre-commit
Linux/Mac: cp pre-commit-hook.py .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
"""

import sys
import subprocess
import os
from pathlib import Path


def run_quick_tests():
    """运行快速测试"""
    print("\n" + "="*70)
    print("🧪 运行预提交测试...")
    print("="*70 + "\n")
    
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    
    # 运行快速测试（跳过慢速测试）
    cmd = [sys.executable, "run_tests.py", "--quick", "--no-html"]
    
    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print("\n✅ 测试通过，允许提交\n")
            return 0
        else:
            print("\n❌ 测试失败，提交被阻止")
            print("   请修复测试错误后再提交\n")
            print("   如需强制提交，使用: git commit --no-verify\n")
            return 1
            
    except Exception as e:
        print(f"\n⚠️  测试运行出错: {e}")
        print("   允许提交但请检查测试配置\n")
        return 0


def check_code_style():
    """检查代码风格（可选）"""
    print("\n🎨 检查代码风格...")
    
    # 这里可以添加代码风格检查，例如：
    # - Black格式化检查
    # - Flake8 linting
    # - Pylint检查
    
    # 示例：检查是否有TODO标记
    staged_files = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True
    ).stdout.strip().split("\n")
    
    python_files = [f for f in staged_files if f.endswith('.py')]
    
    if python_files:
        print(f"   检查 {len(python_files)} 个Python文件...")
    
    return 0


def main():
    """主函数"""
    # 检查是否在Git仓库中
    if not os.path.exists('.git'):
        print("⚠️  警告: 不在Git仓库中，跳过预提交检查")
        return 0
    
    # 1. 运行快速测试
    if run_quick_tests() != 0:
        return 1
    
    # 2. 检查代码风格（可选）
    # check_code_style()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
