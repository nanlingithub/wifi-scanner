"""
macOS PyInstaller 运行时钩子
确保打包后的应用能正确初始化为 GUI 前台应用
此文件在 PyInstaller 打包的 .app 启动时最先执行。
"""
import sys

# multiprocessing 冻结支持（必须在 main 之前调用）
try:
    import multiprocessing
    multiprocessing.freeze_support()
except Exception:
    pass

# macOS：通过 AppKit 把进程注册为前台 GUI 应用
# pyobjc 在 macOS 上通常可用（系统自带），全部 try/except 保护
if sys.platform == 'darwin':
    try:
        from AppKit import NSApplication  # noqa
        _ns_app = NSApplication.sharedApplication()
        _ns_app.activateIgnoringOtherApps_(True)
    except Exception:
        # pyobjc 不可用或激活失败时静默忽略，main() 中的 osascript 会兜底
        pass
