"""
网络概览标签页
功能：WiFi扫描、信号强度显示、雷达图、实时监控
优化：线程安全、频段分析、信道优化、连接质量监控、报告导出
"""

# ============================================================
# ⚠️ 安全警告：此文件为旧版本备份，包含已知安全漏洞
# ============================================================
# 问题：使用 shell=True 存在命令注入风险
# 位置：line 902, line 916
# 状态：已在新版本修复（network_overview.py）
# 建议：请勿在生产环境使用此文件
# 审计日期：2026-02-04
# ============================================================

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
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
    """网络概览标签页（增强版）"""
    
    def __init__(self, parent, wifi_analyzer):
        self.parent = parent
        self.wifi_analyzer = wifi_analyzer
        self.frame = ttk.Frame(parent)
        
        # ✅ P0: 线程安全机制
        self.data_lock = threading.Lock()  # 数据锁
        self.update_queue = queue.Queue(maxsize=100)  # UI更新队列
        
        # 监控相关（使用deque优化内存）
        self.monitoring = False
        self.monitor_thread = None
        self.signal_history = deque(maxlen=240)  # ✅ deque自动淘汰旧数据
        self.max_history_points = 240
        
        # 扫描数据缓存
        self.scanned_networks = []
        self.current_band_filter = "全部"  # ✅ P1: 频段过滤
        
        # 连接质量监控数据
        self.connection_quality = {'latency': 0, 'jitter': 0, 'packet_loss': 0}
        
        self._setup_ui()
        self._start_queue_processor()  # 启动队列处理器
    
    def _setup_ui(self):
        """设置UI"""
        # 顶部控制栏
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(control_frame, text="适配器:", font=('Microsoft YaHei', 10)).pack(side='left', padx=5)
        
        self.adapter_var = tk.StringVar()
        self.adapter_combo = ttk.Combobox(control_frame, textvariable=self.adapter_var, 
                                         width=50, state='readonly')
        self.adapter_combo.pack(side='left', padx=5)
        
        ModernButton(control_frame, text="🔄 刷新", 
                    command=self._refresh_adapters, style='primary').pack(side='left', padx=5)
        
        ModernButton(control_frame, text="📡 扫描", 
                    command=self._scan_wifi, style='success').pack(side='left', padx=5)
        
        ttk.Label(control_frame, text="频段:", font=('Microsoft YaHei', 10)).pack(side='left', padx=(15, 5))
        self.band_var = tk.StringVar(value="全部")
        band_combo = ttk.Combobox(control_frame, textvariable=self.band_var,
                                 values=["全部", "2.4GHz", "5GHz", "6GHz"],
                                 width=8, state='readonly')
        band_combo.pack(side='left', padx=5)
        band_combo.bind('<<ComboboxSelected>>', lambda e: self._apply_band_filter())
        
        self.monitor_btn = ModernButton(control_frame, text="▶ 监控", 
                                       command=self._toggle_monitor, style='warning')
        self.monitor_btn.pack(side='left', padx=5)
        
        ModernButton(control_frame, text="📊 信道", 
                    command=self._show_channel_analysis, style='info').pack(side='left', padx=5)
        ModernButton(control_frame, text="📈 趋势", 
                    command=self._show_history_chart, style='info').pack(side='left', padx=5)
        ModernButton(control_frame, text="📄 报告", 
                    command=self._export_diagnostic_report, style='primary').pack(side='left', padx=5)
        
        # 主内容区域 - 左右分栏
        main_paned = ttk.PanedWindow(self.frame, orient='horizontal')
        main_paned.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 左侧：当前连接信息 + WiFi列表（减小权重）
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=2)
        
        # 当前连接信息
        info_label = ttk.Label(left_frame, text="📶 当前WiFi连接", 
                              font=('Microsoft YaHei', 10, 'bold'))
        info_label.pack(anchor='w', pady=5)
        
        self.current_info = scrolledtext.ScrolledText(left_frame, height=8, width=50,
                                                      font=('Consolas', 9))
        self.current_info.pack(fill='x', pady=5)
        
        # WiFi网络列表
        list_label = ttk.Label(left_frame, text="🌐 周围WiFi网络", 
                              font=('Microsoft YaHei', 10, 'bold'))
        list_label.pack(anchor='w', pady=5)
        
        # 创建Treeview
        columns = ("☑", "#", "SSID", "信号强度", "信号(%)", "dBm", "厂商", 
                  "BSSID", "信道", "频段", "WiFi标准", "加密")
        self.wifi_tree = ttk.Treeview(left_frame, columns=columns, show='headings', height=15)
        
        # 设置列宽
        widths = [30, 30, 140, 95, 55, 60, 95, 125, 45, 55, 95, 75]
        for col, width in zip(columns, widths):
            self.wifi_tree.heading(col, text=col)
            self.wifi_tree.column(col, width=width, anchor='center' if col != 'SSID' else 'w')
        
        # 滚动条
        scrollbar = ttk.Scrollbar(left_frame, orient='vertical', command=self.wifi_tree.yview)
        self.wifi_tree.configure(yscrollcommand=scrollbar.set)
        
        self.wifi_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # ✅ P2: 信号质量彩色标签配置
        self.wifi_tree.tag_configure('excellent', background='#d4edda')  # 绿色 80%+
        self.wifi_tree.tag_configure('good', background='#fff3cd')      # 黄色 60-80%
        self.wifi_tree.tag_configure('fair', background='#ffe5d0')      # 橙色 40-60%
        self.wifi_tree.tag_configure('poor', background='#f8d7da')      # 红色 <40%
        self.wifi_tree.tag_configure('wifi6e', background='#e7f3ff')    # 浅蓝色 6GHz
        
        # 绑定点击事件，允许勾选/取消勾选SSID
        self.wifi_tree.bind('<Button-1>', self._on_tree_click)
        
        # ✅ P1: 右键菜单
        self._setup_context_menu()
        
        # 右侧：WiFi雷达图（增加权重，优先显示）
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=3)
        
        radar_label = ttk.Label(right_frame, text="📡 WiFi信号雷达图 (实时)", 
                               font=('Microsoft YaHei', 10, 'bold'))
        radar_label.pack(anchor='w', pady=5)
        
        # 雷达图控制
        radar_control = ttk.Frame(right_frame)
        radar_control.pack(fill='x', pady=5)
        
        ttk.Label(radar_control, text="刷新间隔:").pack(side='left', padx=5)
        self.interval_var = tk.StringVar(value="5秒")
        interval_combo = ttk.Combobox(radar_control, textvariable=self.interval_var,
                                     values=["1秒", "2秒", "5秒", "10秒", "30秒"],
                                     width=10, state='readonly')
        interval_combo.pack(side='left', padx=5)
        
        # 雷达图画布
        self.radar_figure = Figure(figsize=(6, 5), dpi=100)
        self.radar_canvas = FigureCanvasTkAgg(self.radar_figure, right_frame)
        self.radar_canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # 初始化
        self._refresh_adapters()
        self._draw_empty_radar()
    
    def _refresh_adapters(self):
        """刷新WiFi适配器列表"""
        try:
            adapters = self.wifi_analyzer.get_wifi_interfaces()
            if adapters:
                self.adapter_combo['values'] = adapters
                if not self.adapter_var.get():
                    self.adapter_combo.current(0)
                messagebox.showinfo("提示", f"找到 {len(adapters)} 个WiFi适配器")
            else:
                messagebox.showwarning("警告", "未找到WiFi适配器")
        except Exception as e:
            messagebox.showerror("错误", f"获取适配器失败: {str(e)}")
    
    def _scan_wifi(self):
        """扫描WiFi网络（异步优化）"""
        # ✅ P2: 异步扫描+进度条
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
        # 清空列表
        self.frame.after(0, lambda: [self.wifi_tree.delete(item) for item in self.wifi_tree.get_children()])
        
        try:
            # 显示当前连接信息和适配器详情
            current_wifi = self.wifi_analyzer.get_current_wifi_info()
            self.current_info.delete('1.0', 'end')
            if current_wifi:
                # 构建显示文本，包含所有可用字段
                info_lines = []
                
                # 适配器硬件信息（优先显示）
                if 'adapter_description' in current_wifi or 'adapter_name' in current_wifi:
                    info_lines.append("【WiFi适配器】")
                    if 'adapter_description' in current_wifi:
                        info_lines.append(f"网卡型号: {current_wifi['adapter_description']}")
                    if 'adapter_name' in current_wifi:
                        info_lines.append(f"适配器名称: {current_wifi['adapter_name']}")
                    if 'mac' in current_wifi:
                        info_lines.append(f"物理地址: {current_wifi['mac']}")
                    if 'state' in current_wifi:
                        info_lines.append(f"状态: {current_wifi['state']}")
                    info_lines.append("")  # 空行分隔
                
                # 当前连接信息
                if 'ssid' in current_wifi:
                    info_lines.append("【当前连接】")
                    info_lines.append(f"SSID: {current_wifi['ssid']}")
                    
                    # 信号相关
                    if 'signal' in current_wifi:
                        info_lines.append(f"信号强度: {current_wifi['signal']}")
                    if 'bssid' in current_wifi:
                        info_lines.append(f"BSSID(AP): {current_wifi['bssid']}")
                    
                    # 网络类型和安全
                    if 'radio_type' in current_wifi:
                        info_lines.append(f"无线标准: {current_wifi['radio_type']}")
                    if 'channel' in current_wifi:
                        info_lines.append(f"信道: {current_wifi['channel']}")
                    
                    # 速率信息
                    if 'receive_rate' in current_wifi:
                        info_lines.append(f"接收速率: {current_wifi['receive_rate']}")
                    if 'transmit_rate' in current_wifi:
                        info_lines.append(f"发送速率: {current_wifi['transmit_rate']}")
                    
                    # 安全配置
                    if 'authentication' in current_wifi:
                        info_lines.append(f"认证: {current_wifi['authentication']}")
                    if 'encryption' in current_wifi:
                        info_lines.append(f"加密: {current_wifi['encryption']}")
                    
                    # 连接模式
                    if 'mode' in current_wifi:
                        info_lines.append(f"连接模式: {current_wifi['mode']}")
                    
                    # IP地址
                    if 'ip' in current_wifi:
                        info_lines.append(f"IP地址: {current_wifi['ip']}")
                
                info_text = '\n'.join(info_lines) if info_lines else "已连接但无详细信息"
                self.current_info.insert('1.0', info_text)
            else:
                # 即使未连接WiFi，也显示适配器信息
                self.current_info.insert('1.0', "未连接WiFi\n\n提示: 适配器信息将在连接WiFi后显示")
            
            # 扫描周围网络
            networks = self.wifi_analyzer.scan_wifi_networks(force_refresh=True)
            self.scanned_networks = networks  # 缓存扫描结果
            
            # ✅ P1: 检测信道重叠（2.4GHz）
            overlapping_info = self._detect_channel_overlap(networks)
            if overlapping_info:
                overlap_msg = f"检测到{len(overlapping_info)}组信道重叠：\n" + "\n".join(
                    [f"• {ssid1} ↔ {ssid2}" for ssid1, ssid2 in overlapping_info[:5]]
                )
                self.frame.after(0, lambda: messagebox.showinfo("信道重叠提示", overlap_msg))
            
            # 按信号强度从强到弱排序
            networks_sorted = sorted(networks, key=lambda x: x.get('signal_percent', 0), reverse=True)
            
            for idx, network in enumerate(networks_sorted, 1):
                signal_percent = network.get('signal_percent', 0)
                
                # 确保signal_percent是整数（兼容字符串格式如"85%"）
                if isinstance(signal_percent, str):
                    signal_percent = int(signal_percent.rstrip('%')) if signal_percent != '未知' else 0
                elif not isinstance(signal_percent, (int, float)):
                    signal_percent = 0
                
                # 计算dBm值：从百分比转换（0-100% 映射到 -100至-20 dBm）
                signal_dbm = -100 + (signal_percent * 0.7) if signal_percent > 0 else -100
                
                # ✅ P2: 信号质量彩色指示器
                quality_indicator, quality_color = self._get_signal_quality_indicator(signal_percent)
                bar_length = int(signal_percent / 10)
                signal_bar = quality_indicator + ' ' + '█' * bar_length + '░' * (10 - bar_length)
                
                # 获取WiFi标准并添加标识
                wifi_standard = network.get('wifi_standard', 'N/A')
                band = network.get('band', 'N/A')
                
                # 为6GHz网络添加特殊标识
                if band == '6GHz':
                    wifi_standard_display = f"⚡{wifi_standard}"
                else:
                    wifi_standard_display = wifi_standard
                
                values = (
                    "",  # 默认不勾选
                    idx,
                    network.get('ssid', 'N/A'),
                    signal_bar,
                    f"{signal_percent}%",
                    f"{signal_dbm:.0f} dBm",
                    network.get('vendor', '未知'),
                    network.get('bssid', 'N/A'),
                    network.get('channel', 'N/A'),
                    band,
                    wifi_standard_display,  # 新增：WiFi标准
                    network.get('authentication', 'N/A')
                )
                
                # ✅ P2: 应用tag颜色（按信号质量和频段）
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
                
                item_id = self.wifi_tree.insert('', 'end', values=values, tags=tuple(tags))
            
            # ✅ 统计各频段数量
            band_stats = {'2.4GHz': 0, '5GHz': 0, '6GHz': 0}
            for net in networks:
                band = net.get('band', 'N/A')
                if band in band_stats:
                    band_stats[band] += 1
            
            stats_msg = f"扫描完成，发现 {len(networks)} 个WiFi网络\n" + \
                       f"2.4GHz: {band_stats['2.4GHz']} | 5GHz: {band_stats['5GHz']} | 6GHz: {band_stats['6GHz']}\n" + \
                       "(已按信号强度从强到弱排序，颜色标识信号质量)"
            self.frame.after(0, lambda: messagebox.showinfo("完成", stats_msg))
            
        except Exception as e:
            messagebox.showerror("错误", f"扫描失败: {str(e)}")
    
    def _toggle_monitor(self):
        """切换监控状态"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_btn.config(text="⏸ 停止监控")
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
        else:
            self.monitoring = False
            self.monitor_btn.config(text="▶ 开始监控")
    
    def _monitor_loop(self):
        """监控循环（线程安全优化）"""
        while self.monitoring:
            try:
                # 获取刷新间隔
                interval_str = self.interval_var.get()
                interval = int(interval_str.replace('秒', ''))
                
                # 扫描网络
                networks = self.wifi_analyzer.scan_wifi_networks(force_refresh=True)
                
                # 获取当前勾选的SSID列表
                selected_ssids = []
                for item in self.wifi_tree.get_children():
                    values = self.wifi_tree.item(item)['values']
                    if values[0] == "☑":
                        selected_ssids.append(values[2])
                
                # 记录信号历史（只记录勾选的SSID）
                timestamp = datetime.now()
                signal_data = {
                    'time': timestamp,
                    'networks': []
                }
                
                # 遍历所有扫描到的网络，只记录勾选的SSID
                for network in networks:
                    ssid = network.get('ssid', 'N/A')
                    if ssid in selected_ssids:
                        signal_data['networks'].append({
                            'ssid': ssid,
                            'signal': network.get('signal', -100),
                            'signal_percent': network.get('signal_percent', 0)
                        })
                
                # ✅ P0: 线程安全写入
                with self.data_lock:
                    self.signal_history.append(signal_data)
                    # deque会自动处理maxlen，无需手动pop
                
                # ✅ P2: 监控连接质量（每5次扫描执行一次）
                if len(self.signal_history) % 5 == 0:
                    self._monitor_connection_quality()
                
                # 通过队列通知UI更新
                try:
                    self.update_queue.put_nowait({'type': 'radar_update'})
                except queue.Full:
                    pass  # 丢弃过期更新
                
                time.sleep(interval)
                
            except Exception as e:
                print(f"监控错误: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(5)
    
    def _draw_empty_radar(self):
        """绘制空雷达图（与监控时保持一致的样式）"""
        self.radar_figure.clear()
        
        # 使用与监控时一致的配色方案
        bg_color = '#fafafa'
        grid_color = '#cccccc'
        text_color = '#2c3e50'
        
        self.radar_figure.patch.set_facecolor(bg_color)
        ax = self.radar_figure.add_subplot(111, projection='polar')
        ax.set_facecolor('#ffffff')
        
        # 设置顺时针方向，从0度（12点位置）开始
        ax.set_theta_direction(-1)
        ax.set_theta_zero_location('N')
        
        # 24个检测点，每15度一个
        max_time_points = 24
        all_angles = np.linspace(0, 2 * np.pi, max_time_points, endpoint=False)
        
        # 径向网格
        ax.set_ylim(-100, -20)
        ax.set_yticks([-100, -85, -70, -50, -20])
        ax.set_yticklabels(['-100\n极弱', '-85\n弱', '-70\n一般', 
                           '-50\n良好', '-20\n优秀'], 
                          color=text_color, fontsize=8, fontweight='bold')
        
        # 角度标签 - 显示0、15、30、45...345度
        ax.set_xticks(all_angles)
        angle_degrees = [0, 15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165, 
                       180, 195, 210, 225, 240, 255, 270, 285, 300, 315, 330, 345]
        angle_labels = [f'{deg}°' for deg in angle_degrees]
        ax.set_xticklabels(angle_labels, fontsize=7, color=text_color, fontweight='bold')
        
        # 网格样式
        ax.grid(True, color=grid_color, alpha=0.5, linestyle='--', linewidth=1.2)
        ax.spines['polar'].set_color(grid_color)
        ax.spines['polar'].set_linewidth(2)
        ax.tick_params(colors=text_color, width=1.5)
        
        # 标题
        ax.set_title('WiFi 信号稳定性雷达分析\n等待监控数据...', 
                    fontsize=10, pad=20, color=text_color, fontweight='bold')
        
        self.radar_figure.tight_layout()
        self.radar_canvas.draw()
    
    def _update_radar(self):
        """更新雷达图 - 增强版：信号稳定性可视化分析"""
        try:
            # ✅ P0: 线程安全读取
            with self.data_lock:
                if not self.signal_history:
                    print("[调试] 无信号历史数据")
                    return
                
                # 复制数据避免长时间持锁
                history_snapshot = list(self.signal_history)
            
            print(f"[调试] 更新雷达图，历史数据点: {len(history_snapshot)}")
        
            # 获取勾选的SSID列表
            selected_ssids = []
            for item in self.wifi_tree.get_children():
                values = self.wifi_tree.item(item)['values']
                if values[0] == "☑":
                    ssid = values[2]
                    selected_ssids.append(ssid)
            
            print(f"[调试] 选中的SSID: {selected_ssids}")
            
            # 支持最多10个SSID同时监控
            selected_ssids = selected_ssids[:10]
            
            if len(selected_ssids) == 0:
                # 显示提示信息
                self.radar_figure.clear()
                ax = self.radar_figure.add_subplot(111)
                ax.text(0.5, 0.5, '请先勾选WiFi网络\n然后点击"开始监控"', 
                       ha='center', va='center', fontsize=16, 
                       color='#ff6600', fontweight='bold',
                       bbox=dict(boxstyle='round,pad=1', facecolor='#fff3cd', 
                                edgecolor='#ff6600', linewidth=2))
                ax.text(0.5, 0.35, '1. 点击第一列复选框勾选WiFi\n2. 点击"开始监控"按钮\n3. 等待10-15秒查看雷达图', 
                       ha='center', va='center', fontsize=10, 
                       color='#666666', style='italic')
                ax.axis('off')
                self.radar_canvas.draw()
                return
            
            self.radar_figure.clear()
            
            # 专业配色方案
            bg_color = '#fafafa'
            grid_color = '#cccccc'
            text_color = '#2c3e50'
            
            self.radar_figure.patch.set_facecolor(bg_color)
            ax = self.radar_figure.add_subplot(111, projection='polar')
            ax.set_facecolor('#ffffff')
            
            # 设置顺时针方向，从0度（12点位置）开始
            ax.set_theta_direction(-1)
            ax.set_theta_zero_location('N')
            
            # 24个检测点，每15度一个
            max_time_points = 24
            current_scan_position = len(history_snapshot) % max_time_points
            all_angles = np.linspace(0, 2 * np.pi, max_time_points, endpoint=False)
            
            # SSID配色
            ssid_colors = ['#0066cc', '#ff6600', '#00aa88', '#cc0066', '#6600cc',
                          '#ff9900', '#cc3333', '#0099ff', '#009933', '#993399']
            
            # 数据准备
            recent_history = history_snapshot[-max_time_points:]
            ssid_data = {}
            ssid_stats = {}  # 稳定性统计
            
            for ssid in selected_ssids:
                ssid_data[ssid] = np.full(max_time_points, -100.0)
                ssid_stats[ssid] = {'values': [], 'mean': -100, 'std': 0, 'min': -100, 'max': -100}
            
            # 数据填充
            print(f"[调试] 开始填充数据，历史记录数: {len(recent_history)}")
            for idx, data in enumerate(recent_history):
                angle_position = (current_scan_position - len(recent_history) + idx + 1) % max_time_points
                print(f"[调试] 扫描#{idx+1} 包含 {len(data['networks'])} 个网络")
                for network in data['networks']:
                    ssid = network.get('ssid')
                    print(f"[调试]   网络SSID: '{ssid}' (在选中列表中: {ssid in ssid_data})")
                    if ssid in ssid_data:
                        percent = network.get('signal_percent', 0)
                        if isinstance(percent, str):
                            percent = int(percent.rstrip('%'))
                        signal_dbm = -100 + (percent * 0.7) if percent > 0 else -100
                        
                        # 记录所有有效信号值（包括-100dBm）
                        ssid_data[ssid][angle_position] = signal_dbm
                        ssid_stats[ssid]['values'].append(signal_dbm)
                        print(f"[调试]   ✓ 填充: {ssid} 位置{angle_position} = {signal_dbm:.1f}dBm")
            
            # 计算稳定性指标
            for ssid in selected_ssids:
                # 保留所有采集到的信号值（包括弱信号）
                valid_values = [v for v in ssid_stats[ssid]['values'] if v >= -100]
                if len(valid_values) >= 2:
                    ssid_stats[ssid]['mean'] = np.mean(valid_values)
                    ssid_stats[ssid]['std'] = np.std(valid_values)
                    ssid_stats[ssid]['min'] = np.min(valid_values)
                    ssid_stats[ssid]['max'] = np.max(valid_values)
                    ssid_stats[ssid]['range'] = ssid_stats[ssid]['max'] - ssid_stats[ssid]['min']
                    # 稳定性评分：标准差越小越稳定（0-100分）
                    ssid_stats[ssid]['stability_score'] = max(0, 100 - ssid_stats[ssid]['std'] * 5)
                elif len(valid_values) == 1:
                    ssid_stats[ssid]['mean'] = valid_values[0]
                    ssid_stats[ssid]['stability_score'] = 100  # 单点视为完全稳定
            
            # 绘制每个SSID的信号轨迹和稳定性指示
            print(f"[调试] 开始绘制 {len(selected_ssids)} 个SSID")
            for ssid_idx, ssid in enumerate(selected_ssids):
                values = ssid_data[ssid]
                color = ssid_colors[ssid_idx % len(ssid_colors)]
                stats = ssid_stats[ssid]
                
                print(f"[调试] 绘制SSID: {ssid}")
                print(f"[调试]   数据点数: {len(stats['values'])}")
                print(f"[调试]   数组非-100值数量: {np.sum(values > -100)}")
                
                # 降低阈值，允许显示弱信号（-100dBm附近）
                valid_mask = values > -99.9
                if not np.any(valid_mask):
                    print(f"[调试]   ✗ 跳过{ssid}: 没有有效数据点")
                    continue
                
                valid_indices = np.where(valid_mask)[0]
                valid_angles = all_angles[valid_indices]
                valid_values = values[valid_indices]
                print(f"[调试]   ✓ 有效点数: {len(valid_indices)}")
                
                # 根据稳定性评分选择线条样式
                stability_score = stats.get('stability_score', 0)
                if stability_score >= 80:
                    linestyle = '-'  # 实线：稳定
                    alpha_line = 0.95
                elif stability_score >= 60:
                    linestyle = '--'  # 虚线：中等稳定
                    alpha_line = 0.85
                else:
                    linestyle = ':'  # 点线：不稳定
                    alpha_line = 0.75
                
                # 绘制波动范围（阴影区域显示信号波动幅度）
                if len(valid_values) >= 3 and stats['std'] > 0:
                    # 显示±标准差范围
                    upper_bound = np.minimum(stats['mean'] + stats['std'], -20)
                    lower_bound = np.maximum(stats['mean'] - stats['std'], -100)
                    ax.fill_between(all_angles, 
                                   np.full(max_time_points, lower_bound),
                                   np.full(max_time_points, upper_bound),
                                   color=color, alpha=0.12, zorder=2)
                
                # 绘制平均信号线（虚线）
                if stats['mean'] > -100:
                    avg_line = np.full(max_time_points, stats['mean'])
                    ax.plot(all_angles, avg_line, '--', 
                           linewidth=1.5, color=color, alpha=0.4, zorder=3)
                
                # 绘制实际信号连接线
                if len(valid_indices) >= 2:
                    ax.plot(valid_angles, valid_values, linestyle, 
                           linewidth=4, color=color, alpha=alpha_line, 
                           zorder=7, solid_capstyle='round')
                    
                    # 闭合曲线
                    if len(valid_indices) >= max_time_points - 1:
                        ax.plot([valid_angles[-1], valid_angles[0]], 
                               [valid_values[-1], valid_values[0]], linestyle,
                               linewidth=4, color=color, alpha=alpha_line, zorder=7)
                
                # 数据点标记（大小反映稳定性）
                marker_size = 12 if stability_score >= 80 else 10 if stability_score >= 60 else 8
                ax.plot(valid_angles, valid_values, 'o', 
                       markersize=marker_size, color=color, alpha=1.0,
                       markeredgewidth=2.5, markeredgecolor='white', 
                       zorder=8, label=f'{ssid} (稳定度:{int(stability_score)}%)')
                
                # 数值标注（仅在稳定性较好时显示所有点）
                show_all_labels = stability_score >= 70
                for i, (angle, value) in enumerate(zip(valid_angles, valid_values)):
                    if show_all_labels or i == len(valid_angles) - 1:  # 最新点始终显示
                        offset_x = 10 if i % 2 == 0 else -15
                        offset_y = 8 if i % 3 == 0 else -12
                        
                        ax.annotate(f'{int(value)}', 
                                   xy=(angle, value),
                                   xytext=(offset_x, offset_y), 
                                   textcoords='offset points',
                                   fontsize=7, fontweight='bold', color=color,
                                   bbox=dict(boxstyle='round,pad=0.3', 
                                           facecolor='white', edgecolor=color, 
                                           alpha=0.85, linewidth=1.2),
                                   zorder=9)
            
            # 绘制扫描指示器
            scan_angle = all_angles[current_scan_position]
            ax.plot([scan_angle, scan_angle], [-100, -25], 
                   color='#00ff00', linewidth=5, alpha=0.7, zorder=10)
            ax.plot([scan_angle], [-25], 'o', markersize=18, 
                   color='#00ff00', alpha=0.8, markeredgewidth=4, 
                   markeredgecolor='white', zorder=11)
            ax.text(scan_angle, -20, f'▼\n{int(np.degrees(scan_angle))}°', 
                   ha='center', va='bottom', fontsize=9, 
                   color='#00ff00', fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.4', 
                           facecolor='white', edgecolor='#00ff00',
                           alpha=0.95, linewidth=2.5), zorder=12)
            
            # 径向网格
            ax.set_ylim(-100, -20)
            ax.set_yticks([-100, -85, -70, -50, -20])
            ax.set_yticklabels(['-100\n极弱', '-85\n弱', '-70\n一般', 
                               '-50\n良好', '-20\n优秀'], 
                              color=text_color, fontsize=8, fontweight='bold')
            
            # 角度标签 - 显示0、15、30、45...345度
            ax.set_xticks(all_angles)
            angle_degrees = [0, 15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165, 
                           180, 195, 210, 225, 240, 255, 270, 285, 300, 315, 330, 345]
            angle_labels = [f'{deg}°' for deg in angle_degrees]
            ax.set_xticklabels(angle_labels, fontsize=7, color=text_color, fontweight='bold')
            
            # 网格样式
            ax.grid(True, color=grid_color, alpha=0.5, linestyle='--', linewidth=1.2)
            ax.spines['polar'].set_color(grid_color)
            ax.spines['polar'].set_linewidth(2)
            ax.tick_params(colors=text_color, width=1.5)
            
            # 增强图例（显示稳定性信息）
            legend = ax.legend(loc='upper left', bbox_to_anchor=(1.05, 1.0), 
                              fontsize=7, frameon=True, shadow=True,
                              fancybox=True, borderpad=0.6, labelspacing=0.6,
                              title='网络稳定性监控\n━━实线=稳定 ━━虚线=中等 ⋯⋯点线=不稳定', 
                              title_fontsize=7)
            legend.get_frame().set_facecolor('white')
            legend.get_frame().set_edgecolor(grid_color)
            legend.get_frame().set_alpha(0.95)
            
            # 标题（包含稳定性说明）
            data_count = len(self.signal_history)
            ax.set_title('WiFi 信号稳定性雷达分析\n阴影=波动范围 | 虚线=平均值 | 点大小=稳定度', 
                        fontsize=10, pad=20, color=text_color, fontweight='bold')
            
            # 底部说明（显示连接质量）
            cycle_count = len(history_snapshot) // max_time_points
            quality_text = f"延迟:{self.connection_quality['latency']:.0f}ms | 抖动:{self.connection_quality['jitter']:.0f}ms | 丢包:{self.connection_quality['packet_loss']}%" if self.connection_quality['latency'] > 0 else ""
            info_text = f"扫描: {int(np.degrees(scan_angle))}° | 周期: {cycle_count+1} | 数据: {len(history_snapshot)}/24 | {quality_text}"
            ax.text(0.5, -0.12, info_text, transform=ax.transAxes, 
                   ha='center', fontsize=7, color=text_color, style='italic')
            
            self.radar_figure.tight_layout()
            self.radar_canvas.draw()
            print("[调试] 雷达图绘制完成")
            
        except Exception as e:
            print(f"[错误] 雷达图更新失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_tree_click(self, event):
        """处理树形列表点击事件"""
        region = self.wifi_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.wifi_tree.identify_column(event.x)
            item = self.wifi_tree.identify_row(event.y)
            
            # 只处理第一列的点击
            if column == '#1' and item:  # #1是第一列
                values = list(self.wifi_tree.item(item)['values'])
                # 切换勾选状态
                if values[0] == "☑":
                    values[0] = ""
                else:
                    # 检查已勾选的数量
                    checked_count = sum(1 for i in self.wifi_tree.get_children() 
                                      if self.wifi_tree.item(i)['values'][0] == "☑")
                    if checked_count >= 10:
                        messagebox.showwarning("提示", "最多只能同时监控10个SSID")
                        return
                    values[0] = "☑"
                
                self.wifi_tree.item(item, values=values)
    
    def _start_queue_processor(self):
        """启动队列处理器（主线程）"""
        try:
            update = self.update_queue.get_nowait()
            if update['type'] == 'radar_update':
                self._update_radar()
        except queue.Empty:
            pass
        finally:
            self.parent.after(100, self._start_queue_processor)
    
    def _get_signal_quality_indicator(self, signal_percent):
        """获取信号质量彩色指示器"""
        if signal_percent >= 80:
            return "🟢优秀", "#28a745"
        elif signal_percent >= 60:
            return "🟡良好", "#ffc107"
        elif signal_percent >= 40:
            return "🟠一般", "#fd7e14"
        else:
            return "🔴较弱", "#dc3545"
    
    def _apply_band_filter(self):
        """应用频段过滤"""
        band_filter = self.band_var.get()
        
        # 清空列表
        for item in self.wifi_tree.get_children():
            self.wifi_tree.delete(item)
        
        # 根据频段过滤
        filtered_networks = self.scanned_networks
        if band_filter != "全部":
            filtered_networks = [net for net in self.scanned_networks 
                               if net.get('band') == band_filter]
        
        # 重新填充列表
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
        """检测2.4GHz信道重叠"""
        overlapping = set()
        networks_24g = [n for n in networks if n.get('band') == '2.4GHz']
        
        for i, net1 in enumerate(networks_24g):
            try:
                ch1 = int(net1.get('channel', 0))
                for net2 in networks_24g[i+1:]:
                    try:
                        ch2 = int(net2.get('channel', 0))
                        # 2.4GHz信道重叠规则：±4信道重叠
                        if abs(ch1 - ch2) <= 4:
                            overlapping.add((net1.get('ssid', 'N/A'), net2.get('ssid', 'N/A')))
                    except:
                        pass
            except:
                pass
        
        return list(overlapping)
    
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
        # 选中右键点击的项
        item = self.wifi_tree.identify_row(event.y)
        if item:
            self.wifi_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def _connect_wifi(self):
        """连接选中的WiFi"""
        selected = self.wifi_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择一个WiFi网络")
            return
        
        ssid = self.wifi_tree.item(selected[0])['values'][2]
        
        try:
            cmd = f'netsh wlan connect name="{ssid}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                                   creationflags=CREATE_NO_WINDOW, encoding='gbk', errors='ignore')
            
            if "已成功完成" in result.stdout or "successfully" in result.stdout.lower():
                messagebox.showinfo("成功", f"正在连接到 {ssid}...")
            else:
                messagebox.showerror("失败", f"连接失败：{result.stdout}")
        except Exception as e:
            messagebox.showerror("错误", f"连接失败: {str(e)}")
    
    def _disconnect_wifi(self):
        """断开当前WiFi连接"""
        try:
            cmd = 'netsh wlan disconnect'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True,
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
        """复制BSSID到剪贴板"""
        selected = self.wifi_tree.selection()
        if not selected:
            return
        
        bssid = self.wifi_tree.item(selected[0])['values'][7]
        self.frame.clipboard_clear()
        self.frame.clipboard_append(bssid)
        messagebox.showinfo("成功", f"已复制BSSID: {bssid}")
    
    def _monitor_connection_quality(self):
        """监控连接质量（Ping测试）"""
        try:
            current_wifi = self.wifi_analyzer.get_current_wifi_info()
            if not current_wifi:
                return
            
            # Ping默认网关
            cmd = 'ping -n 4 8.8.8.8'  # Google DNS
            result = subprocess.run(cmd, capture_output=True, text=True,
                                   creationflags=CREATE_NO_WINDOW, 
                                   encoding='gbk', errors='ignore', timeout=10)
            
            # 解析延迟
            latencies = re.findall(r'时间[=<](\d+)ms', result.stdout)
            if not latencies:
                latencies = re.findall(r'time[=<](\d+)ms', result.stdout)
            
            if latencies:
                latencies = [int(l) for l in latencies]
                self.connection_quality['latency'] = np.mean(latencies)
                self.connection_quality['jitter'] = np.std(latencies) if len(latencies) > 1 else 0
            
            # 解析丢包率
            packet_loss = re.search(r'丢失 = (\d+)', result.stdout)
            if not packet_loss:
                packet_loss = re.search(r'Lost = (\d+)', result.stdout)
            
            if packet_loss:
                self.connection_quality['packet_loss'] = int(packet_loss.group(1)) * 25  # 4个包，每个25%
        
        except Exception as e:
            print(f"连接质量监控错误: {e}")
    
    def _show_channel_analysis(self):
        """显示信道利用率分析"""
        if not self.scanned_networks:
            messagebox.showwarning("提示", "请先扫描WiFi网络")
            return
        
        # 分析信道利用率
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
                    # 主信道占用
                    channel_util_24[channel] += signal_percent
                    
                    # 邻近信道干扰
                    for offset in [-2, -1, 1, 2]:
                        neighbor = channel + offset
                        if 1 <= neighbor <= 13:
                            channel_util_24[neighbor] += signal_percent * 0.3
                
                elif band == '5GHz':
                    if channel not in channel_util_5:
                        channel_util_5[channel] = 0
                    channel_util_5[channel] += signal_percent
            
            except:
                pass
        
        # 推荐最佳信道
        best_channel_24 = min(channel_util_24, key=channel_util_24.get) if channel_util_24 else None
        best_channel_5 = min(channel_util_5, key=channel_util_5.get) if channel_util_5 else None
        
        # 创建分析窗口
        analysis_window = tk.Toplevel(self.frame)
        analysis_window.title("信道利用率分析")
        analysis_window.geometry("800x600")
        
        # 显示结果
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
        """显示信号历史趋势图"""
        with self.data_lock:
            if len(self.signal_history) < 2:
                messagebox.showwarning("提示", "历史数据不足，请先开始监控")
                return
            
            history_data = list(self.signal_history)
        
        # 获取所有SSID
        all_ssids = set()
        for data_point in history_data:
            for network in data_point['networks']:
                all_ssids.add(network['ssid'])
        
        if not all_ssids:
            messagebox.showwarning("提示", "没有监控数据")
            return
        
        # 创建趋势图窗口
        trend_window = tk.Toplevel(self.frame)
        trend_window.title("信号历史趋势")
        trend_window.geometry("1000x600")
        
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        colors = ['#0066cc', '#ff6600', '#00aa88', '#cc0066', '#6600cc']
        
        for idx, ssid in enumerate(list(all_ssids)[:5]):  # 最多显示5个
            times = []
            signals = []
            
            for data_point in history_data:
                for network in data_point['networks']:
                    if network['ssid'] == ssid:
                        times.append(data_point['time'])
                        signal_percent = network.get('signal_percent', 0)
                        if isinstance(signal_percent, str):
                            signal_percent = int(signal_percent.rstrip('%'))
                        signal_dbm = -100 + (signal_percent * 0.7) if signal_percent > 0 else -100
                        signals.append(signal_dbm)
                        break
            
            if times:
                ax.plot(times, signals, marker='o', label=ssid, 
                       color=colors[idx % len(colors)], linewidth=2)
        
        ax.set_xlabel('时间', fontsize=12)
        ax.set_ylabel('信号强度 (dBm)', fontsize=12)
        ax.set_title('WiFi信号历史趋势图', fontsize=14, fontweight='bold')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.axhline(y=-70, color='orange', linestyle='--', label='一般信号线', alpha=0.5)
        ax.axhline(y=-50, color='green', linestyle='--', label='良好信号线', alpha=0.5)
        
        canvas = FigureCanvasTkAgg(fig, trend_window)
        canvas.get_tk_widget().pack(fill='both', expand=True)
        canvas.draw()
    
    def _export_diagnostic_report(self):
        """导出诊断报告"""
        if not self.scanned_networks:
            messagebox.showwarning("提示", "请先扫描WiFi网络")
            return
        
        # 选择导出格式
        export_format = messagebox.askquestion("选择格式", 
                                               "导出为PDF？\n点击'否'导出为TXT")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if export_format == 'yes':
            # PDF导出（需要reportlab）
            try:
                from reportlab.lib.pagesizes import A4
                from reportlab.pdfgen import canvas
                from reportlab.pdfbase import pdfmetrics
                from reportlab.pdfbase.ttfonts import TTFont
                
                filename = f"WiFi诊断报告_{timestamp}.pdf"
                pdf = canvas.Canvas(filename, pagesize=A4)
                
                # 注册中文字体
                try:
                    pdfmetrics.registerFont(TTFont('SimSun', 'simsun.ttc'))
                    pdf.setFont('SimSun', 12)
                except:
                    pdf.setFont('Helvetica', 12)
                
                y = 800
                pdf.drawString(100, y, f"WiFi Network Diagnostic Report")
                y -= 20
                pdf.drawString(100, y, f"Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                y -= 30
                
                for idx, net in enumerate(self.scanned_networks[:30], 1):  # 最多30个
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
            
            except ImportError:
                messagebox.showerror("错误", "未安装reportlab库，请使用TXT格式导出")
            except Exception as e:
                messagebox.showerror("错误", f"PDF导出失败: {str(e)}")
        
        else:
            # TXT导出
            filename = f"WiFi诊断报告_{timestamp}.txt"
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("="*60 + "\n")
                    f.write("WiFi网络诊断报告\n")
                    f.write("="*60 + "\n")
                    f.write(f"扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"网络数量: {len(self.scanned_networks)}\n\n")
                    
                    # 频段统计
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
