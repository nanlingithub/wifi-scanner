"""
权限检测工具模块
用于检测和处理管理员权限需求
"""

import ctypes
import sys
import os
from tkinter import messagebox


def is_admin():
    """
    检测当前进程是否具有管理员权限
    
    Returns:
        bool: True表示有管理员权限，False表示无管理员权限
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def restart_as_admin():
    """
    以管理员权限重启当前程序
    
    Returns:
        bool: True表示成功启动，False表示失败
    """
    try:
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
    except Exception as e:
        print(f"以管理员权限重启失败: {e}")
        return False


def check_admin_rights(feature_name="此功能", show_prompt=True):
    """
    检查管理员权限，如果没有则提示用户
    
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
    
    response = messagebox.askyesno(
        "权限不足",
        f"{feature_name}需要管理员权限才能正常运行。\n\n"
        f"是否以管理员身份重启程序？\n\n"
        f"点击'是'将重启程序（需要UAC授权）\n"
        f"点击'否'将继续运行（某些功能可能受限）",
        icon='warning'
    )
    
    if response:
        if restart_as_admin():
            # 成功启动管理员进程，退出当前进程
            sys.exit(0)
        else:
            messagebox.showerror(
                "启动失败",
                "无法以管理员权限启动程序。\n"
                "请手动右键程序图标，选择'以管理员身份运行'。"
            )
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
    获取当前权限状态的文本描述
    
    Returns:
        str: 权限状态描述
    """
    if is_admin():
        return "✓ 管理员模式"
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
