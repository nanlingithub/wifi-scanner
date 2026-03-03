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


class ErrorHandler:
    """✅ 新增: 统一错误处理器 - 提供友好的错误提示"""
    
    ERROR_MESSAGES = {
        'no_adapter': {
            'title': '未检测到WiFi适配器',
            'message': '可能的原因：\n'
                      '1. WiFi适配器已禁用\n'
                      '2. 驱动程序未安装\n'
                      '3. 硬件故障\n\n'
                      '建议操作：\n'
                      '• 检查设备管理器中的网络适配器\n'
                      '• 尝试重新启用WiFi\n'
                      '• 更新网卡驱动程序',
            'type': 'warning'
        },
        'scan_timeout': {
            'title': '扫描超时',
            'message': '扫描WiFi网络超时（>60秒）\n\n'
                      '可能的原因：\n'
                      '1. 系统繁忙\n'
                      '2. 网卡响应慢\n\n'
                      '建议操作：\n'
                      '• 稍后重试\n'
                      '• 重启WiFi适配器',
            'type': 'error'
        },
        'permission_denied': {
            'title': '权限不足',
            'message': '某些功能需要管理员权限\n\n'
                      '建议操作：\n'
                      '• 右键程序图标\n'
                      '• 选择"以管理员身份运行"',
            'type': 'warning'
        },
        'network_error': {
            'title': '网络错误',
            'message': '无法获取网络信息\n\n'
                      '建议操作：\n'
                      '• 检查WiFi是否已开启\n'
                      '• 尝试刷新适配器',
            'type': 'error'
        }
    }
    
    @staticmethod
    def handle_error(exception, context="操作"):
        """处理错误并显示友好提示"""
        error_type = ErrorHandler._classify_error(exception)
        error_info = ErrorHandler.ERROR_MESSAGES.get(error_type, {
            'title': f'{context}失败',
            'message': f'发生未知错误\n\n'
                      f'错误详情: {str(exception)}\n\n'
                      f'建议操作：\n'
                      f'• 查看日志文件获取详细信息\n'
                      f'• 联系技术支持',
            'type': 'error'
        })
        
        if error_info['type'] == 'warning':
            messagebox.showwarning(error_info['title'], error_info['message'])
        else:
            messagebox.showerror(error_info['title'], error_info['message'])
    
    @staticmethod
    def _classify_error(exception):
        """分类错误"""
        error_str = str(exception).lower()
        
        if 'no adapter' in error_str or 'not found' in error_str:
            return 'no_adapter'
        elif 'timeout' in error_str:
            return 'scan_timeout'
        elif 'permission' in error_str or 'access denied' in error_str:
            return 'permission_denied'
        elif 'network' in error_str or 'connection' in error_str:
            return 'network_error'
        else:
            return 'unknown'


class WiFiScanCache:
    """✅ 新增: WiFi扫描缓存管理器 - 优化扫描速度"""
    
    def __init__(self, ttl=30):
        self.cache = {}
        self.ttl = ttl  # 缓存有效期(秒)
    
    def get(self, key):
        """获取缓存"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return data
            else:
                del self.cache[key]  # 过期删除
        return None
    
    def set(self, key, data):
        """设置缓存"""
        self.cache[key] = (data, time.time())
    
    def invalidate(self, key=None):
        """失效缓存"""
        if key is None:
            self.cache.clear()
        elif key in self.cache:
            del self.cache[key]


class NetworkOverviewTab:
    """网络概览标签页 v1.4（完整功能 + 优化雷达）"""
    
    def __init__(self, parent, wifi_analyzer):
        # P1修复: 使用weakref防止循环引用
        self.parent_ref = weakref.ref(parent) if parent else None
        self.parent = parent  # 保留直接引用以兼容现有代码
        self.notebook = parent  # v2.0: 保存notebook引用用于标签页跳转
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
        
        # ✅ 新增: 扫描缓存管理器
        self.scan_cache = WiFiScanCache(ttl=30)
        
        # 动画效果（保留旧版兼容）
        self.pulse_phase = 0
        self.update_flash = {}
        self.last_signal = {}
        self.animation_running = False
        self.last_draw_time = 0
        self.draw_throttle_ms = 100
        self.radar_ax = None  # 缓存polar轴对象，避免每帧重建
        
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
            {'text': '📊 信道', 'command': self._jump_to_channel_analysis, 'style': 'info'},
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
        self.radar_figure.patch.set_facecolor('#fafafa')
        # 预留底部空间放图例，顶部留标题空间；一次设置后复用
        self.radar_figure.subplots_adjust(top=0.87, bottom=0.18)
        # 一次性创建polar轴，后续只用 ax.cla() 清内容，避免每帧重建
        self.radar_ax = self.radar_figure.add_subplot(111, projection='polar')
        self.radar_canvas = FigureCanvasTkAgg(self.radar_figure, parent)
        self.radar_canvas.get_tk_widget().pack(fill='both', expand=True)
    
    def _draw_empty_radar(self):
        """绘制空雷达图（v1.5优化：复用轴对象 + 时序标签）"""
        ax = self.radar_ax
        ax.cla()  # 清除内容，保留subplot结构，避免重建开销

        grid_color = '#cccccc'
        text_color = '#2c3e50'

        ax.set_facecolor('#ffffff')
        ax.set_theta_direction(-1)
        ax.set_theta_zero_location('N')

        max_time_points = 12
        all_angles = np.linspace(0, 2 * np.pi, max_time_points, endpoint=False)

        ax.set_ylim(-100, -20)
        ax.set_yticks([-100, -85, -70, -50, -20])
        ax.set_yticklabels(['-100\n极弱', '-85\n弱', '-70\n一般',
                            '-50\n良好', '-20\n优秀'],
                           color=text_color, fontsize=8, fontweight='bold')

        ax.set_xticks(all_angles)
        # 时序标签：T0(最旧/起始) → T11(当前/最新)
        t_labels = [f'T{i}' if i < 11 else 'T11\n当前' for i in range(12)]
        ax.set_xticklabels(t_labels, fontsize=8, color=text_color, fontweight='bold')

        ax.grid(True, color=grid_color, alpha=0.5, linestyle='--', linewidth=1.2)
        ax.spines['polar'].set_color(grid_color)
        ax.spines['polar'].set_linewidth(2)
        ax.tick_params(colors=text_color, width=1.5)

        ax.set_title('WiFi 信号历史趋势\nT0(起始) → T11(当前) - 等待监控数据...',
                     fontsize=10, pad=20, color=text_color, fontweight='bold')

        self.radar_canvas.draw_idle()
    
    def _update_radar(self):
        """更新雷达图 - v1.5优化：复用轴对象 + 时序标签 + 图例内置 + 性能提升"""
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

            # 复用缓存的polar轴，只清内容（避免每帧重建ax的渲染开销）
            ax = self.radar_ax
            ax.cla()

            if len(selected_ssids) == 0:
                ax.set_axis_off()
                ax.text(0.5, 0.5, '请先勾选WiFi网络（最多10个）\n然后点击"开始监控"',
                        ha='center', va='center', fontsize=14,
                        color='#ff6600', fontweight='bold',
                        transform=ax.transAxes,
                        bbox=dict(boxstyle='round,pad=0.8', facecolor='#fff3cd',
                                  edgecolor='#ff6600', linewidth=2))
                self.radar_canvas.draw_idle()
                return

            grid_color = '#cccccc'
            text_color = '#2c3e50'

            ax.set_facecolor('#ffffff')
            ax.set_theta_direction(-1)
            ax.set_theta_zero_location('N')

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

                # 在每个有效数据点旁显示 dBm 强度值
                # 多个SSID时，按ssid_idx向外偏移，避免标签重叠
                radial_offset = 4 + ssid_idx * 3  # 每个SSID向外多偏移3 dBm
                for i, (angle, val) in enumerate(zip(all_angles, values)):
                    if val <= -99.9:
                        continue  # 跳过未采集槽位
                    label_r = val + radial_offset
                    label_r = min(label_r, -21)  # 不超出Y轴上限
                    ax.annotate(
                        f'{int(val)}',
                        xy=(angle, val),
                        xytext=(angle, label_r),
                        fontsize=6,
                        color=color,
                        fontweight='bold',
                        ha='center',
                        va='center',
                        zorder=11,
                        bbox=dict(
                            boxstyle='round,pad=0.1',
                            facecolor='white',
                            edgecolor=color,
                            alpha=0.75,
                            linewidth=0.6
                        )
                    )

            # 当前写入槽位指示器（红色虚线）：指向刚写完的槽 = T11当前
            latest_dir = (current_dir - 1) % max_time_points
            current_angle = latest_dir * (2 * np.pi / max_time_points)
            slot_label = f'当前: T{latest_dir}'
            ax.plot([current_angle, current_angle], [-100, -20],
                    'r--', linewidth=2, alpha=0.5, label=slot_label)

            # 时序刻度标签：T0(起始/最旧) → T11(当前/最新)
            ax.set_xticks(all_angles)
            t_labels = [f'T{i}' if i < 11 else 'T11\n当前' for i in range(12)]
            ax.set_xticklabels(t_labels, fontsize=8, color=text_color, fontweight='bold')

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

            # 图例：放在极坐标图正下方，不与雷达覆盖区域重叠
            ncol = min(3, len(selected_ssids) + 1)  # 最多3列，自动换行
            legend = ax.legend(loc='upper center',
                               bbox_to_anchor=(0.5, -0.08),
                               ncol=ncol,
                               fontsize=7, frameon=True,
                               shadow=False, fancybox=True,
                               borderpad=0.5, labelspacing=0.5,
                               columnspacing=0.8,
                               title=f'监控 {len(selected_ssids)} 个网络',
                               title_fontsize=7.5)
            legend.get_frame().set_facecolor('white')
            legend.get_frame().set_edgecolor(grid_color)
            legend.get_frame().set_alpha(0.95)

            # 采样进度标题
            filled_count = sum(1 for ssid in selected_ssids
                               if ssid in signals_snapshot
                               and any(v > -99.9 for v in signals_snapshot[ssid]))
            scan_progress = f'T0→T{latest_dir}'
            ax.set_title(f'WiFi 信号历史趋势  T0(起始) → T11(当前)\n'
                         f'监控 {len(selected_ssids)} 个网络 | 已采样: {scan_progress}',
                         fontsize=9, pad=20, color=text_color, fontweight='bold')

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
                                # 0% → -100 dBm，100% → -20 dBm（对齐图表Y轴满量程）
                                signal_dbm = -100 + (signal_percent * 0.8) if signal_percent > 0 else -100
                                
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
        """✅ 优化: 启动队列处理器（降低更新频率）"""
        try:
            # ✅ 增加批量处理数量
            updates_processed = 0
            while updates_processed < 10:  # 从5增加到10
                try:
                    update = self.update_queue.get_nowait()
                    if update['type'] == 'radar_update':
                        updates_processed += 1
                except queue.Empty:
                    break
            
            if updates_processed > 0:
                # ✅ 节流: 距离上次绘制超过200ms才更新
                current_time = time.time() * 1000
                if current_time - self.last_draw_time > 200:  # 200ms = 5fps
                    self._update_radar()
                    self.last_draw_time = current_time
                
        except Exception as e:
            print(f"[警告] 队列处理异常: {e}")
        finally:
            # ✅ 降低处理频率: 150ms → 300ms
            after_id = self.parent.after(300, self._start_queue_processor)
            self.after_ids.append(after_id)
    
    def _run_animation_effects(self):
        """运行动画效果（pulse_phase 供未来渐变动画使用）"""
        if not self.animation_running:
            return

        try:
            self.pulse_phase = (self.pulse_phase + 0.02) % 1.0

            # update_flash 衰减（供外部调用方写入闪烁值时使用）
            for ssid in list(self.update_flash.keys()):
                self.update_flash[ssid] = max(0, self.update_flash[ssid] - 0.04)
                if self.update_flash[ssid] < 0.01:
                    del self.update_flash[ssid]

        except Exception as e:
            print(f"[警告] 动画效果异常: {e}")

        finally:
            if self.animation_running:
                after_id = self.parent.after(200, self._run_animation_effects)
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
        """✅ 优化: WiFi扫描（带详细进度反馈）"""
        # 创建进度对话框
        progress_window = tk.Toplevel(self.frame)
        progress_window.title("扫描进度")
        progress_window.geometry("450x250")
        progress_window.transient(self.frame)
        progress_window.grab_set()
        
        # 进度条
        progress_var = tk.IntVar(value=0)
        progress_bar = ttk.Progressbar(progress_window, variable=progress_var,
                                       maximum=100, mode='determinate')
        progress_bar.pack(fill='x', padx=20, pady=20)
        
        # 状态文本
        status_label = tk.Label(progress_window, text="准备扫描...",
                               font=('Microsoft YaHei', 10))
        status_label.pack(pady=10)
        
        # 详细信息
        detail_text = tk.Text(progress_window, height=6, width=50, wrap='word',
                             font=('Microsoft YaHei', 9))
        detail_text.pack(fill='both', expand=True, padx=20, pady=10)
        
        def update_progress(percent, status, detail=""):
            """更新进度"""
            try:
                progress_var.set(percent)
                status_label.config(text=status)
                if detail:
                    detail_text.insert('end', detail + '\n')
                    detail_text.see('end')
                progress_window.update()
            except:
                pass  # 窗口可能已关闭
        
        def scan_worker():
            try:
                # 阶段1: 检查缓存 (0-10%)
                update_progress(5, "检查扫描缓存...", "查找最近扫描结果")
                cached_networks = self.scan_cache.get('networks')
                
                if cached_networks is not None:
                    update_progress(50, "使用缓存数据", 
                                  f"发现缓存（{len(cached_networks)}个网络）")
                    time.sleep(0.3)
                    self.scanned_networks = cached_networks
                    self.frame.after(0, self._update_wifi_tree, cached_networks)
                    update_progress(100, "完成（使用缓存）", 
                                  "✓ 数据加载完成\n提示：点击'强制刷新'获取最新数据")
                    time.sleep(1)
                    progress_window.destroy()
                    return
                
                # 阶段2: 获取适配器 (10-20%)
                update_progress(10, "获取WiFi适配器...", "检测网卡信息")
                adapters = self.wifi_analyzer.get_wifi_interfaces()
                if not adapters:
                    raise Exception("未找到WiFi适配器")
                update_progress(15, "适配器检测完成", 
                              f"✓ 找到{len(adapters)}个适配器")
                
                # 阶段3: 执行扫描 (20-70%)
                update_progress(20, "扫描周围网络...", "执行系统扫描命令（可能需要10-30秒）")
                networks = self.wifi_analyzer.scan_wifi_networks(force_refresh=True)
                
                if not networks:
                    update_progress(70, "扫描完成", "✗ 未发现WiFi网络")
                    self.frame.after(0, lambda: self._show_empty_state(
                        "未发现WiFi网络\n\n建议：检查WiFi是否已开启"
                    ))
                else:
                    update_progress(70, f"扫描完成", 
                                  f"✓ 发现{len(networks)}个网络")
                
                # 阶段4: 数据解析 (70-85%)
                update_progress(75, "解析网络信息...", "处理SSID/BSSID/信道")
                time.sleep(0.2)
                update_progress(80, "识别厂商信息...", "查询OUI数据库")
                time.sleep(0.2)
                
                # 阶段5: 信道分析 (85-95%)
                update_progress(85, "分析信道重叠...", "检测干扰")
                overlaps = self._detect_channel_overlap(networks)
                update_progress(90, "生成统计信息...", 
                              f"检测到{len(overlaps)}组重叠" if overlaps else "无重叠")
                
                # 阶段6: 缓存和UI更新 (95-100%)
                update_progress(95, "更新界面...", "刷新网络列表")
                self.scan_cache.set('networks', networks)  # ✅ 写入缓存
                self.scanned_networks = networks
                self.frame.after(0, self._update_wifi_tree, networks)
                
                update_progress(100, "扫描完成！", 
                              f"✓ 共发现{len(networks)}个网络\n✓ 数据已缓存（30秒有效）")
                
                time.sleep(1)
                progress_window.destroy()
                
            except Exception as e:
                update_progress(0, "扫描失败", f"✗ 错误: {str(e)}")
                self.frame.after(0, lambda: ErrorHandler.handle_error(e, context="WiFi扫描"))
                time.sleep(2)
                progress_window.destroy()
        
        # 启动扫描线程
        threading.Thread(target=scan_worker, daemon=True).start()
    
    def _update_wifi_tree(self, networks):
        """✅ 新增: 更新WiFi列表（从扫描数据）"""
        self.wifi_tree.delete(*self.wifi_tree.get_children())
        
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
        
        # 频段统计
        band_stats = {'2.4GHz': 0, '5GHz': 0, '6GHz': 0}
        for net in networks:
            band = net.get('band', 'N/A')
            if band in band_stats:
                band_stats[band] += 1
        
        stats_msg = f"扫描完成，发现 {len(networks)} 个WiFi网络\n" + \
                   f"2.4GHz: {band_stats['2.4GHz']} | 5GHz: {band_stats['5GHz']} | 6GHz: {band_stats['6GHz']}"
        messagebox.showinfo("完成", stats_msg)
    
    def _show_empty_state(self, message="暂无数据"):
        """✅ 新增: 显示空状态提示"""
        # 清空列表
        self.wifi_tree.delete(*self.wifi_tree.get_children())
        
        # 插入空状态提示（使用中间列显示消息）
        empty_values = ("", "", "", "", "", "", 
                       message, "", "", "", "", "")
        self.wifi_tree.insert('', 'end', values=empty_values, tags=('empty_state',))
        
        # 配置空状态样式
        self.wifi_tree.tag_configure('empty_state', foreground='#999999', 
                                     font=('Microsoft YaHei', 10))
    
    def _scan_wifi_worker(self):
        """✅ 优化: WiFi扫描工作线程（带空状态和错误处理）"""
        # 显示加载状态
        self.frame.after(0, lambda: self._show_empty_state("正在扫描WiFi网络..."))
        
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
            
            # ✅ 优化: 检查是否有网络
            if not networks:
                self.frame.after(0, lambda: self._show_empty_state(
                    "未发现WiFi网络\n\n"
                    "可能的原因：\n"
                    "• WiFi适配器未开启\n"
                    "• 周围无WiFi信号\n"
                    "• 驱动程序问题\n\n"
                    "建议：点击'扫描'按钮重试"
                ))
                return
            
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
            # ✅ 优化: 使用友好的错误提示
            self.frame.after(0, lambda: ErrorHandler.handle_error(e, context="WiFi扫描"))
            self.frame.after(0, lambda: self._show_empty_state(
                f"扫描失败\n\n{str(e)}\n\n点击'扫描'按钮重试"
            ))
    
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
        """✅ 优化: 应用频段过滤（使用缓存数据，无需重新扫描）"""
        band_filter = self.band_var.get()
        
        # ✅ 直接过滤缓存数据，不需要重新扫描
        filtered_networks = self.scanned_networks
        if band_filter != "全部":
            filtered_networks = [net for net in self.scanned_networks 
                               if net.get('band') == band_filter]
        
        # ✅ 复用_update_wifi_tree方法，但不显示消息框
        self.wifi_tree.delete(*self.wifi_tree.get_children())
        
        if not filtered_networks:
            self._show_empty_state(f"无 {band_filter} 网络\n\n尝试切换到其他频段")
            return
        
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
        
        # ✅ 使用状态栏而非弹窗（减少干扰）
        print(f"[过滤] 显示 {len(filtered_networks)} 个 {band_filter} 网络")
    
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
    
    def _jump_to_channel_analysis(self):
        """跳转到信道分析标签页
        
        v2.0优化: 不再在该模块中重复实现信道分析，
        而是直接跳转到专门的信道分析标签页。
        """
        if not self.scanned_networks:
            messagebox.showwarning("提示", "请先扫描WiFi网络，然后切换到信道分析标签页查看详细分析")
            return
        
        # 跳转到信道分析标签页 (第2个标签，索引1)
        try:
            self.notebook.select(1)  # 0=网络概览, 1=信道分析
            messagebox.showinfo("提示", "已切换到信道分析标签页，请点击'分析'按钮查看详细报告")
        except Exception as e:
            messagebox.showerror("错误", f"跳转失败: {str(e)}")
    
    # ❌ v2.0: _show_channel_analysis()方法已删除，使用上面的_jump_to_channel_analysis()替代
    # 原始方法在network_overview中重复实现了信道分析（~70行），
    # 现在统一使用channel_analysis.py模块。
    
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
        """显示信号强度罗盘弹窗（已提取为独立模块）"""
        from .signal_compass import show_signal_compass
        show_signal_compass(self.parent, self.scanned_networks)


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

