"""
权限检测工具模块
用于检测和处理管理员权限需求
支持 Windows、macOS 和 Linux
"""

import ctypes
import sys
import os
import platform
from tkinter import messagebox


def is_admin():
    """
    检测当前进程是否具有管理员权限（跨平台）
    
    Returns:
        bool: True表示有管理员权限，False表示无管理员权限
    """
    system = platform.system().lower()
    
    try:
        if system == "windows":
            # Windows: 使用 IsUserAnAdmin
            return ctypes.windll.shell32.IsUserAnAdmin()
        elif system == "darwin":  # macOS
            # macOS: 检查是否为 root 用户
            return os.geteuid() == 0
        elif system == "linux":
            # Linux: 检查是否为 root 用户
            return os.geteuid() == 0
        else:
            return False
    except Exception:
        return False


def restart_as_admin():
    """
    以管理员权限重启当前程序（跨平台）
    
    Returns:
        bool: True表示成功启动，False表示失败
    """
    system = platform.system().lower()
    
    try:
        if system == "windows":
            # Windows: 使用 ShellExecute
            if sys.argv[0].endswith('.py'):
                # Python脚本模式
                script = os.path.abspath(sys.argv[0])
                params = ' '.join([script] + sys.argv[1:])
                
                ctypes.windll.shell32.ShellExecuteW(
                    None, 
                    "runas", 
                    sys.executable, 
                    params, 
                    None, 
                    1  # SW_SHOWNORMAL
                )
            else:
                # EXE打包模式
                exe_path = sys.executable
                params = ' '.join(sys.argv[1:])
                
                ctypes.windll.shell32.ShellExecuteW(
                    None,
                    "runas",
                    exe_path,
                    params,
                    None,
                    1
                )
            return True
            
        elif system in ["darwin", "linux"]:  # macOS 或 Linux
            # 使用 osascript (macOS) 或 pkexec/gksudo (Linux)
            script_path = os.path.abspath(sys.argv[0])
            
            if system == "darwin":
                # macOS: 使用 osascript 提权
                cmd = f'''osascript -e 'do shell script "python3 {script_path}" with administrator privileges' '''
            else:
                # Linux: 尝试使用 pkexec 或 gksudo
                if os.path.exists('/usr/bin/pkexec'):
                    cmd = f'pkexec python3 {script_path}'
                elif os.path.exists('/usr/bin/gksudo'):
                    cmd = f'gksudo python3 {script_path}'
                else:
                    # 回退到终端 sudo
                    cmd = f'xterm -e "sudo python3 {script_path}"'
            
            os.system(cmd)
            return True
        else:
            return False
            
    except Exception as e:
        print(f"以管理员权限重启失败: {e}")
        return False


def check_admin_rights(feature_name="此功能", show_prompt=True):
    """
    检查管理员权限，如果没有则提示用户（跨平台）
    
    Args:
        feature_name: 功能名称，用于显示在提示框中
        show_prompt: 是否显示提示框
        
    Returns:
        bool: True表示有权限或用户选择继续，False表示无权限且用户取消
    """
    if is_admin():
        return True
    
    if not show_prompt:
        return False
    
    system = platform.system().lower()
    
    if system == "windows":
        prompt_msg = (
            f"{feature_name}需要管理员权限才能正常运行。\n\n"
            f"是否以管理员身份重启程序？\n\n"
            f"点击'是'将重启程序（需要UAC授权）\n"
            f"点击'否'将继续运行（某些功能可能受限）"
        )
    else:
        prompt_msg = (
            f"{feature_name}需要管理员权限才能正常运行。\n\n"
            f"是否以管理员权限重启程序？\n\n"
            f"点击'是'将重启程序（需要输入密码）\n"
            f"点击'否'将继续运行（某些功能可能受限）"
        )
    
    response = messagebox.askyesno(
        "权限不足",
        prompt_msg,
        icon='warning'
    )
    
    if response:
        if restart_as_admin():
            # 成功启动管理员进程，退出当前进程
            sys.exit(0)
        else:
            if system == "windows":
                error_msg = (
                    "无法以管理员权限启动程序。\n"
                    "请手动右键程序图标，选择'以管理员身份运行'。"
                )
            else:
                error_msg = (
                    "无法以管理员权限启动程序。\n"
                    "请在终端使用 sudo 运行此程序。"
                )
            
            messagebox.showerror("启动失败", error_msg)
            return False
    
    return False  # 用户选择不以管理员身份运行


def require_admin(func):
    """
    装饰器：要求函数必须在管理员权限下运行
    
    使用示例:
        @require_admin
        def traceroute_scan(self):
            # 需要管理员权限的操作
            pass
    """
    def wrapper(*args, **kwargs):
        if not is_admin():
            messagebox.showwarning(
                "权限不足",
                f"操作'{func.__name__}'需要管理员权限。\n"
                f"请以管理员身份重启程序后再试。"
            )
            return None
        return func(*args, **kwargs)
    
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


def get_admin_status_text():
    """
    获取当前权限状态的文本描述（跨平台）
    
    Returns:
        str: 权限状态描述
    """
    system = platform.system().lower()
    
    if is_admin():
        if system == "windows":
            return "✓ 管理员模式"
        else:
            return "✓ Root模式"
    else:
        return "⚠ 受限模式（部分功能需要管理员权限）"


# 使用示例
if __name__ == "__main__":
    print("权限检测测试")
    print(f"当前权限状态: {get_admin_status_text()}")
    
    if not is_admin():
        print("\n当前未以管理员身份运行")
        print("某些功能（如Traceroute）可能受限")
    else:
        print("\n✓ 当前以管理员身份运行")
        print("所有功能均可正常使用")
