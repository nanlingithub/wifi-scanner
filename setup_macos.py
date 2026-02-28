#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
macOS 安装助手脚本
自动检查系统环境、安装依赖、创建启动脚本
"""

import os
import sys
import subprocess
import platform

def check_macos_version():
    """检查 macOS 版本"""
    print("🔍 检查 macOS 版本...")
    version = platform.mac_ver()[0]
    major_version = int(version.split('.')[0])
    
    print(f"   当前系统: macOS {version}")
    
    if major_version < 10 or (major_version == 10 and int(version.split('.')[1]) < 13):
        print("❌ 警告: 需要 macOS 10.13 (High Sierra) 或更高版本")
        return False
    
    print("✅ 系统版本符合要求")
    return True

def check_python_version():
    """检查 Python 版本"""
    print("\n🐍 检查 Python 版本...")
    version = sys.version_info
    print(f"   当前 Python 版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ 警告: 建议使用 Python 3.8 或更高版本")
        return False
    
    print("✅ Python 版本符合要求")
    return True

def check_airport_command():
    """检查 airport 命令是否可用"""
    print("\n📡 检查 WiFi 扫描工具...")
    airport_path = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
    
    if os.path.exists(airport_path):
        print(f"✅ airport 命令已找到: {airport_path}")
        return True
    else:
        print(f"❌ 未找到 airport 命令")
        return False

def install_dependencies():
    """安装依赖包"""
    print("\n📦 安装 Python 依赖包...")
    
    try:
        # 升级 pip
        print("   升级 pip...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        
        # 安装依赖
        print("   安装项目依赖...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        
        print("✅ 依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        return False

def create_launcher_script():
    """创建 macOS 启动脚本"""
    print("\n📝 创建启动脚本...")
    
    launcher_content = '''#!/bin/bash
# WiFi专业工具 macOS 启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 检查位置服务权限
echo "🔍 检查位置服务权限..."
if ! sudo -n true 2>/dev/null; then
    echo "⚠️  部分功能可能需要管理员权限"
fi

# 启动程序
echo "🚀 启动 WiFi专业工具..."
python3 wifi_professional.py

# 如果出错，等待用户按键
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ 启动失败，请检查错误信息"
    echo "按任意键退出..."
    read -n 1
fi
'''
    
    try:
        with open('启动WiFi专业工具.command', 'w', encoding='utf-8') as f:
            f.write(launcher_content)
        
        # 添加执行权限
        os.chmod('启动WiFi专业工具.command', 0o755)
        
        print("✅ 启动脚本已创建: 启动WiFi专业工具.command")
        return True
    except Exception as e:
        print(f"❌ 创建启动脚本失败: {e}")
        return False

def check_location_permission():
    """检查位置服务权限"""
    print("\n📍 检查位置服务...")
    
    try:
        result = subprocess.run(
            ["sudo", "-n", "launchctl", "list"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if "com.apple.locationd" in result.stdout:
            print("✅ 位置服务正常运行")
        else:
            print("⚠️  位置服务可能未启用")
            print("   WiFi 扫描需要位置服务权限")
            print("   请在 系统偏好设置 → 安全性与隐私 → 隐私 → 位置服务 中启用")
    except subprocess.TimeoutExpired:
        print("⚠️  无法检查位置服务状态（需要管理员权限）")
    except Exception as e:
        print(f"⚠️  位置服务检查失败: {e}")

def main():
    """主函数"""
    print("=" * 60)
    print("WiFi专业分析工具 - macOS 安装助手")
    print("版本: 1.7.2")
    print("=" * 60)
    print()
    
    # 检查系统环境
    checks = [
        check_macos_version(),
        check_python_version(),
        check_airport_command()
    ]
    
    if not all(checks):
        print("\n❌ 环境检查未通过，请解决上述问题后重试")
        return 1
    
    # 安装依赖
    if not install_dependencies():
        print("\n❌ 依赖安装失败")
        return 1
    
    # 创建启动脚本
    if not create_launcher_script():
        print("\n⚠️  启动脚本创建失败，但不影响程序运行")
    
    # 检查权限
    check_location_permission()
    
    # 完成
    print("\n" + "=" * 60)
    print("✅ 安装完成！")
    print("=" * 60)
    print()
    print("使用方法:")
    print("1. 双击 '启动WiFi专业工具.command' 运行程序")
    print("   或")
    print("2. 在终端运行: python3 wifi_professional.py")
    print()
    print("首次运行注意事项:")
    print("• 系统会提示授予位置服务权限，请允许")
    print("• 某些高级功能可能需要管理员权限")
    print("• 使用 sudo 运行可获得完整功能")
    print()
    print("如需打包为 .app 应用:")
    print("运行: ./build_macos.sh")
    print()
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  安装被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 安装出错: {e}")
        sys.exit(1)
