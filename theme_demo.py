#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
主题演示工具 - 展示所有企业主题效果
版本: 1.0
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wifi_modules.theme import ModernTheme, ModernButton, ModernCard, StatusBadge, apply_modern_style


class ThemeDemo:
    """主题演示窗口"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("WiFi专业工具 - 企业主题演示")
        self.root.geometry("1200x800")
        
        self.current_theme = 'enterprise_blue'
        self.setup_ui()
        self.apply_theme()
        
    def setup_ui(self):
        """设置UI"""
        # 顶部控制面板
        control_panel = tk.Frame(self.root)
        control_panel.pack(fill='x', padx=10, pady=10)
        
        tk.Label(control_panel, text="选择主题:", 
                font=('Microsoft YaHei UI', 11, 'bold')).pack(side='left', padx=5)
        
        # 主题按钮
        themes = [
            ('浅色经典', 'light'),
            ('深色经典', 'dark'),
            ('🏢 商务蓝', 'enterprise_blue'),
            ('🏢 专业灰', 'enterprise_gray'),
            ('🏢 科技黑', 'enterprise_tech'),
            ('🏢 金融版', 'enterprise_finance'),
            ('🏢 医疗版', 'enterprise_medical')
        ]
        
        for name, theme_id in themes:
            btn = tk.Button(control_panel, text=name,
                          command=lambda t=theme_id: self.switch_theme(t),
                          relief='raised', borderwidth=2,
                          padx=15, pady=5,
                          font=('Microsoft YaHei UI', 9))
            btn.pack(side='left', padx=3)
        
        # 主内容区
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 创建Notebook
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill='both', expand=True)
        
        # 创建演示标签页
        self.create_demo_tabs()
        
    def create_demo_tabs(self):
        """创建演示标签页"""
        # Tab 1: 按钮和徽章
        tab1 = ttk.Frame(self.notebook)
        self.notebook.add(tab1, text="🎨 按钮和徽章")
        self.create_buttons_demo(tab1)
        
        # Tab 2: 卡片和表格
        tab2 = ttk.Frame(self.notebook)
        self.notebook.add(tab2, text="📊 卡片和表格")
        self.create_cards_demo(tab2)
        
        # Tab 3: 颜色方案
        tab3 = ttk.Frame(self.notebook)
        self.notebook.add(tab3, text="🎨 配色方案")
        self.create_colors_demo(tab3)
        
    def create_buttons_demo(self, parent):
        """创建按钮演示"""
        theme = ModernTheme.get_theme(self.current_theme)
        
        # 标题
        title_frame = tk.Frame(parent, bg=theme['bg'])
        title_frame.pack(fill='x', pady=10)
        
        tk.Label(title_frame, text="按钮样式演示",
                font=('Microsoft YaHei UI', 14, 'bold'),
                bg=theme['bg'], fg=theme['fg']).pack()
        
        # 按钮容器
        btn_container = tk.Frame(parent, bg=theme['bg'])
        btn_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 主要按钮
        primary_frame = tk.Frame(btn_container, bg=theme['bg'])
        primary_frame.pack(fill='x', pady=10)
        
        tk.Label(primary_frame, text="Primary 按钮:",
                bg=theme['bg'], fg=theme['fg'],
                font=('Microsoft YaHei UI', 10, 'bold')).pack(side='left', padx=10)
        
        ModernButton(primary_frame, text="WiFi扫描", style='primary',
                    theme_name=self.current_theme).pack(side='left', padx=5)
        ModernButton(primary_frame, text="开始监控", style='primary',
                    theme_name=self.current_theme).pack(side='left', padx=5)
        ModernButton(primary_frame, text="生成报告", style='primary',
                    theme_name=self.current_theme).pack(side='left', padx=5)
        
        # 成功按钮
        success_frame = tk.Frame(btn_container, bg=theme['bg'])
        success_frame.pack(fill='x', pady=10)
        
        tk.Label(success_frame, text="Success 按钮:",
                bg=theme['bg'], fg=theme['fg'],
                font=('Microsoft YaHei UI', 10, 'bold')).pack(side='left', padx=10)
        
        ModernButton(success_frame, text="连接成功", style='success',
                    theme_name=self.current_theme).pack(side='left', padx=5)
        ModernButton(success_frame, text="验证通过", style='success',
                    theme_name=self.current_theme).pack(side='left', padx=5)
        
        # 警告按钮
        warning_frame = tk.Frame(btn_container, bg=theme['bg'])
        warning_frame.pack(fill='x', pady=10)
        
        tk.Label(warning_frame, text="Warning 按钮:",
                bg=theme['bg'], fg=theme['fg'],
                font=('Microsoft YaHei UI', 10, 'bold')).pack(side='left', padx=10)
        
        ModernButton(warning_frame, text="信号弱", style='warning',
                    theme_name=self.current_theme).pack(side='left', padx=5)
        ModernButton(warning_frame, text="干扰检测", style='warning',
                    theme_name=self.current_theme).pack(side='left', padx=5)
        
        # 危险按钮
        danger_frame = tk.Frame(btn_container, bg=theme['bg'])
        danger_frame.pack(fill='x', pady=10)
        
        tk.Label(danger_frame, text="Danger 按钮:",
                bg=theme['bg'], fg=theme['fg'],
                font=('Microsoft YaHei UI', 10, 'bold')).pack(side='left', padx=10)
        
        ModernButton(danger_frame, text="安全漏洞", style='danger',
                    theme_name=self.current_theme).pack(side='left', padx=5)
        ModernButton(danger_frame, text="强制断开", style='danger',
                    theme_name=self.current_theme).pack(side='left', padx=5)
        
        # 状态徽章
        badge_frame = tk.Frame(btn_container, bg=theme['bg'])
        badge_frame.pack(fill='x', pady=20)
        
        tk.Label(badge_frame, text="状态徽章:",
                bg=theme['bg'], fg=theme['fg'],
                font=('Microsoft YaHei UI', 10, 'bold')).pack(side='left', padx=10)
        
        StatusBadge(badge_frame, text="在线", status='success',
                   theme_name=self.current_theme).pack(side='left', padx=5)
        StatusBadge(badge_frame, text="信号弱", status='warning',
                   theme_name=self.current_theme).pack(side='left', padx=5)
        StatusBadge(badge_frame, text="离线", status='danger',
                   theme_name=self.current_theme).pack(side='left', padx=5)
        StatusBadge(badge_frame, text="WiFi 6E", status='info',
                   theme_name=self.current_theme).pack(side='left', padx=5)
        
    def create_cards_demo(self, parent):
        """创建卡片演示"""
        theme = ModernTheme.get_theme(self.current_theme)
        
        # 创建tk.Frame而不是使用ttk.Frame
        cards_wrapper = tk.Frame(parent, bg=theme['bg'])
        cards_wrapper.pack(fill='both', expand=True)
        
        cards_wrapper = tk.Frame(parent, bg=theme['bg'])
        cards_wrapper.pack(fill='both', expand=True)
        
        # 卡片容器
        cards_container = tk.Frame(cards_wrapper, bg=theme['bg'])
        cards_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 网络信息卡片
        card1 = ModernCard(cards_container, title="📡 网络概览",
                          theme_name=self.current_theme)
        card1.pack(fill='both', expand=True, pady=10)
        
        content = card1.get_content_frame()
        
        info_items = [
            ("SSID", "Enterprise-WiFi-5G"),
            ("频段", "5 GHz"),
            ("信道", "36 (5180 MHz)"),
            ("信号强度", "-45 dBm (优秀)"),
            ("加密方式", "WPA3-Enterprise"),
            ("速率", "866 Mbps")
        ]
        
        for label, value in info_items:
            row = tk.Frame(content, bg=theme['card_bg'])
            row.pack(fill='x', pady=3)
            
            tk.Label(row, text=f"{label}:",
                    bg=theme['card_bg'], fg=theme['text_muted'],
                    font=('Microsoft YaHei UI', 9)).pack(side='left')
            
            tk.Label(row, text=value,
                    bg=theme['card_bg'], fg=theme['fg'],
                    font=('Microsoft YaHei UI', 9, 'bold')).pack(side='left', padx=(10, 0))
        
        # 安全评分卡片
        card2 = ModernCard(cards_container, title="🔒 安全评分",
                          theme_name=self.current_theme)
        card2.pack(fill='both', expand=True, pady=10)
        
        content2 = card2.get_content_frame()
        
        score_frame = tk.Frame(content2, bg=theme['card_bg'])
        score_frame.pack(fill='x')
        
        tk.Label(score_frame, text="综合评分:",
                bg=theme['card_bg'], fg=theme['text_muted'],
                font=('Microsoft YaHei UI', 10)).pack(side='left')
        
        tk.Label(score_frame, text="92/100",
                bg=theme['card_bg'], fg=theme['success'],
                font=('Microsoft YaHei UI', 20, 'bold')).pack(side='left', padx=(10, 0))
        
        StatusBadge(score_frame, text="优秀", status='success',
                   theme_name=self.current_theme).pack(side='left', padx=(10, 0))
        
    def create_colors_demo(self, parent):
        """创建配色方案演示"""
        theme = ModernTheme.get_theme(self.current_theme)
        
        # 创建tk.Frame而不是使用ttk.Frame
        colors_wrapper = tk.Frame(parent, bg=theme['bg'])
        colors_wrapper.pack(fill='both', expand=True)
        
        colors_wrapper = tk.Frame(parent, bg=theme['bg'])
        colors_wrapper.pack(fill='both', expand=True)
        
        # 标题
        title = tk.Label(colors_wrapper, text=f"当前主题配色方案: {ModernTheme.get_theme_display_name(self.current_theme)}",
                        bg=theme['bg'], fg=theme['fg'],
                        font=('Microsoft YaHei UI', 14, 'bold'))
        title.pack(pady=20)
        
        # 配色容器
        colors_container = tk.Frame(colors_wrapper, bg=theme['bg'])
        colors_container.pack(fill='both', expand=True, padx=30)
        
        # 主要颜色
        colors = [
            ("主色调 (Primary)", theme['primary']),
            ("成功 (Success)", theme['success']),
            ("警告 (Warning)", theme['warning']),
            ("危险 (Danger)", theme['danger']),
            ("信息 (Info)", theme['info']),
            ("次要 (Secondary)", theme['secondary'])
        ]
        
        for name, color in colors:
            row = tk.Frame(colors_container, bg=theme['bg'])
            row.pack(fill='x', pady=8)
            
            # 颜色方块
            color_box = tk.Frame(row, bg=color, width=80, height=40)
            color_box.pack(side='left', padx=10)
            color_box.pack_propagate(False)
            
            # 颜色名称
            tk.Label(row, text=name,
                    bg=theme['bg'], fg=theme['fg'],
                    font=('Microsoft YaHei UI', 10, 'bold')).pack(side='left', padx=10)
            
            # 颜色代码
            tk.Label(row, text=color,
                    bg=theme['bg'], fg=theme['text_muted'],
                    font=('Consolas', 10)).pack(side='left', padx=10)
        
    def switch_theme(self, theme_name):
        """切换主题"""
        self.current_theme = theme_name
        self.apply_theme()
        
        # 重新创建标签页
        for child in self.notebook.winfo_children():
            child.destroy()
        self.create_demo_tabs()
        
    def apply_theme(self):
        """应用主题"""
        theme = ModernTheme.get_theme(self.current_theme)
        apply_modern_style(self.root, self.current_theme)
        self.root.configure(bg=theme['bg'])
        
    def run(self):
        """运行演示"""
        self.root.mainloop()


if __name__ == '__main__':
    demo = ThemeDemo()
    demo.run()
