"""
macOS PyInstaller 运行时钩子
确保打包后的应用能正确初始化为 GUI 前台应用
"""
import sys
import os

# multiprocessing 冻结支持（必须在 main 之前调用）
import multiprocessing
multiprocessing.freeze_support()

# macOS：通过 AppKit 激活应用，使其成为前台 GUI 进程
# 这是解决"打开无窗口"问题的根本方案
if sys.platform == 'darwin':
    try:
        from AppKit import NSApplication, NSApp
        app = NSApplication.sharedApplication()
        app.activateIgnoringOtherApps_(True)
    except ImportError:
        # pyobjc 不可用时，退回到 osascript 方案（在 main() 中处理）
        pass
