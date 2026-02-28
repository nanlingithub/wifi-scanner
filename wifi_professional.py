#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WiFi专业分析工具 - 模块化版本
功能：WiFi网络扫描、信号分析、热力图生成、性能评估、信号罗盘测向、企业级报告生成、PCI-DSS安全评估、智能干扰源定位
版本：1.6.3
开发者：NL@China_SZ
"""

import tkinter as tk
import weakref  # P1修复: 防止循环引用
from tkinter import ttk, messagebox
import sys
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


class WiFiProfessionalApp:
    """WiFi专业分析工具主应用"""
    
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_TITLE} v{VERSION}")
        self.root.geometry("1400x900")
        
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
        theme_menu.add_command(label='✓ 浅色经典' if self.current_theme == 'light' else '   浅色经典', 
                              command=lambda: self._switch_theme('light'))
        theme_menu.add_command(label='✓ 深色经典' if self.current_theme == 'dark' else '   深色经典', 
                              command=lambda: self._switch_theme('dark'))
        theme_menu.add_separator()
        theme_menu.add_command(label='✓ 🏢 商务蓝' if self.current_theme == 'enterprise_blue' else '   🏢 商务蓝', 
                              command=lambda: self._switch_theme('enterprise_blue'))
        theme_menu.add_command(label='✓ 🏢 专业灰' if self.current_theme == 'enterprise_gray' else '   🏢 专业灰', 
                              command=lambda: self._switch_theme('enterprise_gray'))
        theme_menu.add_command(label='✓ 🏢 科技黑' if self.current_theme == 'enterprise_tech' else '   🏢 科技黑', 
                              command=lambda: self._switch_theme('enterprise_tech'))
        theme_menu.add_command(label='✓ 🏢 金融版' if self.current_theme == 'enterprise_finance' else '   🏢 金融版', 
                              command=lambda: self._switch_theme('enterprise_finance'))
        theme_menu.add_command(label='✓ 🏢 医疗版' if self.current_theme == 'enterprise_medical' else '   🏢 医疗版', 
                              command=lambda: self._switch_theme('enterprise_medical'))
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='帮助', menu=help_menu)
        help_menu.add_command(label='关于', command=self._show_about)
        
        # 主容器
        main_container = ttk.Frame(self.root)
        main_container.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 创建Notebook（标签页容器）
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill='both', expand=True)
        
        # 创建7个标签页
        self.tabs = {}
        
        # Tab 1: 网络概览
        self.tabs['overview'] = NetworkOverviewTab(self.notebook, self.wifi_analyzer)
        self.notebook.add(self.tabs['overview'].get_frame(), 
                         text=f"{PROFESSIONAL_ICONS['network_overview']} 网络概览")
        
        # Tab 2: 信道分析
        self.tabs['channel'] = ChannelAnalysisTab(self.notebook, self.wifi_analyzer)
        self.notebook.add(self.tabs['channel'].get_frame(), 
                         text=f"{PROFESSIONAL_ICONS['channel_analysis']} 信道分析")
        
        # Tab 3: 实时监控
        self.tabs['monitor'] = RealtimeMonitorTab(self.notebook, self.wifi_analyzer)
        self.notebook.add(self.tabs['monitor'].get_frame(), 
                         text=f"{PROFESSIONAL_ICONS['realtime_monitor']} 实时监控")
        
        # Tab 4: WiFi热力图
        self.tabs['heatmap'] = HeatmapTab(self.notebook, self.wifi_analyzer)
        self.notebook.add(self.tabs['heatmap'].get_frame(), 
                         text=f"{PROFESSIONAL_ICONS['heatmap']} 信号热力图")
        
        # Tab 5: 部署优化
        self.tabs['deployment'] = DeploymentTab(self.notebook, self.wifi_analyzer)
        self.notebook.add(self.tabs['deployment'].get_frame(), 
                         text=f"{PROFESSIONAL_ICONS['deployment']} 部署优化")
        
        # Tab 6: 安全检测
        self.tabs['security'] = SecurityTab(self.notebook, self.wifi_analyzer)
        self.notebook.add(self.tabs['security'].get_frame(), 
                         text=f"{PROFESSIONAL_ICONS['security']} 安全检测")
        
        # Tab 7: 企业级报告 (新增 v1.6)
        self.tabs['enterprise'] = EnterpriseReportTab(self.notebook, self.wifi_analyzer)
        self.notebook.add(self.tabs['enterprise'].get_frame(), 
                         text="📊 企业级报告")
        
        # Tab 8: 智能干扰定位 (新增 v1.6.3)
        self.tabs['interference'] = InterferenceLocatorTab(self.notebook)
        # 标签页已在InterferenceLocatorTab内部添加
        
        # 底部状态栏
        statusbar = ttk.Frame(self.root)
        statusbar.pack(fill='x', side='bottom')
        
        ttk.Label(statusbar, text=f'版本: {VERSION}', 
                 font=('Microsoft YaHei UI', 8)).pack(side='left', padx=5)
        
        ttk.Label(statusbar, text=f'开发者: {DEVELOPER}', 
                 font=('Microsoft YaHei UI', 8)).pack(side='left', padx=5)
        
        # 权限状态显示
        admin_status = get_admin_status_text()
        self.admin_label = ttk.Label(
            statusbar, 
            text=admin_status,
            font=('Microsoft YaHei UI', 8),
            foreground='green' if is_admin() else 'orange'
        )
        self.admin_label.pack(side='left', padx=5)
        
        # 性能测试快捷按钮
        ModernButton(statusbar, text=f'{PROFESSIONAL_ICONS["performance"]} WiFi性能测试', 
                    command=self._open_performance_test, 
                    style='primary').pack(side='right', padx=5)
        
        self.status_label = ttk.Label(statusbar, text='就绪', 
                                      font=('Microsoft YaHei UI', 8))
        self.status_label.pack(side='right', padx=5)
    
    def _apply_theme(self):
        """应用主题"""
        theme = ModernTheme.get_theme(self.current_theme)
        
        # 应用现代化样式
        apply_modern_style(self.root, self.current_theme)
        
        # 应用到根窗口
        self.root.configure(bg=theme['bg'])
    
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
            config_path = 'config.json'
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
            config_path = 'config.json'
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
• 智能干扰定位 - RSSI三角定位/干扰源识别 (v1.6.3新增)

Copyright © 2026 {DEVELOPER}
保留所有权利
"""
        
        messagebox.showinfo("关于", about_text)


    def _on_closing(self):
        """✅ P1-1: 窗口关闭清理回调"""
        try:
            logging.info("应用程序正在关闭，执行清理操作...")
            
            # 1. 停止实时监控
            if hasattr(self, 'tabs') and 'realtime' in self.tabs:
                try:
                    realtime_tab = self.tabs['realtime']
                    if hasattr(realtime_tab, 'stop_monitoring'):
                        realtime_tab.stop_monitoring()
                        logging.info("✅ 实时监控已停止")
                except Exception as e:
                    logging.error(f"停止实时监控失败: {e}")
            
            # 2. 等待后台线程结束（超时保护）
            import threading
            active_threads = [t for t in threading.enumerate() if t != threading.current_thread()]
            if active_threads:
                logging.info(f"等待 {len(active_threads)} 个后台线程结束...")
                for thread in active_threads:
                    if hasattr(thread, 'join'):
                        try:
                            thread.join(timeout=2)  # ✅ 2秒超时保护
                            if thread.is_alive():
                                logging.warning(f"线程 {thread.name} 超时未结束")
                            else:
                                logging.info(f"✅ 线程 {thread.name} 已正常结束")
                        except Exception as e:
                            logging.error(f"等待线程失败: {e}")
            
            # 3. 关闭日志系统
            logging.info("关闭日志系统")
            logging.shutdown()
            
            # 4. ✅ P2-3: 停止内存监控
            if hasattr(self, 'memory_monitor'):
                self.memory_monitor.stop()
            
        except Exception as e:
            print(f"清理过程出错: {e}")
        finally:
            # 5. 销毁窗口
            self.root.destroy()


def main():
    """主函数"""
    root = tk.Tk()
    app = WiFiProfessionalApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()

