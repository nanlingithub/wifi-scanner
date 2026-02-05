"""
网络概览标签页 - v1.5版本 (方案A: 信号罗盘)
特性：保留原有完整功能 + 集成优化的12等分雷达图 + 信号强度罗盘
功能：WiFi扫描、信号强度显示、优化雷达图、实时监控、频段分析、信道优化、报告导出、信号测向
新增：信号罗盘 - 基于RSSI的12方向信号强度扫描，提供AP方向参考（精度±30-60°）
优化：12等分雷达、简化数据结构、提升性能、降低内存占用
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import weakref  # P1修复: 防止循环引用
import time
from datetime import datetime, timedelta
import numpy as np
import queue
import subprocess
import re
import platform
from collections import deque
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from .theme import (
    ModernTheme, 
    ModernButton, 
    ModernCard,
    ModernTooltip,
    create_section_title,
    create_info_label
)
from . import font_config  # 配置中文字体

# Windows命令执行配置
if platform.system().lower() == "windows":
    CREATE_NO_WINDOW = 0x08000000
else:
    CREATE_NO_WINDOW = 0


class NetworkOverviewTab:
    """网络概览标签页 v1.4（完整功能 + 优化雷达）"""
    
    def __init__(self, parent, wifi_analyzer):
        # P1修复: 使用weakref防止循环引用
        self.parent_ref = weakref.ref(parent) if parent else None
        self.parent = parent  # 保留直接引用以兼容现有代码
        self.wifi_analyzer = wifi_analyzer
        self.frame = ttk.Frame(parent)
        
        # ✅ 线程安全机制
        self.data_lock = threading.Lock()
        self.update_queue = queue.Queue(maxsize=100)
        
        # ✅ v1.4优化：简化数据结构，12方向雷达
        self.monitoring = False
        self.monitor_thread = None
        self.radar_directions = 12  # 12等分，每30度一个点
        self.max_wifi_count = 10
        
        # 雷达数据优化：使用固定12方向存储
        self.wifi_signals = {}  # {ssid: [12个方向的信号值]}
        self.wifi_colors = {}   # {ssid: color}
        self.selected_ssids = []
        self.current_direction = 0  # 当前扫描方向（0-11）
        
        # 扫描控制
        self.scan_interval = 0.5
        self.rotation_speed = 1.0
        
        # 扫描数据缓存
        self.scanned_networks = []
        self.current_band_filter = "全部"
        
        # 连接质量监控
        self.connection_quality = {'latency': 0, 'jitter': 0, 'packet_loss': 0}
        
        # P1修复: 定时器管理
        self.after_ids = []  # 存储所有定时器ID，防止内存泄漏
        
        # 动画效果（保留旧版兼容）
        self.pulse_phase = 0
        self.update_flash = {}
        self.last_signal = {}
        self.animation_running = False
        self.last_draw_time = 0
        self.draw_throttle_ms = 100
        
        # v1.4优化：IBM色盲友好配色
        self.COLOR_BLIND_SAFE = [
            '#648FFF',  # 蓝色
            '#785EF0',  # 紫色
            '#DC267F',  # 品红色
            '#FE6100',  # 橙色
            '#FFB000',  # 黄色
            '#00B4D8',  # 青色
            '#90E0EF',  # 浅蓝
            '#023047',  # 深蓝
            '#8338EC',  # 亮紫
            '#06FFA5'   # 翠绿
        ]
        
        self._setup_ui()
        self._start_queue_processor()
    
    def _setup_ui(self):
        """设置UI（重构版 - 主入口）"""
        self._setup_control_bar()
        main_paned = self._setup_main_layout()
        self._setup_left_panel(main_paned)
        self._setup_right_panel(main_paned)
        
        # 初始化
        self._refresh_adapters()
        self._draw_empty_radar()
    
    def _setup_control_bar(self):
        """设置顶部控制栏"""
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        # 适配器选择
        self._create_adapter_selector(control_frame)
        
        # 扫描控制按钮
        self._create_scan_buttons(control_frame)
        
        # 频段过滤器
        self._create_band_filter(control_frame)
        
        # 功能按钮组
        self._create_feature_buttons(control_frame)
    
    def _create_adapter_selector(self, parent):
        """创建适配器选择器"""
        ttk.Label(parent, text="适配器:", font=('Microsoft YaHei', 10)).pack(side='left', padx=5)
        
        self.adapter_var = tk.StringVar()
        self.adapter_combo = ttk.Combobox(
            parent, 
            textvariable=self.adapter_var,
            width=50, 
            state='readonly'
        )
        self.adapter_combo.pack(side='left', padx=5)
    
    def _create_scan_buttons(self, parent):
        """创建扫描相关按钮"""
        ModernButton(
            parent, 
            text="🔄 刷新",
            command=self._refresh_adapters, 
            style='primary'
        ).pack(side='left', padx=5)
        
        ModernButton(
            parent, 
            text="📡 扫描",
            command=self._scan_wifi, 
            style='success'
        ).pack(side='left', padx=5)
    
    def _create_band_filter(self, parent):
        """创建频段过滤器"""
        ttk.Label(
            parent, 
            text="频段:", 
            font=('Microsoft YaHei', 10)
        ).pack(side='left', padx=(15, 5))
        
        self.band_var = tk.StringVar(value="全部")
        band_combo = ttk.Combobox(
            parent, 
            textvariable=self.band_var,
            values=["全部", "2.4GHz", "5GHz", "6GHz"],
            width=8, 
            state='readonly'
        )
        band_combo.pack(side='left', padx=5)
        band_combo.bind('<<ComboboxSelected>>', lambda e: self._apply_band_filter())
    
    def _create_feature_buttons(self, parent):
        """创建功能按钮组"""
        self.monitor_btn = ModernButton(
            parent, 
            text="▶ 监控",
            command=self._toggle_monitor, 
            style='warning'
        )
        self.monitor_btn.pack(side='left', padx=5)
        
        # 分析功能按钮
        buttons_config = [
            {'text': '📊 信道', 'command': self._show_channel_analysis, 'style': 'info'},
            {'text': '📈 趋势', 'command': self._show_history_chart, 'style': 'info'},
            {'text': '📄 报告', 'command': self._export_diagnostic_report, 'style': 'primary'},
            {'text': '🧭 罗盘', 'command': self._show_signal_compass, 'style': 'success'}
        ]
        
        for config in buttons_config:
            ModernButton(parent, **config).pack(side='left', padx=5)
    
    def _setup_main_layout(self):
        """设置主布局区域"""
        main_paned = ttk.PanedWindow(self.frame, orient='horizontal')
        main_paned.pack(fill='both', expand=True, padx=10, pady=5)
        return main_paned
    
    def _setup_left_panel(self, parent):
        """设置左侧面板：当前连接信息 + WiFi列表"""
        left_frame = ttk.Frame(parent)
        parent.add(left_frame, weight=2)
        
        # 当前连接信息
        self._create_connection_info(left_frame)
        
        # WiFi网络列表
        self._create_wifi_tree(left_frame)
    
    def _create_connection_info(self, parent):
        """创建当前连接信息组件"""
        ttk.Label(
            parent, 
            text="📶 当前WiFi连接",
            font=('Microsoft YaHei', 10, 'bold')
        ).pack(anchor='w', pady=5)
        
        self.current_info = scrolledtext.ScrolledText(
            parent, 
            height=8, 
            width=50,
            font=('Consolas', 9)
        )
        self.current_info.pack(fill='x', pady=5)
    
    def _create_wifi_tree(self, parent):
        """创建WiFi网络列表树形控件"""
        ttk.Label(
            parent, 
            text="🌐 周围WiFi网络",
            font=('Microsoft YaHei', 10, 'bold')
        ).pack(anchor='w', pady=5)
        
        # 定义列
        columns = (
            "☑", "#", "SSID", "信号强度", "信号(%)", "dBm", "厂商",
            "BSSID", "信道", "频段", "WiFi标准", "加密"
        )
        widths = [30, 30, 140, 95, 55, 60, 95, 125, 45, 55, 95, 75]
        
        # 创建Treeview
        self.wifi_tree = ttk.Treeview(
            parent, 
            columns=columns, 
            show='headings', 
            height=15
        )
        
        # 配置列
        for col, width in zip(columns, widths):
            self.wifi_tree.heading(col, text=col)
            anchor = 'w' if col == 'SSID' else 'center'
            self.wifi_tree.column(col, width=width, anchor=anchor)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(
            parent, 
            orient='vertical', 
            command=self.wifi_tree.yview
        )
        self.wifi_tree.configure(yscrollcommand=scrollbar.set)
        
        self.wifi_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 配置信号质量标签样式
        self._configure_tree_tags()
        
        # 绑定事件
        self.wifi_tree.bind('<Button-1>', self._on_tree_click)
        self._setup_context_menu()
    
    def _configure_tree_tags(self):
        """配置树形控件的标签样式"""
        tag_styles = {
            'excellent': '#d4edda',
            'good': '#fff3cd',
            'fair': '#ffe5d0',
            'poor': '#f8d7da',
            'wifi6e': '#e7f3ff'
        }
        
        for tag, bg_color in tag_styles.items():
            self.wifi_tree.tag_configure(tag, background=bg_color)
    
    def _setup_right_panel(self, parent):
        """设置右侧面板：WiFi雷达图"""
        right_frame = ttk.Frame(parent)
        parent.add(right_frame, weight=3)
        
        # 标题
        self._create_radar_title(right_frame)
        
        # 雷达控制
        self._create_radar_controls(right_frame)
        
        # 雷达画布
        self._create_radar_canvas(right_frame)
    
    def _create_radar_title(self, parent):
        """创建雷达图标题"""
        title_frame = ttk.Frame(parent)
        title_frame.pack(fill='x', pady=5)
        
        ttk.Label(
            title_frame, 
            text="📡 WiFi信号雷达图",
            font=('Microsoft YaHei', 10, 'bold')
        ).pack(side='left')
    
    def _create_radar_controls(self, parent):
        """创建雷达图控制组件"""
        radar_control = ttk.Frame(parent)
        radar_control.pack(fill='x', pady=5)
        
        # 刷新间隔控制
        ttk.Label(radar_control, text="刷新间隔:").pack(side='left', padx=5)
        self.interval_var = tk.StringVar(value="5秒")
        interval_combo = ttk.Combobox(
            radar_control, 
            textvariable=self.interval_var,
            values=["1秒", "2秒", "5秒", "10秒", "30秒", "60秒"],
            width=10, 
            state='readonly'
        )
        interval_combo.pack(side='left', padx=5)
        
        # 扫描速度控制
        ttk.Label(radar_control, text="速度:").pack(side='left', padx=(15, 5))
        self.speed_var = tk.DoubleVar(value=1.0)
        speed_slider = ttk.Scale(
            radar_control, 
            from_=0.5, 
            to=3.0,
            variable=self.speed_var, 
            orient='horizontal', 
            length=100
        )
        speed_slider.pack(side='left', padx=5)
        
        self.speed_label = ttk.Label(radar_control, text="1.0x")
        self.speed_label.pack(side='left')
        speed_slider.config(command=self._update_speed)
    
    def _create_radar_canvas(self, parent):
        """创建雷达图画布"""
        self.radar_figure = Figure(figsize=(6, 5), dpi=100)
        self.radar_canvas = FigureCanvasTkAgg(self.radar_figure, parent)
        self.radar_canvas.get_tk_widget().pack(fill='both', expand=True)
    
    def _draw_empty_radar(self):
        """绘制空雷达图（v1.4优化：12等分）"""
        self.radar_figure.clear()
        
        bg_color = '#fafafa'
        grid_color = '#cccccc'
        text_color = '#2c3e50'
        
        self.radar_figure.patch.set_facecolor(bg_color)
        ax = self.radar_figure.add_subplot(111, projection='polar')
        ax.set_facecolor('#ffffff')
        
        ax.set_theta_direction(-1)
        ax.set_theta_zero_location('N')
        
        # v1.4关键优化：12等分（每30度）
        max_time_points = 12
        all_angles = np.linspace(0, 2 * np.pi, max_time_points, endpoint=False)
        
        ax.set_ylim(-100, -20)
        ax.set_yticks([-100, -85, -70, -50, -20])
        ax.set_yticklabels(['-100\n极弱', '-85\n弱', '-70\n一般', 
                           '-50\n良好', '-20\n优秀'], 
                          color=text_color, fontsize=8, fontweight='bold')
        
        ax.set_xticks(all_angles)
        # v1.4：12个角度标签（0, 30, 60, ..., 330）
        angle_labels = [f'{deg}°' for deg in [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]]
        ax.set_xticklabels(angle_labels, fontsize=9, color=text_color, fontweight='bold')
        
        ax.grid(True, color=grid_color, alpha=0.5, linestyle='--', linewidth=1.2)
        ax.spines['polar'].set_color(grid_color)
        ax.spines['polar'].set_linewidth(2)
        ax.tick_params(colors=text_color, width=1.5)
        
        ax.set_title('WiFi 信号雷达分析\n12方向扫描 - 等待监控数据...', 
                    fontsize=10, pad=20, color=text_color, fontweight='bold')
        
        self.radar_figure.tight_layout()
        self.radar_canvas.draw_idle()
    
    def _update_radar(self):
        """更新雷达图 - v1.4优化版本：12等分 + 色盲友好 + 性能提升"""
        try:
            # 节流控制
            current_time = time.time() * 1000
            if current_time - self.last_draw_time < self.draw_throttle_ms:
                return
            self.last_draw_time = current_time
            
            # 线程安全读取
            with self.data_lock:
                if not self.wifi_signals:
                    return
                signals_snapshot = {k: list(v) for k, v in self.wifi_signals.items()}
                current_dir = self.current_direction
            
            # 获取选中的SSID
            selected_ssids = self.selected_ssids[:10]
            
            if len(selected_ssids) == 0:
                self.radar_figure.clear()
                ax = self.radar_figure.add_subplot(111)
                ax.text(0.5, 0.5, '请先勾选WiFi网络（最多10个）\n然后点击"开始监控"', 
                       ha='center', va='center', fontsize=16, 
                       color='#ff6600', fontweight='bold',
                       bbox=dict(boxstyle='round,pad=1', facecolor='#fff3cd', 
                                edgecolor='#ff6600', linewidth=2))
                ax.axis('off')
                self.radar_canvas.draw_idle()
                return
            
            self.radar_figure.clear()
            
            bg_color = '#fafafa'
            grid_color = '#cccccc'
            text_color = '#2c3e50'
            
            self.radar_figure.patch.set_facecolor(bg_color)
            ax = self.radar_figure.add_subplot(111, projection='polar')
            ax.set_facecolor('#ffffff')
            
            ax.set_theta_direction(-1)
            ax.set_theta_zero_location('N')
            
            # v1.4关键：12等分配置
            max_time_points = 12
            all_angles = np.linspace(0, 2 * np.pi, max_time_points, endpoint=False)
            
            # 绘制每个WiFi信号
            for ssid_idx, ssid in enumerate(selected_ssids):
                if ssid not in signals_snapshot:
                    continue
                
                values = np.array(signals_snapshot[ssid])
                color = self.COLOR_BLIND_SAFE[ssid_idx % len(self.COLOR_BLIND_SAFE)]
                
                # 检查有效数据
                valid_mask = values > -99.9
                if not np.any(valid_mask):
                    continue
                
                # 计算统计信息
                valid_values = values[valid_mask]
                mean_signal = np.mean(valid_values) if len(valid_values) > 0 else -100
                std_signal = np.std(valid_values) if len(valid_values) > 1 else 0
                
                # 稳定性评分
                if abs(mean_signal) > 0:
                    cv = (std_signal / abs(mean_signal)) * 100
                    stability_score = max(0, min(100, 100 - cv * 2))
                else:
                    stability_score = 50
                
                # 绘制填充区域
                values_closed = np.append(values, values[0])
                angles_closed = np.append(all_angles, all_angles[0])
                
                ax.fill(angles_closed, values_closed, color=color, alpha=0.25)
                
                # 绘制边线（按稳定性调整样式）
                linestyle = '-' if stability_score >= 80 else '--' if stability_score >= 60 else ':'
                alpha_line = 0.95 if stability_score >= 80 else 0.85 if stability_score >= 60 else 0.75
                
                ax.plot(angles_closed, values_closed, linestyle,
                       linewidth=2.5, color=color, alpha=alpha_line, label=ssid)
                
                # 绘制数据点
                marker_size = 10 if stability_score >= 80 else 8 if stability_score >= 60 else 6
                ax.scatter(all_angles, values, color=color, s=marker_size**2, 
                          zorder=10, edgecolors='white', linewidth=1.5, alpha=0.9)
            
            # 绘制扫描方向指示器
            current_angle = current_dir * (2*np.pi / max_time_points)
            ax.plot([current_angle, current_angle], [-100, -20], 
                   'r--', linewidth=3, alpha=0.6, label='扫描方向')
            
            # 设置刻度
            ax.set_xticks(all_angles)
            angle_labels = [f'{deg}°' for deg in [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]]
            ax.set_xticklabels(angle_labels, fontsize=9, color=text_color, fontweight='bold')
            
            ax.set_ylim(-100, -20)
            ax.set_yticks([-100, -85, -70, -50, -20])
            ax.set_yticklabels(['-100\n极弱', '-85\n弱', '-70\n一般', 
                               '-50\n良好', '-20\n优秀'], 
                              color=text_color, fontsize=8, fontweight='bold')
            
            # 网格
            ax.grid(True, color=grid_color, alpha=0.5, linestyle='--', linewidth=1.2)
            ax.spines['polar'].set_color(grid_color)
            ax.spines['polar'].set_linewidth(2)
            ax.tick_params(colors=text_color, width=1.5)
            
            # 图例
            legend = ax.legend(loc='upper left', bbox_to_anchor=(1.05, 1.0), 
                              fontsize=7, frameon=True, shadow=True,
                              fancybox=True, borderpad=0.6, labelspacing=0.8,
                              title='WiFi信号监控\n🎯 12方向扫描', 
                              title_fontsize=7.5)
            legend.get_frame().set_facecolor('white')
            legend.get_frame().set_edgecolor(grid_color)
            legend.get_frame().set_alpha(0.95)
            
            # 标题
            ax.set_title(f'WiFi 信号雷达分析\n监控{len(selected_ssids)}个网络 | 方向:{current_dir*30}°', 
                        fontsize=9, pad=20, color=text_color, fontweight='bold')
            
            self.radar_figure.tight_layout()
            self.radar_canvas.draw_idle()
            
        except Exception as e:
            print(f"[错误] 雷达图更新失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _toggle_monitor(self):
        """切换监控状态（v1.4优化）"""
        if not self.monitoring:
            # 获取选中的WiFi
            selected_indices = []
            for item in self.wifi_tree.get_children():
                values = self.wifi_tree.item(item)['values']
                if values[0] == "☑":
                    selected_indices.append(item)
            
            if not selected_indices:
                messagebox.showwarning("提示", "请先勾选要监控的WiFi网络")
                return
            
            if len(selected_indices) > 10:
                messagebox.showwarning("提示", "最多只能同时监控10个WiFi")
                return
            
            # 提取SSID
            self.selected_ssids = []
            for item in selected_indices:
                values = self.wifi_tree.item(item)['values']
                ssid = values[2]
                self.selected_ssids.append(ssid)
            
            # v1.4优化：初始化12方向数据结构
            with self.data_lock:
                self.wifi_signals = {}
                self.wifi_colors = {}
                for i, ssid in enumerate(self.selected_ssids):
                    self.wifi_signals[ssid] = [-100] * self.radar_directions
                    self.wifi_colors[ssid] = self.COLOR_BLIND_SAFE[i % len(self.COLOR_BLIND_SAFE)]
                
                self.current_direction = 0
            
            # 启动监控
            self.monitoring = True
            self.monitor_btn.config(text="⏸ 停止监控")
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            
            # 启动动画
            if not self.animation_running:
                self.animation_running = True
                self._run_animation_effects()
        else:
            self.monitoring = False
            self.monitor_btn.config(text="▶ 开始监控")
            self.animation_running = False
    
    def _monitor_loop(self):
        """监控循环（v1.4优化）"""
        while self.monitoring:
            try:
                # 扫描网络
                networks = self.wifi_analyzer.scan_wifi_networks(force_refresh=True)
                
                # v1.4优化：更新当前方向的信号数据
                with self.data_lock:
                    for ssid in self.selected_ssids:
                        found = False
                        for network in networks:
                            if network.get('ssid') == ssid:
                                signal_percent = network.get('signal_percent', 0)
                                if isinstance(signal_percent, str):
                                    signal_percent = int(signal_percent.rstrip('%'))
                                signal_dbm = -100 + (signal_percent * 0.7) if signal_percent > 0 else -100
                                
                                self.wifi_signals[ssid][self.current_direction] = signal_dbm
                                found = True
                                break
                        
                        if not found:
                            self.wifi_signals[ssid][self.current_direction] = -100
                    
                    # 移动到下一个方向
                    self.current_direction = (self.current_direction + 1) % self.radar_directions
                
                # 通知UI更新
                try:
                    self.update_queue.put_nowait({'type': 'radar_update'})
                except queue.Full:
                    print('[警告] 队列已满，数据已丢弃')  # P2修复: 添加日志
                
                # 等待（根据刷新间隔和速度）
                # 刷新间隔：一圈旋转的总时间，速度：加速倍数
                interval_str = self.interval_var.get()
                interval = int(interval_str.replace('秒', ''))
                # 每个方向的等待时间 = (刷新间隔 / 12方向) / 速度倍数
                wait_time = (interval / 12) / self.rotation_speed
                time.sleep(wait_time)
                
            except Exception as e:
                print(f"监控错误: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(5)
    
    def _update_speed(self, value):
        """更新扫描速度"""
        self.rotation_speed = float(value)
        self.speed_label.config(text=f"{self.rotation_speed:.1f}x")
    
    def _start_queue_processor(self):
        """启动队列处理器"""
        try:
            updates_processed = 0
            while updates_processed < 5:
                try:
                    update = self.update_queue.get_nowait()
                    if update['type'] == 'radar_update':
                        updates_processed += 1
                except queue.Empty:
                    break
            
            if updates_processed > 0:
                self._update_radar()
                
        except Exception as e:
            print(f"[警告] 队列处理异常: {e}")
        finally:
            # ✅ M1修复: 记录after_id
            after_id = self.parent.after(150, self._start_queue_processor)
            self.after_ids.append(after_id)
    
    def _run_animation_effects(self):
        """运行动画效果"""
        if not self.animation_running:
            return
        
        try:
            self.pulse_phase = (self.pulse_phase + 0.025) % 1.0
            
            for ssid in list(self.update_flash.keys()):
                self.update_flash[ssid] = max(0, self.update_flash[ssid] - 0.04)
                if self.update_flash[ssid] < 0.01:
                    self.update_flash[ssid] = 0
            
            has_flash = any(v > 0 for v in self.update_flash.values())
            phase_key_point = abs(self.pulse_phase % 0.25) < 0.05
            
            if (has_flash or phase_key_point) and hasattr(self, 'wifi_signals') and len(self.wifi_signals) > 0:
                try:
                    if self.update_queue.qsize() < 2:
                        self.update_queue.put_nowait({'type': 'radar_update'})
                except queue.Full:
                    print('[警告] 队列已满，数据已丢弃')  # P2修复: 添加日志
        
        except Exception as e:
            print(f"[警告] 动画效果异常: {e}")
        
        finally:
            if self.animation_running:
                after_id = self.parent.after(120, self._run_animation_effects)
                self.after_ids.append(after_id)
    
    # ========== 以下保留完整的旧版功能 ==========
    
    def _refresh_adapters(self):
        """刷新WiFi适配器列表"""
        try:
            adapters = self.wifi_analyzer.get_wifi_interfaces()
            if adapters:
                # 构建详细的适配器显示列表
                adapter_displays = []
                for adapter in adapters:
                    if isinstance(adapter, dict):
                        # 使用增强的显示名称
                        display = adapter.get('display_name', '')
                        
                        # 如果没有display_name，手动构建
                        if not display:
                            name = adapter.get('name', 'WLAN')
                            vendor = adapter.get('vendor', '')
                            std = adapter.get('wifi_standard', '')
                            state = adapter.get('state', '')
                            
                            parts = [name]
                            if vendor:
                                parts.append(f"[{vendor}]")
                            if std:
                                parts.append(f"({std})")
                            if state:
                                parts.append(f"- {state}")
                            
                            display = " ".join(parts)
                        
                        adapter_displays.append(display)
                    else:
                        # 兼容字符串格式
                        adapter_displays.append(str(adapter))
                
                self.adapter_combo['values'] = adapter_displays
                if not self.adapter_var.get() and adapter_displays:
                    self.adapter_combo.current(0)
                
                # 显示详细的适配器信息
                adapter_info = self.wifi_analyzer.get_adapter_info()
                info_parts = []
                
                vendor = adapter_info.get('vendor', '')
                model = adapter_info.get('model', '')
                wifi_std = adapter_info.get('wifi_standard', '')
                state = adapter_info.get('state', '')
                mac = adapter_info.get('mac_address', '')
                driver = adapter_info.get('driver_version', '')
                
                if vendor and model:
                    info_parts.append(f"厂商: {vendor}")
                if model:
                    info_parts.append(f"型号: {model}")
                if wifi_std:
                    info_parts.append(f"标准: {wifi_std}")
                if state:
                    info_parts.append(f"状态: {state}")
                if mac:
                    info_parts.append(f"MAC: {mac}")
                if driver:
                    info_parts.append(f"驱动: {driver}")
                
                info_text = " | ".join(info_parts) if info_parts else "适配器信息获取中..."
                print(f"[适配器信息] {info_text}")
                print(f"[信息] 找到 {len(adapters)} 个WiFi适配器")
            else:
                messagebox.showwarning("警告", "未找到WiFi适配器")
        except Exception as e:
            messagebox.showerror("错误", f"获取适配器失败: {str(e)}")
    
    def _scan_wifi(self):
        """扫描WiFi网络"""
        scan_progress = ttk.Progressbar(self.frame, mode='indeterminate')
        scan_progress.pack(pady=5)
        scan_progress.start()
        
        def scan_worker():
            try:
                self._scan_wifi_worker()
            except Exception as e:
                self.frame.after(0, lambda: messagebox.showerror("错误", f"扫描失败: {str(e)}"))
            finally:
                self.frame.after(0, scan_progress.destroy)
        
        threading.Thread(target=scan_worker, daemon=True).start()
    
    def _scan_wifi_worker(self):
        """WiFi扫描工作线程"""
        # ✅ M3修复: 批量删除Treeview项，提升性能
        self.frame.after(0, lambda: self.wifi_tree.delete(*self.wifi_tree.get_children()))
        
        try:
            # 显示当前连接信息
            current_wifi = self.wifi_analyzer.get_current_wifi_info()
            self.current_info.delete('1.0', 'end')
            if current_wifi:
                info_lines = []
                
                if 'adapter_description' in current_wifi or 'adapter_name' in current_wifi:
                    info_lines.append("【WiFi适配器】")
                    if 'adapter_description' in current_wifi:
                        info_lines.append(f"网卡型号: {current_wifi['adapter_description']}")
                    if 'adapter_name' in current_wifi:
                        info_lines.append(f"适配器名称: {current_wifi['adapter_name']}")
                    if 'mac' in current_wifi:
                        info_lines.append(f"物理地址: {current_wifi['mac']}")
                    info_lines.append("")
                
                if 'ssid' in current_wifi:
                    info_lines.append("【当前连接】")
                    info_lines.append(f"SSID: {current_wifi['ssid']}")
                    if 'signal' in current_wifi:
                        info_lines.append(f"信号强度: {current_wifi['signal']}")
                    if 'bssid' in current_wifi:
                        info_lines.append(f"BSSID(AP): {current_wifi['bssid']}")
                    if 'radio_type' in current_wifi:
                        info_lines.append(f"无线标准: {current_wifi['radio_type']}")
                    if 'channel' in current_wifi:
                        info_lines.append(f"信道: {current_wifi['channel']}")
                    if 'receive_rate' in current_wifi:
                        info_lines.append(f"接收速率: {current_wifi['receive_rate']}")
                    if 'transmit_rate' in current_wifi:
                        info_lines.append(f"发送速率: {current_wifi['transmit_rate']}")
                
                info_text = '\n'.join(info_lines) if info_lines else "已连接但无详细信息"
                self.current_info.insert('1.0', info_text)
            else:
                self.current_info.insert('1.0', "未连接WiFi")
            
            # 扫描周围网络
            networks = self.wifi_analyzer.scan_wifi_networks(force_refresh=True)
            self.scanned_networks = networks
            
            # 检测信道重叠
            overlapping_info = self._detect_channel_overlap(networks)
            if overlapping_info:
                overlap_msg = f"检测到{len(overlapping_info)}组信道重叠：\n" + "\n".join(
                    [f"• {ssid1} ↔ {ssid2}" for ssid1, ssid2 in overlapping_info[:5]]
                )
                self.frame.after(0, lambda: messagebox.showinfo("信道重叠提示", overlap_msg))
            
            # 按信号强度排序
            networks_sorted = sorted(networks, key=lambda x: x.get('signal_percent', 0), reverse=True)
            
            for idx, network in enumerate(networks_sorted, 1):
                signal_percent = network.get('signal_percent', 0)
                if isinstance(signal_percent, str):
                    signal_percent = int(signal_percent.rstrip('%')) if signal_percent != '未知' else 0
                
                signal_dbm = -100 + (signal_percent * 0.7) if signal_percent > 0 else -100
                
                quality_indicator, _ = self._get_signal_quality_indicator(signal_percent)
                bar_length = int(signal_percent / 10)
                signal_bar = quality_indicator + ' ' + '█' * bar_length + '░' * (10 - bar_length)
                
                wifi_standard = network.get('wifi_standard', 'N/A')
                band = network.get('band', 'N/A')
                if band == '6GHz':
                    wifi_standard = f"⚡{wifi_standard}"
                
                values = (
                    "", idx, network.get('ssid', 'N/A'), signal_bar,
                    f"{signal_percent}%", f"{signal_dbm:.0f} dBm",
                    network.get('vendor', '未知'), network.get('bssid', 'N/A'),
                    network.get('channel', 'N/A'), band, wifi_standard,
                    network.get('authentication', 'N/A')
                )
                
                tags = []
                if band == '6GHz':
                    tags.append('wifi6e')
                elif signal_percent >= 80:
                    tags.append('excellent')
                elif signal_percent >= 60:
                    tags.append('good')
                elif signal_percent >= 40:
                    tags.append('fair')
                else:
                    tags.append('poor')
                
                self.wifi_tree.insert('', 'end', values=values, tags=tuple(tags))
            
            band_stats = {'2.4GHz': 0, '5GHz': 0, '6GHz': 0}
            for net in networks:
                band = net.get('band', 'N/A')
                if band in band_stats:
                    band_stats[band] += 1
            
            stats_msg = f"扫描完成，发现 {len(networks)} 个WiFi网络\n" + \
                       f"2.4GHz: {band_stats['2.4GHz']} | 5GHz: {band_stats['5GHz']} | 6GHz: {band_stats['6GHz']}"
            self.frame.after(0, lambda: messagebox.showinfo("完成", stats_msg))
            
        except Exception as e:
            messagebox.showerror("错误", f"扫描失败: {str(e)}")
    
    def _get_signal_quality_indicator(self, signal_percent):
        """获取信号质量指示器"""
        if signal_percent >= 80:
            return "🟢优秀", "#28a745"
        elif signal_percent >= 60:
            return "🟡良好", "#ffc107"
        elif signal_percent >= 40:
            return "🟠一般", "#fd7e14"
        else:
            return "🔴较弱", "#dc3545"
    
    def _on_tree_click(self, event):
        """处理树形列表点击"""
        region = self.wifi_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.wifi_tree.identify_column(event.x)
            item = self.wifi_tree.identify_row(event.y)
            
            if column == '#1' and item:
                values = list(self.wifi_tree.item(item)['values'])
                if values[0] == "☑":
                    values[0] = ""
                else:
                    checked_count = sum(1 for i in self.wifi_tree.get_children() 
                                      if self.wifi_tree.item(i)['values'][0] == "☑")
                    if checked_count >= 10:
                        messagebox.showwarning("提示", "最多只能同时监控10个WiFi")
                        return
                    values[0] = "☑"
                
                self.wifi_tree.item(item, values=values)
    
    def _setup_context_menu(self):
        """设置右键菜单"""
        self.context_menu = tk.Menu(self.wifi_tree, tearoff=0)
        self.context_menu.add_command(label="📶 连接此网络", command=self._connect_wifi)
        self.context_menu.add_command(label="🔌 断开当前网络", command=self._disconnect_wifi)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="📊 详细诊断", command=self._show_network_details)
        self.context_menu.add_command(label="📋 复制BSSID", command=self._copy_bssid)
        
        self.wifi_tree.bind("<Button-3>", self._show_context_menu)
    
    def _show_context_menu(self, event):
        """显示右键菜单"""
        item = self.wifi_tree.identify_row(event.y)
        if item:
            self.wifi_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def _connect_wifi(self):
        """连接WiFi"""
        selected = self.wifi_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择一个WiFi网络")
            return
        
        ssid = self.wifi_tree.item(selected[0])['values'][2]
        
        try:
            # P0修复: 使用列表形式避免shell=True的命令注入风险
            cmd = ["netsh", "wlan", "connect", f"name={ssid}"]
            result = subprocess.run(cmd, shell=False, capture_output=True, text=True,
                                   creationflags=CREATE_NO_WINDOW, encoding='gbk', errors='ignore')
            
            if "已成功完成" in result.stdout or "successfully" in result.stdout.lower():
                messagebox.showinfo("成功", f"正在连接到 {ssid}...")
            else:
                messagebox.showerror("失败", f"连接失败：{result.stdout}")
        except Exception as e:
            messagebox.showerror("错误", f"连接失败: {str(e)}")
    
    def _disconnect_wifi(self):
        """断开WiFi"""
        try:
            # P0修复: 使用列表形式避免shell=True的命令注入风险
            cmd = ["netsh", "wlan", "disconnect"]
            result = subprocess.run(cmd, shell=False, capture_output=True, text=True,
                                   creationflags=CREATE_NO_WINDOW, encoding='gbk', errors='ignore')
            
            if "已成功完成" in result.stdout or "successfully" in result.stdout.lower():
                messagebox.showinfo("成功", "已断开WiFi连接")
            else:
                messagebox.showwarning("提示", result.stdout)
        except Exception as e:
            messagebox.showerror("错误", f"断开失败: {str(e)}")
    
    def _show_network_details(self):
        """显示网络详细信息"""
        selected = self.wifi_tree.selection()
        if not selected:
            return
        
        values = self.wifi_tree.item(selected[0])['values']
        details = f"""网络详细信息
{'='*40}
SSID: {values[2]}
信号强度: {values[4]} ({values[5]})
厂商: {values[6]}
BSSID: {values[7]}
信道: {values[8]}
频段: {values[9]}
WiFi标准: {values[10]}
加密方式: {values[11]}
"""
        messagebox.showinfo("网络详情", details)
    
    def _copy_bssid(self):
        """复制BSSID"""
        selected = self.wifi_tree.selection()
        if not selected:
            return
        
        bssid = self.wifi_tree.item(selected[0])['values'][7]
        self.frame.clipboard_clear()
        self.frame.clipboard_append(bssid)
        messagebox.showinfo("成功", f"已复制BSSID: {bssid}")
    
    def _apply_band_filter(self):
        """应用频段过滤"""
        band_filter = self.band_var.get()
        
        # ✅ M3修复: 批量删除优化性能
        self.wifi_tree.delete(*self.wifi_tree.get_children())
        
        filtered_networks = self.scanned_networks
        if band_filter != "全部":
            filtered_networks = [net for net in self.scanned_networks 
                               if net.get('band') == band_filter]
        
        for idx, network in enumerate(filtered_networks, 1):
            signal_percent = network.get('signal_percent', 0)
            if isinstance(signal_percent, str):
                signal_percent = int(signal_percent.rstrip('%')) if signal_percent != '未知' else 0
            
            quality_indicator, _ = self._get_signal_quality_indicator(signal_percent)
            bar_length = int(signal_percent / 10)
            signal_bar = quality_indicator + ' ' + '█' * bar_length + '░' * (10 - bar_length)
            signal_dbm = -100 + (signal_percent * 0.7) if signal_percent > 0 else -100
            
            band = network.get('band', 'N/A')
            wifi_standard = network.get('wifi_standard', 'N/A')
            if band == '6GHz':
                wifi_standard = f"⚡{wifi_standard}"
            
            values = (
                "", idx, network.get('ssid', 'N/A'), signal_bar,
                f"{signal_percent}%", f"{signal_dbm:.0f} dBm",
                network.get('vendor', '未知'), network.get('bssid', 'N/A'),
                network.get('channel', 'N/A'), band, wifi_standard,
                network.get('authentication', 'N/A')
            )
            
            tags = []
            if band == '6GHz':
                tags.append('wifi6e')
            elif signal_percent >= 80:
                tags.append('excellent')
            elif signal_percent >= 60:
                tags.append('good')
            elif signal_percent >= 40:
                tags.append('fair')
            else:
                tags.append('poor')
            
            self.wifi_tree.insert('', 'end', values=values, tags=tuple(tags))
        
        messagebox.showinfo("过滤结果", f"显示 {len(filtered_networks)} 个 {band_filter} 网络")
    
    def _detect_channel_overlap(self, networks):
        """检测信道重叠"""
        overlapping = set()
        networks_24g = [n for n in networks if n.get('band') == '2.4GHz']
        
        for i, net1 in enumerate(networks_24g):
            try:
                ch1 = int(net1.get('channel', 0))
                for net2 in networks_24g[i+1:]:
                    try:
                        ch2 = int(net2.get('channel', 0))
                        if abs(ch1 - ch2) <= 4:
                            overlapping.add((net1.get('ssid', 'N/A'), net2.get('ssid', 'N/A')))
                    except ValueError:
                        print('[警告] 操作失败但已忽略')  # P2修复: 添加日志
            except ValueError:
                print('[警告] 操作失败但已忽略')  # P2修复: 添加日志
        
        return list(overlapping)
    
    def _show_channel_analysis(self):
        """显示信道利用率分析"""
        if not self.scanned_networks:
            messagebox.showwarning("提示", "请先扫描WiFi网络")
            return
        
        channel_util_24 = {ch: 0 for ch in range(1, 14)}
        channel_util_5 = {}
        
        for net in self.scanned_networks:
            try:
                channel = int(net.get('channel', 0))
                signal_percent = net.get('signal_percent', 0)
                if isinstance(signal_percent, str):
                    signal_percent = int(signal_percent.rstrip('%'))
                
                band = net.get('band', 'N/A')
                
                if band == '2.4GHz' and 1 <= channel <= 13:
                    channel_util_24[channel] += signal_percent
                    for offset in [-2, -1, 1, 2]:
                        neighbor = channel + offset
                        if 1 <= neighbor <= 13:
                            channel_util_24[neighbor] += signal_percent * 0.3
                
                elif band == '5GHz':
                    if channel not in channel_util_5:
                        channel_util_5[channel] = 0
                    channel_util_5[channel] += signal_percent
            
            except (ValueError, KeyError):
                print('[警告] 操作失败但已忽略')  # P2修复: 添加日志
        
        best_channel_24 = min(channel_util_24, key=channel_util_24.get) if channel_util_24 else None
        best_channel_5 = min(channel_util_5, key=channel_util_5.get) if channel_util_5 else None
        
        analysis_window = tk.Toplevel(self.frame)
        analysis_window.title("信道利用率分析")
        analysis_window.geometry("800x600")
        
        result_text = scrolledtext.ScrolledText(analysis_window, font=('Consolas', 10))
        result_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        result_text.insert('end', "=" * 60 + "\n")
        result_text.insert('end', "信道利用率分析报告\n")
        result_text.insert('end', "=" * 60 + "\n\n")
        
        result_text.insert('end', "【2.4GHz频段】\n")
        for ch in sorted(channel_util_24.keys()):
            util = channel_util_24[ch]
            bar = '█' * int(util / 10)
            marker = " ← 推荐" if ch == best_channel_24 else ""
            result_text.insert('end', f"信道 {ch:2d}: {bar} {util:.1f}%{marker}\n")
        
        result_text.insert('end', f"\n✅ 推荐2.4GHz信道: {best_channel_24}\n\n")
        
        if channel_util_5:
            result_text.insert('end', "【5GHz频段】\n")
            for ch in sorted(channel_util_5.keys()):
                util = channel_util_5[ch]
                bar = '█' * int(util / 10)
                marker = " ← 推荐" if ch == best_channel_5 else ""
                result_text.insert('end', f"信道 {ch:3d}: {bar} {util:.1f}%{marker}\n")
            
            result_text.insert('end', f"\n✅ 推荐5GHz信道: {best_channel_5}\n")
        
        result_text.config(state='disabled')
    
    def _show_history_chart(self):
        """显示历史趋势图"""
        with self.data_lock:
            if not self.wifi_signals or len(self.selected_ssids) == 0:
                messagebox.showwarning("提示", "请先开始监控并等待数据采集")
                return
            
            signals_data = {k: list(v) for k, v in self.wifi_signals.items()}
        
        trend_window = tk.Toplevel(self.frame)
        trend_window.title("信号历史趋势")
        trend_window.geometry("1000x600")
        
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        angles_deg = [i * 30 for i in range(self.radar_directions)]
        
        for idx, ssid in enumerate(self.selected_ssids[:5]):
            if ssid in signals_data:
                values = signals_data[ssid]
                color = self.COLOR_BLIND_SAFE[idx % len(self.COLOR_BLIND_SAFE)]
                ax.plot(angles_deg, values, marker='o', label=ssid, 
                       color=color, linewidth=2)
        
        ax.set_xlabel('方向角度 (度)', fontsize=12)
        ax.set_ylabel('信号强度 (dBm)', fontsize=12)
        ax.set_title('WiFi信号12方向分布图', fontsize=14, fontweight='bold')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.axhline(y=-70, color='orange', linestyle='--', alpha=0.5)
        ax.axhline(y=-50, color='green', linestyle='--', alpha=0.5)
        ax.set_xticks(angles_deg)
        
        canvas = FigureCanvasTkAgg(fig, trend_window)
        canvas.get_tk_widget().pack(fill='both', expand=True)
        canvas.draw()
    
    def _export_diagnostic_report(self):
        """导出诊断报告"""
        if not self.scanned_networks:
            messagebox.showwarning("提示", "请先扫描WiFi网络")
            return
        
        export_format = messagebox.askquestion("选择格式", 
                                               "导出为PDF？\n点击'否'导出为TXT")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if export_format == 'yes':
            try:
                from reportlab.lib.pagesizes import A4
                from reportlab.pdfgen import canvas
                from reportlab.pdfbase import pdfmetrics
                from reportlab.pdfbase.ttfonts import TTFont
            except ImportError:
                messagebox.showerror("缺失依赖", 
                                   "PDF导出功能需要安装reportlab库\n\n"
                                   "安装命令: pip install reportlab")
                return
            
            try:
                filename = f"WiFi诊断报告_v1.4_{timestamp}.pdf"
                pdf = canvas.Canvas(filename, pagesize=A4)
                
                try:
                    pdfmetrics.registerFont(TTFont('SimSun', 'simsun.ttc'))
                    pdf.setFont('SimSun', 12)
                except (OSError, IOError):
                    pdf.setFont('Helvetica', 12)
                
                y = 800
                pdf.drawString(100, y, f"WiFi Network Diagnostic Report v1.4")
                y -= 20
                pdf.drawString(100, y, f"Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                y -= 30
                
                for idx, net in enumerate(self.scanned_networks[:30], 1):
                    if y < 100:
                        pdf.showPage()
                        y = 800
                    
                    signal_percent = net.get('signal_percent', 0)
                    if isinstance(signal_percent, str):
                        signal_percent = int(signal_percent.rstrip('%'))
                    
                    line = f"{idx}. SSID:{net.get('ssid', 'N/A')} | Signal:{signal_percent}% | Channel:{net.get('channel', 'N/A')} | Band:{net.get('band', 'N/A')}"
                    pdf.drawString(100, y, line)
                    y -= 20
                
                pdf.save()
                messagebox.showinfo("成功", f"报告已保存: {filename}")
            
            except Exception as e:
                messagebox.showerror("错误", f"PDF导出失败: {str(e)}")
        
        else:
            filename = f"WiFi诊断报告_v1.4_{timestamp}.txt"
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("="*60 + "\n")
                    f.write("WiFi网络诊断报告 v1.4\n")
                    f.write("="*60 + "\n")
                    f.write(f"扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"网络数量: {len(self.scanned_networks)}\n\n")
                    
                    band_stats = {'2.4GHz': 0, '5GHz': 0, '6GHz': 0}
                    for net in self.scanned_networks:
                        band = net.get('band', 'N/A')
                        if band in band_stats:
                            band_stats[band] += 1
                    
                    f.write("频段分布:\n")
                    f.write(f"  2.4GHz: {band_stats['2.4GHz']} 个\n")
                    f.write(f"  5GHz: {band_stats['5GHz']} 个\n")
                    f.write(f"  6GHz: {band_stats['6GHz']} 个\n\n")
                    
                    f.write("="*60 + "\n")
                    f.write("详细网络列表\n")
                    f.write("="*60 + "\n\n")
                    
                    for idx, net in enumerate(self.scanned_networks, 1):
                        signal_percent = net.get('signal_percent', 0)
                        if isinstance(signal_percent, str):
                            signal_percent = int(signal_percent.rstrip('%'))
                        
                        signal_dbm = -100 + (signal_percent * 0.7) if signal_percent > 0 else -100
                        
                        f.write(f"[{idx}] {net.get('ssid', 'N/A')}\n")
                        f.write(f"    信号强度: {signal_percent}% ({signal_dbm:.0f} dBm)\n")
                        f.write(f"    BSSID: {net.get('bssid', 'N/A')}\n")
                        f.write(f"    信道: {net.get('channel', 'N/A')}\n")
                        f.write(f"    频段: {net.get('band', 'N/A')}\n")
                        f.write(f"    WiFi标准: {net.get('wifi_standard', 'N/A')}\n")
                        f.write(f"    加密方式: {net.get('authentication', 'N/A')}\n")
                        f.write(f"    厂商: {net.get('vendor', '未知')}\n")
                        f.write("\n")
                
                messagebox.showinfo("成功", f"报告已保存: {filename}")
            
            except Exception as e:
                messagebox.showerror("错误", f"TXT导出失败: {str(e)}")
    
    def get_frame(self):
        """获取框架"""
        return self.frame

    def _show_signal_compass(self):
        """方案A: 显示信号强度罗盘 - RSSI方向提示"""
        try:
            import tkinter.simpledialog as simpledialog
            
            # 检查是否有扫描数据
            if not self.scanned_networks:
                messagebox.showwarning("提示", "请先扫描WiFi网络！")
                return
            
            # 选择要分析的WiFi
            ssid_list = [net.get('ssid', '未知') for net in self.scanned_networks if net.get('ssid')]
            if not ssid_list:
                messagebox.showwarning("提示", "没有可用的WiFi网络")
                return
            
            # 创建选择对话框
            compass_window = tk.Toplevel(self.parent)
            compass_window.title("🧭 WiFi信号罗盘 - 方向提示工具 v1.5")
            compass_window.geometry("1300x820")
            compass_window.resizable(True, True)
            
            # 说明文字
            info_frame = ttk.Frame(compass_window)
            info_frame.pack(fill='x', padx=20, pady=15)
            
            ttk.Label(info_frame, text="📡 WiFi信号方向提示工具", 
                     font=('Microsoft YaHei', 13, 'bold')).pack(anchor='w', pady=(0, 8))
            ttk.Label(info_frame, text="原理：记录您旋转360°时各方向的信号强度（RSSI），推算AP大致方向", 
                     font=('Microsoft YaHei', 10), foreground='#666').pack(anchor='w', pady=3)
            ttk.Label(info_frame, text="精度：±30-60° (参考级别，受墙壁、反射、多径效应影响)", 
                     font=('Microsoft YaHei', 10), foreground='#dc3545').pack(anchor='w', pady=3)
            ttk.Label(info_frame, text="使用方法：1) 选择WiFi  2) 设置采样频率  3) 开始扫描  4) 慢慢旋转360°  5) 查看信号方向分布", 
                     font=('Microsoft YaHei', 10), foreground='#28a745').pack(anchor='w', pady=3)
            
            # 控制区
            control_frame = ttk.Frame(compass_window)
            control_frame.pack(fill='x', padx=20, pady=10)
            
            ttk.Label(control_frame, text="目标WiFi:", font=('Microsoft YaHei', 11, 'bold')).pack(side='left', padx=(0, 10))
            target_var = tk.StringVar(value=ssid_list[0])
            target_combo = ttk.Combobox(control_frame, textvariable=target_var, 
                                       values=ssid_list, width=50, state='readonly')
            target_combo.pack(side='left', padx=5)
            
            # 采样频率控制
            ttk.Label(control_frame, text="采样频率:", font=('Microsoft YaHei', 10)).pack(side='left', padx=(15, 5))
            sample_interval_var = tk.StringVar(value="1秒")
            interval_combo = ttk.Combobox(control_frame, textvariable=sample_interval_var,
                                         values=["0.5秒", "1秒", "2秒", "3秒", "5秒"], 
                                         width=8, state='readonly')
            interval_combo.pack(side='left', padx=5)
            
            # 扫描控制
            scan_active = {
                'running': False, 
                'direction_data': {}, 
                'current_angle': 0,
                'sample_count': 0  # 采样计数器
            }
            
            def start_compass_scan():
                """开始罗盘扫描"""
                if scan_active['running']:
                    messagebox.showwarning("提示", "扫描正在进行中")
                    return
                
                scan_active['running'] = True
                scan_active['direction_data'] = {}
                scan_active['current_angle'] = 0
                scan_active['sample_count'] = 0
                start_btn.config(state='disabled')
                stop_btn.config(state='normal')
                status_label.config(text="🔄 正在扫描... 请慢慢顺时针旋转360°", foreground='#28a745')
                
                def scan_loop():
                    if not scan_active['running']:
                        return
                    
                    # 扫描当前方向
                    target_ssid = target_var.get()
                    current_signal = -100
                    
                    # 执行快速扫描
                    try:
                        result = subprocess.run(
                            ['netsh', 'wlan', 'show', 'networks', 'mode=bssid'],
                            capture_output=True, timeout=3,
                            creationflags=CREATE_NO_WINDOW
                        )
                        
                        # 安全解码输出
                        if result.stdout:
                            try:
                                output_text = result.stdout.decode('gbk', errors='ignore')
                            except Exception as e:  # P2修复: 指定异常类型
                                output_text = result.stdout.decode('utf-8', errors='ignore')
                        else:
                            output_text = ""
                        
                        # 解析目标WiFi信号
                        if output_text:
                            lines = output_text.split('\n')
                            for i, line in enumerate(lines):
                                if target_ssid in line and 'SSID' in line:
                                    # 找到信号强度
                                    for j in range(i, min(i+10, len(lines))):
                                        if '信号' in lines[j] or 'Signal' in lines[j]:
                                            signal_match = re.search(r'(\d+)%', lines[j])
                                            if signal_match:
                                                signal_percent = int(signal_match.group(1))
                                                current_signal = -100 + (signal_percent * 0.7)
                                                break
                                    break
                    except Exception as e:
                        print(f"扫描错误: {e}")
                    
                    # 记录数据（基于北向参考的相对角度）
                    scan_active['sample_count'] += 1
                    relative_angle = scan_active['current_angle']  # 相对于北向的角度
                    
                    # 将角度标准化到12个方位（每30度一个）
                    sector_angle = round(relative_angle / 30) * 30
                    sector_angle = sector_angle % 360  # 确保在0-359范围内
                    
                    if sector_angle not in scan_active['direction_data']:
                        scan_active['direction_data'][sector_angle] = []
                    scan_active['direction_data'][sector_angle].append(current_signal)
                    
                    # 计算当前方位（相对于北向）
                    direction_name = get_direction_name(relative_angle)
                    
                    # 优化2: 更新实时状态面板
                    info_labels['direction'].config(
                        text=f"{direction_name} ({relative_angle}°)",
                        foreground='#007bff'
                    )
                    
                    # 信号强度着色（优化3: 分级着色）
                    if current_signal >= -50:
                        signal_color = '#00CC00'  # 优秀
                        signal_bar = '●●●●●'
                    elif current_signal >= -60:
                        signal_color = '#66FF66'  # 良好
                        signal_bar = '●●●●○'
                    elif current_signal >= -70:
                        signal_color = '#FF9900'  # 中等
                        signal_bar = '●●●○○'
                    elif current_signal >= -80:
                        signal_color = '#FF3300'  # 较弱
                        signal_bar = '●●○○○'
                    else:
                        signal_color = '#CC0000'  # 很弱
                        signal_bar = '●○○○○'
                    
                    info_labels['signal'].config(
                        text=f"{current_signal:.1f} dBm {signal_bar}",
                        foreground=signal_color
                    )
                    
                    info_labels['samples'].config(text=f"{scan_active['sample_count']} 次")
                    
                    # 计算覆盖角度
                    if scan_active['direction_data']:
                        angles = list(scan_active['direction_data'].keys())
                        coverage = max(angles) - min(angles)
                        info_labels['coverage'].config(text=f"{coverage}°")
                    
                    # 实时显示取样数据
                    status_label.config(text=f"🔄 扫描中... 已采样: {scan_active['sample_count']} 次 | 当前方位: {direction_name} ({relative_angle}°) | 信号: {current_signal:.1f} dBm")
                    
                    # 更新结果文本显示实时数据
                    if scan_active['sample_count'] % 5 == 0:  # 每5次更新一次，避免频繁刷新
                        result_text.delete('1.0', 'end')
                        result_text.insert('end', f"📡 实时采样数据\n{'='*50}\n\n")
                        result_text.insert('end', f"目标WiFi: {target_var.get()}\n")
                        result_text.insert('end', f"总采样次数: {scan_active['sample_count']}\n\n")
                        result_text.insert('end', "最近10次采样:\n")
                        
                        # 显示最近的采样数据（按采样顺序）
                        all_samples = []
                        for ang in sorted(scan_active['direction_data'].keys()):
                            for sig in scan_active['direction_data'][ang]:
                                all_samples.append((ang, sig))
                        
                        for i, (ang, sig) in enumerate(all_samples[-10:], 1):
                            dir_name = get_direction_name(ang)
                            result_text.insert('end', f"  [{i}] {dir_name} ({ang}°) → {sig:.1f} dBm\n")
                        
                        result_text.insert('end', f"\n💡 提示: 红色箭头指向最强信号方向...\n")
                    
                    # 更新显示
                    update_compass_display()
                    
                    # 获取采样间隔
                    interval_text = sample_interval_var.get()
                    interval_ms = int(float(interval_text.replace('秒', '')) * 1000)
                    
                    # 继续扫描
                    after_id = compass_window.after(interval_ms, scan_loop)
                    # 将罗盘窗口的定时器也记录下来
                    if hasattr(self, 'compass_after_ids'):
                        self.compass_after_ids.append(after_id)
                    else:
                        self.compass_after_ids = [after_id]
                
                scan_loop()
            
            def stop_compass_scan():
                """停止扫描"""
                scan_active['running'] = False
                start_btn.config(state='normal')
                stop_btn.config(state='disabled')
                status_label.config(text="✅ 扫描完成", foreground='#007bff')
                
                # 分析数据
                analyze_direction_data()
            
            def get_direction_name(angle):
                """根据角度获取方位名称"""
                # 标准化角度到0-360
                angle = angle % 360
                
                # 12方位系统（每30度一个方位）
                directions = [
                    "正北", "北偏东", "东北", "东偏北",
                    "正东", "东偏南", "东南", "南偏东",
                    "正南", "南偏西", "西南", "西偏南",
                    "正西", "西偏北", "西北", "北偏西"
                ]
                
                # 计算方位索引（每22.5度一个方位）
                index = int((angle + 11.25) / 22.5) % 16
                return directions[index]
            
            def update_compass_display():
                """更新罗盘显示 - 箭头指向最强信号"""
                try:
                    compass_fig.clear()
                    ax = compass_fig.add_subplot(111, projection='polar')
                    
                    # 设置方向（顺时针，0度在顶部）
                    ax.set_theta_direction(-1)
                    ax.set_theta_zero_location('N')
                    
                    # 绘制已扫描的数据
                    angles = []
                    signals = []
                    angle_signal_map = {}  # 记录角度-信号对应关系
                    
                    for angle in sorted(scan_active['direction_data'].keys()):
                        avg_signal = np.mean(scan_active['direction_data'][angle])
                        angles.append(np.deg2rad(angle))
                        signals.append(avg_signal)
                        angle_signal_map[angle] = avg_signal
                    
                    if angles:
                        # 闭合曲线
                        angles.append(angles[0])
                        signals.append(signals[0])
                        
                        # 绘制信号强度曲线
                        ax.plot(angles, signals, 'b-', linewidth=2.5, label='信号强度', zorder=5)
                        ax.fill(angles, signals, alpha=0.25, color='blue', zorder=4)
                        
                        # 找出最强信号方向
                        max_idx = signals[:-1].index(max(signals[:-1]))
                        max_angle = angles[max_idx]
                        max_signal = signals[max_idx]
                        max_angle_deg = np.rad2deg(max_angle)
                        direction_name = get_direction_name(max_angle_deg)
                        
                        # ===== 优化3: 信号点分级着色 =====
                        for angle, signal in angle_signal_map.items():
                            angle_rad = np.deg2rad(angle)
                            
                            # 根据信号强度确定颜色和大小
                            if signal >= -50:
                                point_color = '#00CC00'  # 优秀 - 深绿
                                point_size = 12
                            elif signal >= -60:
                                point_color = '#66FF66'  # 良好 - 浅绿
                                point_size = 10
                            elif signal >= -70:
                                point_color = '#FF9900'  # 中等 - 橙色
                                point_size = 10
                            elif signal >= -80:
                                point_color = '#FF3300'  # 较弱 - 红色
                                point_size = 8
                            else:
                                point_color = '#CC0000'  # 很弱 - 深红
                                point_size = 8
                            
                            # 标记采样点
                            ax.plot([angle_rad], [signal], 'o', 
                                   color=point_color, markersize=point_size, 
                                   markeredgecolor='white', markeredgewidth=1,
                                   zorder=6)
                            
                            # 智能标注：仅在最小值点显示，避免过度标注
                            is_min_point = (signal == min(angle_signal_map.values()))
                            # 跳过接近最强点的标注（±30度范围内）
                            angle_diff = abs(angle - np.rad2deg(max_angle)) % 360
                            if angle_diff > 180:
                                angle_diff = 360 - angle_diff
                            is_near_max = angle_diff < 30
                            
                            if is_min_point and not is_near_max:
                                # 最弱点向内偏移，避免与外圈重叠
                                label_offset = 6
                                label_r = signal + label_offset  # 始终向内
                                
                                # 显示信号强度数值
                                ax.text(angle_rad, label_r, f'{signal:.0f}', 
                                       ha='center', va='center',
                                       fontsize=6.5, fontweight='bold',
                                       color=point_color,
                                       bbox=dict(boxstyle='round,pad=0.15', 
                                               facecolor='white', 
                                               edgecolor=point_color, 
                                               alpha=0.8),
                                       zorder=7)
                        
                        # ===== 优化2: 增强指针显示（角度+强度标注） =====
                        # 指针从圆心指向最强信号方向（箭头根部在圆心，头部指向信号源）
                        # 注意：max_signal是负值（如-60），在极坐标中保持负值表示距离
                        pointer_end_r = max_signal * 0.92  # 指针终点半径（留出空间给星标）
                        
                        # 使用annotate绘制箭头，确保从圆心出发
                        # 绘制主指针（红色箭头）- 从圆心(-100)指向信号点
                        ax.annotate('', 
                                   xy=(max_angle, pointer_end_r),  # 箭头头部（信号点内侧）
                                   xytext=(max_angle, -100),  # 箭头尾部（圆心，Y轴最小值）
                                   arrowprops=dict(
                                       arrowstyle='-|>',
                                       color='red',
                                       lw=3.5,
                                       alpha=0.85,
                                       mutation_scale=20
                                   ),
                                   zorder=9)
                        
                        # 标记最强信号点（红色星形，减小尺寸）
                        ax.plot([max_angle], [max_signal], '*', 
                               color='red', markersize=18, 
                               markeredgecolor='darkred', markeredgewidth=1.5,
                               label=f'最强: {direction_name} ({max_angle_deg:.0f}°)',
                               zorder=10)
                        
                        # 优化：在最强点添加详细标注（放置在圆外侧，避免与数据重叠）
                        # 计算标注位置：如果在正北附近，向侧面偏移；否则向外偏移
                        if abs(max_angle_deg) < 45 or abs(max_angle_deg - 360) < 45:  # 正北±45度
                            # 向右侧偏移30度，避免与标题重叠
                            annotation_angle = max_angle + np.deg2rad(30)
                            annotation_r = -20 + 8
                        else:
                            # 直接向外偏移
                            annotation_angle = max_angle
                            annotation_r = -20 + 12
                        
                        annotation_text = f'★ {direction_name}\n{max_angle_deg:.0f}° | {max_signal:.1f}dBm'
                        ax.annotate(annotation_text, 
                                   xy=(max_angle, max_signal),  # 指向信号点
                                   xytext=(annotation_angle, annotation_r),  # 文字放在圆外
                                   ha='center', va='center',
                                   fontsize=7.5, fontweight='bold',
                                   color='darkred',
                                   bbox=dict(boxstyle='round,pad=0.35',
                                           facecolor='#FFFACD',  # 浅黄色
                                           edgecolor='red',
                                           linewidth=1.2,
                                           alpha=0.88),
                                   arrowprops=dict(arrowstyle='->', 
                                                  color='red', 
                                                  lw=1.2,
                                                  alpha=0.65),
                                   zorder=11)
                    
                    ax.set_ylim(-100, -10)  # 扩大外圈范围，为外部标注留空间
                    title_text = f'WiFi信号方位罗盘\n目标: {target_var.get()}'
                    ax.set_title(title_text, fontsize=11, pad=20, fontweight='bold')
                    ax.legend(loc='upper left', bbox_to_anchor=(-0.15, 1.08), fontsize=8, framealpha=0.9)
                    ax.grid(True, alpha=0.3, linestyle='--')
                    
                    compass_canvas.draw_idle()
                except Exception as e:
                    print(f"罗盘显示错误: {e}")
            
            def analyze_direction_data():
                """分析方向数据，给出建议（基于北向参考）"""
                if not scan_active['direction_data']:
                    result_text.delete('1.0', 'end')
                    result_text.insert('end', "⚠ 没有扫描数据\n")
                    return
                
                # 计算每个方向的平均信号
                direction_avg = {}
                for angle, signals in scan_active['direction_data'].items():
                    direction_avg[angle] = np.mean(signals)
                
                # 找出最强和最弱方向
                best_angle = max(direction_avg.items(), key=lambda x: x[1])
                worst_angle = min(direction_avg.items(), key=lambda x: x[1])
                
                # 计算方位名称
                best_direction = get_direction_name(best_angle[0])
                worst_direction = get_direction_name(worst_angle[0])
                
                # 计算信号范围
                signal_range = best_angle[1] - worst_angle[1]
                
                # 生成报告
                result_text.delete('1.0', 'end')
                result_text.insert('end', f"📊 WiFi信号方位分析报告\n{'='*55}\n\n")
                result_text.insert('end', f"目标WiFi: {target_var.get()}\n")
                result_text.insert('end', f"扫描方位数: {len(direction_avg)} 个\n")
                result_text.insert('end', f"总采样次数: {scan_active['sample_count']}\n\n")
                
                result_text.insert('end', f"🎯 推荐方向:\n")
                result_text.insert('end', f"   最强: {best_direction} ({best_angle[0]}°) → {best_angle[1]:.1f} dBm\n", 'highlight')
                result_text.insert('end', f"   最弱: {worst_direction} ({worst_angle[0]}°) → {worst_angle[1]:.1f} dBm\n")
                result_text.insert('end', f"   信号差异: {signal_range:.1f} dB\n\n")
                
                result_text.insert('end', f"💡 建议:\n")
                if best_angle[1] > -50:
                    result_text.insert('end', f"   ✅ 信号很强，AP可能在{best_direction}方向约50米内\n")
                elif best_angle[1] > -70:
                    result_text.insert('end', f"   ✓ 信号良好，AP可能在{best_direction}方向约100米内\n")
                else:
                    result_text.insert('end', f"   ⚠ 信号较弱，AP可能较远或有遮挡\n")
                
                # 测向精度评估
                result_text.insert('end', f"\n📍 测向精度评估:\n")
                if signal_range > 20:
                    result_text.insert('end', "   ✅ 信号差异大，方向性明显，精度高（±30°）\n")
                elif signal_range > 10:
                    result_text.insert('end', "   ✓ 信号差异中等，有一定方向性（±45°）\n")
                else:
                    result_text.insert('end', "   ⚠ 信号差异小，可能有多径干扰或全向天线（±60°）\n")
                
                result_text.insert('end', f"\n📝 注意事项:\n")
                result_text.insert('end', "   • 方向精度: ±30-60°（受墙壁、反射、多径效应影响）\n")
                result_text.insert('end', "   • 室内环境下，反射信号可能干扰测向精度\n")
                result_text.insert('end', "   • 建议在空旷环境或室外测试以获得更准确结果\n")
                result_text.insert('end', "   • 方向角度为相对方向，以开始扫描位置为0°基准\n")
                
                # 显示所有方位数据
                result_text.insert('end', f"\n📊 所有方位数据（按信号强度排序）:\n")
                result_text.insert('end', f"{'='*55}\n")
                
                # 按信号强度排序
                sorted_directions = sorted(direction_avg.items(), key=lambda x: x[1], reverse=True)
                
                for i, (angle, signal) in enumerate(sorted_directions, 1):
                    dir_name = get_direction_name(angle)
                    samples = len(scan_active['direction_data'][angle])
                    
                    # 信号强度条
                    bar_length = int((signal + 100) / 2)  # -100到-20 映射到 0-40
                    bar = '█' * max(0, bar_length)
                    
                    if i == 1:
                        result_text.insert('end', f"  🥇 {dir_name:8s} ({angle:3d}°) {signal:6.1f} dBm {bar} [{samples}次]\n")
                    elif i == len(sorted_directions):
                        result_text.insert('end', f"  ❌ {dir_name:8s} ({angle:3d}°) {signal:6.1f} dBm {bar} [{samples}次]\n")
                    else:
                        result_text.insert('end', f"     {dir_name:8s} ({angle:3d}°) {signal:6.1f} dBm {bar} [{samples}次]\n")
                
                result_text.insert('end', f"\n🔍 算法说明:\n")
                result_text.insert('end', "   1. 将360°分为12个方位扇区（每30°）\n")
                result_text.insert('end', "   2. 每个方位多次采样取平均值，减少随机误差\n")
                result_text.insert('end', "   3. 基于信号强度差异评估测向可靠性\n")
                result_text.insert('end', "   4. 起始位置作为0°基准，顺时针旋转增加\n")
            
            # 按钮区
            button_frame = ttk.Frame(compass_window)
            button_frame.pack(fill='x', padx=15, pady=10)
            
            start_btn = ModernButton(button_frame, text="▶ 开始扫描", 
                                    command=start_compass_scan, style='success')
            start_btn.pack(side='left', padx=8)
            
            stop_btn = ModernButton(button_frame, text="⏹ 停止", 
                                   command=stop_compass_scan, style='danger')
            stop_btn.pack(side='left', padx=8)
            stop_btn.config(state='disabled')
            
            status_label = ttk.Label(button_frame, text="⏳ 准备就绪", 
                                    font=('Microsoft YaHei', 10), foreground='#666')
            status_label.pack(side='left', padx=20)
            
            # 罗盘显示区
            display_frame = ttk.Frame(compass_window)
            display_frame.pack(fill='both', expand=True, padx=15, pady=10)
            
            # 左侧：WiFi罗盘图（大面积显示）
            left_frame = ttk.Frame(display_frame)
            left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
            
            # 右侧：信息面板垂直排列（网络信息 + 扫描状态 + 分析结果）
            right_frame = ttk.Frame(display_frame)
            right_frame.pack(side='right', fill='both', padx=(10, 0))
            
            # WiFi信息面板（优化1: 显示详细网络信息）
            info_panel = ttk.LabelFrame(right_frame, text="🎯 目标网络信息", padding=15)
            info_panel.pack(fill='x', pady=(0, 10))
            
            # 获取目标网络详细信息
            def get_target_network_info():
                """获取当前选中WiFi的详细信息"""
                target_ssid = target_var.get()
                for net in self.scanned_networks:
                    if net.get('ssid') == target_ssid:
                        return net
                return {}
            
            # 信息标签容器
            info_labels = {}
            info_grid = ttk.Frame(info_panel)
            info_grid.pack(fill='x')
            
            # SSID
            ttk.Label(info_grid, text="SSID:", font=('Microsoft YaHei', 10, 'bold')).grid(row=0, column=0, sticky='w', pady=4, padx=(0, 10))
            info_labels['ssid'] = ttk.Label(info_grid, text=target_var.get(), font=('Consolas', 10), foreground='#007bff')
            info_labels['ssid'].grid(row=0, column=1, sticky='w', padx=8, pady=4)
            
            # BSSID
            ttk.Label(info_grid, text="BSSID:", font=('Microsoft YaHei', 10, 'bold')).grid(row=1, column=0, sticky='w', pady=4, padx=(0, 10))
            info_labels['bssid'] = ttk.Label(info_grid, text="--", font=('Consolas', 10))
            info_labels['bssid'].grid(row=1, column=1, sticky='w', padx=8, pady=4)
            
            # 频段和信道
            ttk.Label(info_grid, text="频段:", font=('Microsoft YaHei', 10, 'bold')).grid(row=2, column=0, sticky='w', pady=4, padx=(0, 10))
            info_labels['band'] = ttk.Label(info_grid, text="--", font=('Consolas', 10))
            info_labels['band'].grid(row=2, column=1, sticky='w', padx=8, pady=4)
            
            # 加密方式
            ttk.Label(info_grid, text="加密:", font=('Microsoft YaHei', 10, 'bold')).grid(row=3, column=0, sticky='w', pady=4, padx=(0, 10))
            info_labels['auth'] = ttk.Label(info_grid, text="--", font=('Consolas', 10))
            info_labels['auth'].grid(row=3, column=1, sticky='w', padx=8, pady=4)
            
            # 当前扫描状态面板
            status_panel = ttk.LabelFrame(right_frame, text="📊 当前扫描状态", padding=15)
            status_panel.pack(fill='x', pady=(0, 10))
            
            status_grid = ttk.Frame(status_panel)
            status_grid.pack(fill='x')
            
            # 当前方位
            ttk.Label(status_grid, text="当前方位:", font=('Microsoft YaHei', 11, 'bold')).grid(row=0, column=0, sticky='w', pady=5, padx=(0, 15))
            info_labels['direction'] = ttk.Label(status_grid, text="准备中", font=('Consolas', 11), foreground='#666')
            info_labels['direction'].grid(row=0, column=1, sticky='w', padx=10, pady=5)
            
            # 实时信号
            ttk.Label(status_grid, text="实时信号:", font=('Microsoft YaHei', 11, 'bold')).grid(row=1, column=0, sticky='w', pady=5, padx=(0, 15))
            info_labels['signal'] = ttk.Label(status_grid, text="-- dBm", font=('Consolas', 11))
            info_labels['signal'].grid(row=1, column=1, sticky='w', padx=10, pady=5)
            
            # 已采样次数
            ttk.Label(status_grid, text="已采样:", font=('Microsoft YaHei', 11, 'bold')).grid(row=2, column=0, sticky='w', pady=5, padx=(0, 15))
            info_labels['samples'] = ttk.Label(status_grid, text="0 次", font=('Consolas', 11))
            info_labels['samples'].grid(row=2, column=1, sticky='w', padx=10, pady=5)
            
            # 覆盖角度
            ttk.Label(status_grid, text="覆盖角度:", font=('Microsoft YaHei', 11, 'bold')).grid(row=3, column=0, sticky='w', pady=5, padx=(0, 15))
            info_labels['coverage'] = ttk.Label(status_grid, text="0°", font=('Consolas', 11))
            info_labels['coverage'].grid(row=3, column=1, sticky='w', padx=10, pady=5)
            
            # 更新WiFi信息
            def update_wifi_info():
                """更新WiFi网络信息"""
                net = get_target_network_info()
                if net:
                    info_labels['ssid'].config(text=net.get('ssid', '--'))
                    info_labels['bssid'].config(text=net.get('bssid', '--'))
                    
                    # 频段和信道
                    channel = net.get('channel', '--')
                    if channel and channel != '--':
                        try:
                            ch_num = int(channel)
                            if ch_num <= 14:
                                band_text = f"2.4GHz (信道 {ch_num})"
                            else:
                                band_text = f"5GHz (信道 {ch_num})"
                        except Exception as e:  # P2修复: 指定异常类型
                            band_text = f"信道 {channel}"
                    else:
                        band_text = "--"
                    info_labels['band'].config(text=band_text)
                    
                    # 加密方式
                    auth = net.get('authentication', '--')
                    info_labels['auth'].config(text=auth)
            
            update_wifi_info()
            
            # 罗盘图（左侧主显示区）
            compass_fig = Figure(figsize=(8, 7), dpi=100)
            compass_canvas = FigureCanvasTkAgg(compass_fig, left_frame)
            compass_canvas.get_tk_widget().pack(fill='both', expand=True)
            
            # 初始化空罗盘
            ax = compass_fig.add_subplot(111, projection='polar')
            ax.set_theta_direction(-1)
            ax.set_theta_zero_location('N')
            ax.set_ylim(-100, -20)
            ax.set_title('等待开始扫描...', fontsize=12, pad=20)
            ax.grid(True)
            compass_canvas.draw()
            
            # 分析结果面板（右侧底部，可扩展）
            result_frame = ttk.LabelFrame(right_frame, text="📋 分析结果", padding=12)
            result_frame.pack(fill='both', expand=True)
            
            result_text = scrolledtext.ScrolledText(result_frame, height=15, width=38,
                                                   font=('Consolas', 9), wrap='word')
            result_text.pack(fill='both', expand=True)
            result_text.tag_config('highlight', foreground='#dc3545', font=('Consolas', 9, 'bold'))
            
            result_text.insert('end', "等待扫描数据...\n\n")
            result_text.insert('end', "使用说明：\n")
            result_text.insert('end', "1. 选择要定位的WiFi网络\n")
            result_text.insert('end', "2. 点击'开始扫描'\n")
            result_text.insert('end', "3. 保持设备水平，慢慢旋转360°\n")
            result_text.insert('end', "4. 完成一圈后点击'停止'\n")
            result_text.insert('end', "5. 查看推荐方向\n\n")
            result_text.insert('end', "⚠ 此功能基于RSSI值推测方向\n")
            result_text.insert('end', "精度受环境影响，仅供参考！\n")
            
        except Exception as e:
            messagebox.showerror("错误", f"信号罗盘启动失败: {str(e)}")

    def _get_parent(self):
        """安全获取parent - P1修复"""
        if self.parent_ref:
            parent = self.parent_ref()
            if parent is None:
                raise RuntimeError("Parent窗口已被销毁")
            return parent
        return self.parent
    def cleanup(self):
        """清理资源 - P1修复：防止内存泄漏"""
        print("[清理] 开始清理NetworkOverviewTab资源...")
        
        # 停止监控
        if self.monitoring:
            self.monitoring = False
            print("[清理] 已停止WiFi监控")
        
        # 取消所有定时器
        cancelled_count = 0
        for after_id in self.after_ids:
            try:
                self.parent.after_cancel(after_id)
                cancelled_count += 1
            except Exception as e:
                print('[警告] 操作失败但已忽略')  # P2修复: 添加日志
        
        if cancelled_count > 0:
            print(f"[清理] 已取消 {cancelled_count} 个定时器")
        
        self.after_ids.clear()
        
        # 清理数据结构
        if hasattr(self, 'wifi_signals'):
            self.wifi_signals.clear()
        if hasattr(self, 'wifi_colors'):
            self.wifi_colors.clear()
        
        print("[清理] NetworkOverviewTab资源清理完成")

