#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WiFi专业分析工具 - 模块化版本
功能：WiFi网络扫描、信号分析、热力图生成、性能评估、信号罗盘测向、企业级报告生成、PCI-DSS安全评估、智能干扰源定位
版本：1.6.3
开发者：NL@China_SZ
"""

import sys
import io

# 修复 pythonw.exe 无控制台模式下 sys.stdout/stderr 为 None 的问题
# 必须在所有其他 import 之前执行，否则某些模块（如 speedtest）在加载时会崩溃
_no_console = sys.stdout is None   # 记录是否为无控制台模式（pythonw.exe）
if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()

import tkinter as tk
import weakref  # P1修复: 防止循环引用
from tkinter import ttk, messagebox
import os
import logging

# 添加core模块路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入图标系统
from wifi_modules.icon_system import PROFESSIONAL_ICONS, TAB_CONFIG

# 导入权限检测工具
from core.admin_utils import is_admin, get_admin_status_text, check_admin_rights

# 版本信息
VERSION = "1.6.3"
DEVELOPER = "NL@China_SZ"
APP_TITLE = "WiFi专业分析工具"

from core.wifi_analyzer import WiFiAnalyzer
from wifi_modules import (
    ModernTheme, 
    ModernButton,
    ModernCard,
    StatusBadge,
    apply_modern_style,
    NetworkOverviewTab,
    ChannelAnalysisTab,
    RealtimeMonitorTab,
    HeatmapTab,
    DeploymentTab,
    SecurityTab
)
from wifi_modules.performance_window import PerformanceBenchmarkWindow
from wifi_modules.enterprise_report_tab import EnterpriseReportTab
from wifi_modules.interference_locator_tab import InterferenceLocatorTab

# ✅ P2-3: 导入内存监控模块
from core.memory_monitor import get_memory_monitor
import json
from pathlib import Path


class WiFiProfessionalApp:
    """WiFi专业分析工具主应用"""
    
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_TITLE} v{VERSION}")
        self.root.geometry("1400x900")
        self.root.minsize(1100, 700)

        # 窗口居中显示
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - 1400) // 2
        y = (sh - 900) // 2
        self.root.geometry(f"1400x900+{x}+{y}")

        # ✅ P1-1: 注册窗口关闭回调
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # 设置窗口图标 (支持打包后运行)
        try:
            # 获取正确的基础路径（支持PyInstaller打包）
            if getattr(sys, 'frozen', False):
                # 打包后从临时目录加载
                base_path = sys._MEIPASS
            else:
                # 开发模式从脚本目录加载
                base_path = os.path.dirname(__file__)
            
            icon_path = os.path.join(base_path, 'wifi_icon.ico')
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
            else:
                # 兼容旧文件名
                old_icon_path = os.path.join(base_path, 'wifi_professional.ico')
                if os.path.exists(old_icon_path):
                    self.root.iconbitmap(old_icon_path)
        except Exception as e:
            logging.warning(f"无法加载窗口图标: {e}")
        
        # 初始化WiFi分析器
        self.wifi_analyzer = WiFiAnalyzer()
        
        # 加载主题设置（从配置文件）
        self.current_theme = self._load_theme_config()
        
        # 用于记录所有标签页引用（便于清理）
        self.tabs = {}
        
        # ✅ P2-3: 启动内存监控（每60分钟记录一次）
        self.memory_monitor = get_memory_monitor(interval_minutes=60)
        self.memory_monitor.start()
        logging.info("✅ 内存监控已启动（间隔60分钟）")
        
        self._setup_ui()
        self._apply_theme()
    
    def _setup_ui(self):
        """设置用户界面"""
        # 顶部菜单栏
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='文件', menu=file_menu)
        file_menu.add_command(label='退出', command=self.root.quit)
        
        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='工具', menu=tools_menu)
        tools_menu.add_command(label='⚡ WiFi性能测试', command=self._open_performance_test)
        tools_menu.add_separator()
        
        # 主题子菜单
        theme_menu = tk.Menu(tools_menu, tearoff=0)
        tools_menu.add_cascade(label='🎨 主题选择', menu=theme_menu)
        
        # 添加所有主题选项
        for tid, tlabel in [
            ('light',              '浅色经典'),
            ('dark',               '深色经典'),
            (None, None),
            ('enterprise_blue',    '🏢 商务蓝'),
            ('enterprise_gray',    '🏢 专业灰'),
            ('enterprise_tech',    '🏢 科技黑'),
            ('enterprise_finance', '🏢 金融版'),
            ('enterprise_medical', '🏢 医疗版'),
        ]:
            if tid is None:
                theme_menu.add_separator()
            else:
                mark = '✓ ' if self.current_theme == tid else '   '
                theme_menu.add_command(label=f'{mark}{tlabel}',
                                       command=lambda t=tid: self._switch_theme(t))
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='帮助', menu=help_menu)
        help_menu.add_command(label='关于', command=self._show_about)

        # ─── 顶部 Header 栏 ───────────────────────────────────────────
        self._header_bar = tk.Frame(self.root, height=68)
        self._header_bar.pack(fill='x', side='top')
        self._header_bar.pack_propagate(False)

        # 左侧：图标 + 应用名
        self._left_hdr = tk.Frame(self._header_bar)
        self._left_hdr.pack(side='left', padx=(16, 0), pady=6)
        self._app_icon_label = tk.Label(self._left_hdr, text='📶',
                                        font=('Microsoft YaHei UI', 18))
        self._app_icon_label.pack(side='left', padx=(0, 8))
        self._title_frame = tk.Frame(self._left_hdr)
        self._title_frame.pack(side='left')
        self._header_title = tk.Label(self._title_frame, text=APP_TITLE,
                                      font=('Microsoft YaHei UI', 14, 'bold'))
        self._header_title.pack(anchor='w')
        self._header_sub = tk.Label(self._title_frame,
                                    text=f'v{VERSION}  —  专业级 WiFi 网络分析工具',
                                    font=('Microsoft YaHei UI', 8))
        self._header_sub.pack(anchor='w')

        # 右侧：管理员徽章 + 性能测试按钮
        self._right_hdr = tk.Frame(self._header_bar)
        self._right_hdr.pack(side='right', padx=(0, 16), pady=14)
        self._header_perf_btn = ModernButton(
            self._right_hdr,
            text=f'{PROFESSIONAL_ICONS["performance"]} 性能测试',
            command=self._open_performance_test,
            style='primary',
            font=('Microsoft YaHei UI', 9, 'bold'),
            padx=14, pady=6
        )
        self._header_perf_btn.pack(side='right', padx=(8, 0))
        admin_fg = '#27ae60' if is_admin() else '#e67e22'
        self._header_admin = tk.Label(self._right_hdr, text=get_admin_status_text(),
                                      font=('Microsoft YaHei UI', 9), fg=admin_fg)
        self._header_admin.pack(side='right')

        # Header 底部分隔线
        self._header_sep = tk.Frame(self.root, height=1)
        self._header_sep.pack(fill='x', side='top')

        # ─── 主内容区 ─────────────────────────────────────────────────
        main_container = ttk.Frame(self.root)
        main_container.pack(fill='both', expand=True, padx=6, pady=(6, 0))

        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill='both', expand=True)

        self.tabs = {}
        tab_defs = [
            ('overview',   NetworkOverviewTab,  (self.notebook, self.wifi_analyzer), PROFESSIONAL_ICONS['network_overview'], '网络概览'),
            ('channel',    ChannelAnalysisTab,  (self.notebook, self.wifi_analyzer), PROFESSIONAL_ICONS['channel_analysis'], '信道分析'),
            ('monitor',    RealtimeMonitorTab,  (self.notebook, self.wifi_analyzer), PROFESSIONAL_ICONS['realtime_monitor'], '实时监控'),
            ('heatmap',    HeatmapTab,          (self.notebook, self.wifi_analyzer), PROFESSIONAL_ICONS['heatmap'],          '信号热力图'),
            ('deployment', DeploymentTab,       (self.notebook, self.wifi_analyzer), PROFESSIONAL_ICONS['deployment'],       '部署优化'),
            ('security',   SecurityTab,         (self.notebook, self.wifi_analyzer), PROFESSIONAL_ICONS['security'],         '安全检测'),
            ('enterprise', EnterpriseReportTab, (self.notebook, self.wifi_analyzer), '📊',                                 '企业报告'),
        ]
        for key, cls, args, icon, label in tab_defs:
            self.tabs[key] = cls(*args)
            self.notebook.add(self.tabs[key].get_frame(), text=f'  {icon} {label}  ')

        # Tab 8: 信号干扰定位（内部自行注册到 notebook）
        self.tabs['interference'] = InterferenceLocatorTab(self.notebook)

        # ─── 底部状态栏 ───────────────────────────────────────────────
        self._sb_top_sep = tk.Frame(self.root, height=1)
        self._sb_top_sep.pack(fill='x', side='bottom')

        statusbar = tk.Frame(self.root, height=28)
        statusbar.pack(fill='x', side='bottom')
        statusbar.pack_propagate(False)

        # 左侧：版本、开发者、权限状态
        self._sb_ver = tk.Label(statusbar, text=f'💻 v{VERSION}',
                                font=('Microsoft YaHei UI', 8))
        self._sb_ver.pack(side='left', padx=(12, 0))
        tk.Label(statusbar, text='│', font=('Microsoft YaHei UI', 8)).pack(side='left', padx=6)
        tk.Label(statusbar, text=f'开发: {DEVELOPER}',
                 font=('Microsoft YaHei UI', 8)).pack(side='left')
        tk.Label(statusbar, text='│', font=('Microsoft YaHei UI', 8)).pack(side='left', padx=6)
        self.admin_label = tk.Label(
            statusbar, text=get_admin_status_text(),
            font=('Microsoft YaHei UI', 8),
            fg='#27ae60' if is_admin() else '#e67e22'
        )
        self.admin_label.pack(side='left')

        # 右侧：实时时钟、就绪状态
        self._sb_clock = tk.Label(statusbar, text='', font=('Microsoft YaHei UI', 8))
        self._sb_clock.pack(side='right', padx=(0, 12))
        tk.Label(statusbar, text='│', font=('Microsoft YaHei UI', 8)).pack(side='right', padx=6)
        self.status_label = tk.Label(statusbar, text='就绪 ✅',
                                     font=('Microsoft YaHei UI', 8))
        self.status_label.pack(side='right', padx=(0, 6))

        self._update_clock()

    def _update_clock(self):
        """实时更新状态栏时钟"""
        import datetime
        now = datetime.datetime.now().strftime('%Y-%m-%d  %H:%M:%S')
        if hasattr(self, '_sb_clock'):
            self._sb_clock.config(text=f'⏰  {now}')
            self.root.after(1000, self._update_clock)
    
    def _apply_theme(self):
        """应用主题"""
        theme = ModernTheme.get_theme(self.current_theme)

        # 应用 ttk 样式
        apply_modern_style(self.root, self.current_theme)

        # 根窗口背景色
        self.root.configure(bg=theme['bg'])

        # Header 栏配色
        if hasattr(self, '_header_bar'):
            hdr_bg = theme['primary']
            hdr_fg = 'white'
            sub_fg = '#cce0ff' if 'blue' in self.current_theme else (
                     '#aad4d4' if 'medical' in self.current_theme else (
                     '#d0d0d0' if 'gray' in self.current_theme else (
                     '#f5deb3' if 'finance' in self.current_theme else (
                     '#7efff5' if 'tech' in self.current_theme else '#e0e0e0'))))

            def _set_bg_recursive(widget, bg):
                """递归设置所有子组件背景色"""
                try:
                    widget.configure(bg=bg)
                except Exception:
                    pass
                for child in widget.winfo_children():
                    _set_bg_recursive(child, bg)

            _set_bg_recursive(self._header_bar, hdr_bg)

            # 针对性设置前景色
            for lbl in (self._app_icon_label, self._header_title, self._header_admin):
                try:
                    lbl.configure(fg=hdr_fg)
                except Exception:
                    pass
            try:
                self._header_sub.configure(fg=sub_fg)
            except Exception:
                pass
            try:
                self._header_sep.configure(bg=theme['primary_dark'])
            except Exception:
                pass

        # 状态栏配色
        sb_bg = theme['card_bg']
        sb_fg = theme['text_muted']
        for attr in ('_sb_ver', '_sb_clock', 'status_label', 'admin_label'):
            w = getattr(self, attr, None)
            if w:
                try:
                    w.configure(bg=sb_bg, fg=sb_fg)
                except Exception:
                    pass
        if hasattr(self, '_sb_top_sep'):
            try:
                self._sb_top_sep.configure(bg=theme['border'])
            except Exception:
                pass
        # 状态栏父框背景
        if hasattr(self, 'status_label'):
            try:
                self.status_label.master.configure(bg=sb_bg)
            except Exception:
                pass
        # 分隔符和其他标签
        if hasattr(self, 'admin_label'):
            try:
                sb = self.admin_label.master
                for w in sb.winfo_children():
                    try:
                        w.configure(bg=sb_bg)
                    except Exception:
                        pass
            except Exception:
                pass
    
    def _open_performance_test(self):
        """打开WiFi性能测试窗口"""
        try:
            PerformanceBenchmarkWindow(self.root)
        except Exception as e:
            messagebox.showerror("错误", f"打开性能测试失败: {str(e)}")
    
    def _switch_theme(self, theme_name):
        """切换到指定主题"""
        self.current_theme = theme_name
        self._apply_theme()
        
        # 保存主题设置到配置文件
        self._save_theme_config(theme_name)
        
        # 获取主题显示名称
        display_name = ModernTheme.get_theme_display_name(theme_name)
        
        messagebox.showinfo("主题切换", 
                          f"已切换到 {display_name} 主题\n\n"
                          f"提示: 部分标签页需要重新打开才能完全应用新主题")
    
    def _toggle_theme(self):
        """快速切换主题（保留旧接口兼容性）"""
        themes = ModernTheme.get_all_themes()
        current_index = themes.index(self.current_theme) if self.current_theme in themes else 0
        next_index = (current_index + 1) % len(themes)
        self._switch_theme(themes[next_index])
    
    def _load_theme_config(self):
        """从配置文件加载主题设置"""
        try:
            config_path = Path(__file__).parent / 'config.json'
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    theme = config.get('theme', 'enterprise_blue')
                    # 验证主题是否有效
                    if theme in ModernTheme.get_all_themes():
                        logging.info(f"✅ 已加载主题配置: {theme}")
                        return theme
        except Exception as e:
            logging.warning(f"加载主题配置失败: {e}")
        
        # 默认使用企业商务蓝主题
        return 'enterprise_blue'
    
    def _save_theme_config(self, theme_name):
        """保存主题设置到配置文件"""
        try:
            config_path = Path(__file__).parent / 'config.json'
            config = {}
            
            # 读取现有配置
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            # 更新主题设置
            config['theme'] = theme_name
            
            # 保存配置
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logging.info(f"✅ 主题配置已保存: {theme_name}")
        except Exception as e:
            logging.warning(f"保存主题配置失败: {e}")
    
    def _show_about(self):
        """显示关于对话框"""
        about_text = f"""WiFi专业分析工具

版本: {VERSION}
开发者: {DEVELOPER}

功能介绍:
• 网络概览 - WiFi网络扫描与信息展示
• 信道分析 - 2.4G/5G信道占用与冲突检测
• 实时监控 - 信号强度、速率、延迟监控
• 信号热力图 - 信号覆盖可视化与优化
• 部署优化 - AP位置规划与覆盖分析
• 安全检测 - WEP/WPA/加密方式检测
• 企业级报告 - PDF/Excel专业分析报告
• 信号干扰定位 - RSSI三角定位/干扰源识别 (v1.6.3新增)

Copyright © 2026 {DEVELOPER}
保留所有权利
"""
        
        messagebox.showinfo("关于", about_text)


    def _on_closing(self):
        """✅ P1-1: 窗口关闭清理回调"""
        try:
            logging.info("应用程序正在关闭，执行清理操作...")

            # 1. 停止实时监控（线程内部有 stop_event，会迅速退出）
            if hasattr(self, 'tabs') and 'monitor' in self.tabs:
                try:
                    realtime_tab = self.tabs['monitor']
                    if hasattr(realtime_tab, 'stop_monitoring'):
                        realtime_tab.stop_monitoring()
                        logging.info("✅ 实时监控已停止")
                except Exception as e:
                    logging.error(f"停止实时监控失败: {e}")

            # 2. 停止内存监控（Event 唤醒，最多等 1 秒）
            if hasattr(self, 'memory_monitor'):
                try:
                    self.memory_monitor.stop()
                    logging.info("✅ 内存监控已停止")
                except Exception as e:
                    logging.error(f"停止内存监控失败: {e}")

            # 3. 关闭日志系统
            logging.info("关闭日志系统")
            logging.shutdown()

        except Exception as e:
            print(f"清理过程出错: {e}")
        finally:
            # 4. 销毁窗口（其余 daemon 线程随进程自动消亡）
            self.root.destroy()


def main():
    """主函数"""
    import traceback

    def _run():
        root = tk.Tk()
        app = WiFiProfessionalApp(root)
        # 确保窗口可见并置顶（pythonw.exe 下窗口可能不会自动浮到前台）
        root.deiconify()
        root.lift()
        root.attributes('-topmost', True)           # 临时置最顶层
        root.after(300, lambda: root.attributes('-topmost', False))  # 300ms 后恢复
        root.focus_force()
        root.mainloop()

    if _no_console:
        # pythonw.exe 无控制台模式：把未捕获异常写到日志文件，方便排查
        try:
            _run()
        except Exception:
            import os
            log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'crash.log')
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    import datetime
                    f.write(f"\n[{datetime.datetime.now()}] 程序崩溃:\n")
                    f.write(traceback.format_exc())
            except Exception:
                pass
    else:
        _run()


if __name__ == '__main__':
    main()

