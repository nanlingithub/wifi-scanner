"""
WiFi雷达实时信号分析模块 - 重新设计版
功能：实时监控10个WiFi信号的强度变化，使用雷达图动态展示
设计理念：简洁、高效、实时性强
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from datetime import datetime
import numpy as np
import queue
import subprocess
import re
import platform
from collections import deque
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from .theme import ModernTheme, ModernButton
from . import font_config

# Windows命令执行配置
if platform.system().lower() == "windows":
    CREATE_NO_WINDOW = 0x08000000
else:
    CREATE_NO_WINDOW = 0


class WifiRadarAnalyzer:
    """WiFi雷达实时分析器"""
    
    def __init__(self, parent, wifi_analyzer):
        self.parent = parent
        self.wifi_analyzer = wifi_analyzer
        self.frame = ttk.Frame(parent)
        
        # 核心数据结构
        self.monitoring = False
        self.monitor_thread = None
        self.data_lock = threading.Lock()
        
        # 雷达数据 - 12个方向，最多10个WiFi
        self.radar_directions = 12  # 0°, 30°, 60°, ..., 330°
        self.max_wifi_count = 10
        self.current_direction = 0  # 当前扫描方向索引（0-11）
        
        # WiFi信号数据 {ssid: [signal_values_12_directions]}
        self.wifi_signals = {}  # {ssid: [12个方向的信号值]}
        self.wifi_colors = {}   # {ssid: color}
        self.selected_ssids = [] # 选中的SSID列表（最多10个）
        
        # 扫描控制
        self.scan_interval = 0.5  # 每0.5秒扫描一个方向
        self.rotation_speed = 1.0  # 旋转速度倍数
        
        # 可用颜色（10种鲜明对比色）
        self.color_palette = [
            '#FF6B6B',  # 红色
            '#4ECDC4',  # 青色
            '#45B7D1',  # 蓝色
            '#FFA07A',  # 橙色
            '#98D8C8',  # 薄荷绿
            '#F7DC6F',  # 黄色
            '#BB8FCE',  # 紫色
            '#85C1E2',  # 天蓝
            '#F8B88B',  # 杏色
            '#A8E6CE',  # 淡绿
        ]
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI界面"""
        # 顶部标题和控制栏
        header = ttk.Frame(self.frame)
        header.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(header, text="📡 WiFi雷达实时信号分析", 
                 font=('Microsoft YaHei UI', 14, 'bold')).pack(side='left')
        
        # 控制按钮
        btn_frame = ttk.Frame(header)
        btn_frame.pack(side='right')
        
        self.start_btn = ModernButton(btn_frame, text="▶ 开始扫描", 
                                      command=self._start_monitoring, style='success')
        self.start_btn.pack(side='left', padx=5)
        
        self.stop_btn = ModernButton(btn_frame, text="⏸ 停止", 
                                     command=self._stop_monitoring, style='danger')
        self.stop_btn.pack(side='left', padx=5)
        self.stop_btn.config(state='disabled')
        
        ModernButton(btn_frame, text="🔄 刷新WiFi列表", 
                    command=self._refresh_wifi_list, style='primary').pack(side='left', padx=5)
        
        # 主内容区域 - 分左右两栏
        content = ttk.Frame(self.frame)
        content.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 左侧 - WiFi列表选择区
        left_panel = ttk.LabelFrame(content, text="WiFi信号选择（最多10个）", padding=10)
        left_panel.pack(side='left', fill='both', padx=(0, 5))
        
        # WiFi列表
        list_frame = ttk.Frame(left_panel)
        list_frame.pack(fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.wifi_listbox = tk.Listbox(
            list_frame, 
            selectmode=tk.MULTIPLE,
            yscrollcommand=scrollbar.set,
            font=('Consolas', 10),
            height=20,
            width=30
        )
        self.wifi_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.wifi_listbox.yview)
        
        # 信息标签
        self.info_label = ttk.Label(left_panel, text="已选择: 0/10", 
                                    font=('Microsoft YaHei UI', 9))
        self.info_label.pack(pady=5)
        
        # 扫描速度控制
        speed_frame = ttk.Frame(left_panel)
        speed_frame.pack(fill='x', pady=5)
        ttk.Label(speed_frame, text="扫描速度:").pack(side='left', padx=5)
        self.speed_var = tk.DoubleVar(value=1.0)
        speed_slider = ttk.Scale(speed_frame, from_=0.5, to=3.0, 
                                variable=self.speed_var, orient='horizontal')
        speed_slider.pack(side='left', fill='x', expand=True, padx=5)
        self.speed_label = ttk.Label(speed_frame, text="1.0x")
        self.speed_label.pack(side='left')
        speed_slider.config(command=self._update_speed)
        
        # 右侧 - 雷达图显示区
        right_panel = ttk.LabelFrame(content, text="实时雷达信号图", padding=10)
        right_panel.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        # 创建雷达图
        self.figure = Figure(figsize=(8, 8), dpi=100)
        self.figure.patch.set_facecolor('#f8f9fa')
        
        self.ax = self.figure.add_subplot(111, projection='polar')
        self.canvas = FigureCanvasTkAgg(self.figure, right_panel)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # 状态栏
        status_frame = ttk.Frame(right_panel)
        status_frame.pack(fill='x', pady=(10, 0))
        
        self.status_label = ttk.Label(status_frame, text="状态: 待机", 
                                      font=('Microsoft YaHei UI', 10))
        self.status_label.pack(side='left')
        
        self.direction_label = ttk.Label(status_frame, text="方向: 0°", 
                                        font=('Microsoft YaHei UI', 10))
        self.direction_label.pack(side='right')
        
        # 初始化空雷达图
        self._draw_empty_radar()
        
        # 刷新WiFi列表
        self._refresh_wifi_list()
    
    def _draw_empty_radar(self):
        """绘制空雷达图"""
        self.ax.clear()
        
        # 设置雷达图样式
        self.ax.set_theta_direction(-1)  # 顺时针
        self.ax.set_theta_zero_location('N')  # 0度在北方
        
        # 设置角度刻度 - 12个方向
        angles = np.linspace(0, 2*np.pi, self.radar_directions, endpoint=False)
        self.ax.set_xticks(angles)
        self.ax.set_xticklabels([f'{int(np.degrees(a))}°' for a in angles], 
                               fontsize=10, fontweight='bold')
        
        # 设置径向刻度 - 信号强度（-100到-20 dBm）
        self.ax.set_ylim(-100, -20)
        self.ax.set_yticks([-100, -80, -60, -40, -20])
        self.ax.set_yticklabels(['极弱\n-100', '弱\n-80', '中\n-60', '良\n-40', '强\n-20'],
                               fontsize=8)
        
        # 网格
        self.ax.grid(True, linestyle='--', alpha=0.7, linewidth=1.5)
        
        # 标题
        self.ax.set_title('WiFi信号雷达扫描\n等待开始...', 
                         fontsize=14, fontweight='bold', pad=20)
        
        self.canvas.draw()
    
    def _refresh_wifi_list(self):
        """刷新WiFi列表"""
        try:
            # 清空列表
            self.wifi_listbox.delete(0, tk.END)
            
            # 扫描WiFi
            networks = self._scan_wifi_networks()
            
            if not networks:
                self.wifi_listbox.insert(tk.END, "未检测到WiFi网络")
                return
            
            # 填充列表
            for network in networks:
                ssid = network.get('ssid', 'Unknown')
                signal = network.get('signal', '-100')
                self.wifi_listbox.insert(tk.END, f"{ssid} ({signal} dBm)")
            
            messagebox.showinfo("成功", f"检测到 {len(networks)} 个WiFi网络")
            
        except Exception as e:
            messagebox.showerror("错误", f"刷新失败: {e}")
    
    def _scan_wifi_networks(self):
        """扫描WiFi网络（使用WiFiAnalyzer）"""
        try:
            # 使用WiFiAnalyzer扫描网络
            if hasattr(self.wifi_analyzer, 'scan_networks'):
                networks_data = self.wifi_analyzer.scan_networks()
                networks = []
                for net in networks_data:
                    networks.append({
                        'ssid': net.get('ssid', 'Unknown'),
                        'signal': int(net.get('signal', -100))
                    })
                return networks
            
            # 备用方案：直接使用netsh命令
            # P0修复: 使用列表形式避免shell=True的命令注入风险
            cmd = ["netsh", "wlan", "show", "networks", "mode=bssid"]
            result = subprocess.run(
                cmd,
                shell=False,
                capture_output=True,
                text=True,
                creationflags=CREATE_NO_WINDOW,
                encoding='gbk',
                errors='ignore'
            )
            
            networks = []
            current_network = {}
            
            for line in result.stdout.split('\n'):
                line = line.strip()
                
                if 'SSID' in line and ':' in line and 'BSSID' not in line:
                    if current_network:
                        networks.append(current_network)
                    ssid = line.split(':', 1)[1].strip()
                    current_network = {'ssid': ssid}
                
                elif '信号' in line and ':' in line:
                    signal_str = line.split(':', 1)[1].strip().rstrip('%')
                    try:
                        signal_percent = int(signal_str)
                        signal_dbm = -100 + (signal_percent * 0.7)
                        current_network['signal'] = int(signal_dbm)
                    except:
                        current_network['signal'] = -100
            
            if current_network:
                networks.append(current_network)
            
            return networks
            
        except Exception as e:
            print(f"扫描WiFi失败: {e}")
            return []
    
    def _start_monitoring(self):
        """开始监控"""
        # 获取选中的WiFi
        selected_indices = self.wifi_listbox.curselection()
        
        if not selected_indices:
            messagebox.showwarning("提示", "请先选择要监控的WiFi网络")
            return
        
        if len(selected_indices) > 10:
            messagebox.showwarning("提示", "最多只能选择10个WiFi")
            return
        
        # 提取SSID
        self.selected_ssids = []
        for idx in selected_indices:
            text = self.wifi_listbox.get(idx)
            ssid = text.split('(')[0].strip()
            self.selected_ssids.append(ssid)
        
        # 初始化数据
        with self.data_lock:
            self.wifi_signals = {}
            self.wifi_colors = {}
            for i, ssid in enumerate(self.selected_ssids):
                self.wifi_signals[ssid] = [-100] * self.radar_directions
                self.wifi_colors[ssid] = self.color_palette[i % len(self.color_palette)]
            
            self.current_direction = 0
        
        # 启动监控线程
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        # 更新按钮状态
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.wifi_listbox.config(state='disabled')
        
        self.status_label.config(text="状态: 扫描中...")
    
    def _stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        
        # 更新按钮状态
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.wifi_listbox.config(state='normal')
        
        self.status_label.config(text="状态: 已停止")
    
    def _monitoring_loop(self):
        """监控循环 - 后台线程"""
        while self.monitoring:
            try:
                # 扫描当前方向的WiFi信号
                networks = self._scan_wifi_networks()
                
                # 更新数据
                with self.data_lock:
                    for ssid in self.selected_ssids:
                        # 查找当前SSID的信号强度
                        found = False
                        for network in networks:
                            if network['ssid'] == ssid:
                                self.wifi_signals[ssid][self.current_direction] = network['signal']
                                found = True
                                break
                        
                        # 如果没找到，设为极弱信号
                        if not found:
                            self.wifi_signals[ssid][self.current_direction] = -100
                    
                    # 更新方向指示
                    direction_deg = self.current_direction * 30
                    self.parent.after(0, lambda: self.direction_label.config(
                        text=f"方向: {direction_deg}°"))
                    
                    # 移动到下一个方向
                    self.current_direction = (self.current_direction + 1) % self.radar_directions
                
                # 更新雷达图
                self.parent.after(0, self._update_radar)
                
                # 等待（根据速度）
                time.sleep(self.scan_interval / self.rotation_speed)
                
            except Exception as e:
                print(f"监控错误: {e}")
                time.sleep(1)
    
    def _update_radar(self):
        """更新雷达图"""
        try:
            with self.data_lock:
                if not self.wifi_signals:
                    return
                
                self.ax.clear()
                
                # 设置雷达图样式
                self.ax.set_theta_direction(-1)
                self.ax.set_theta_zero_location('N')
                
                # 角度数组
                angles = np.linspace(0, 2*np.pi, self.radar_directions, endpoint=False)
                
                # 绘制每个WiFi的信号
                for ssid in self.selected_ssids:
                    values = self.wifi_signals[ssid]
                    color = self.wifi_colors[ssid]
                    
                    # 闭合路径（连接最后一个点到第一个点）
                    values_closed = values + [values[0]]
                    angles_closed = np.append(angles, angles[0])
                    
                    # 绘制填充区域
                    self.ax.fill(angles_closed, values_closed, 
                                color=color, alpha=0.25)
                    
                    # 绘制边线
                    self.ax.plot(angles_closed, values_closed, 
                                color=color, linewidth=2, label=ssid)
                    
                    # 绘制数据点
                    self.ax.scatter(angles, values, 
                                   color=color, s=80, zorder=10, 
                                   edgecolors='white', linewidth=1.5)
                
                # 绘制扫描方向指示器
                current_angle = self.current_direction * (2*np.pi / self.radar_directions)
                self.ax.plot([current_angle, current_angle], [-100, -20], 
                            'r--', linewidth=3, alpha=0.6, label='扫描方向')
                
                # 设置刻度
                self.ax.set_xticks(angles)
                self.ax.set_xticklabels([f'{int(np.degrees(a))}°' for a in angles], 
                                       fontsize=10, fontweight='bold')
                
                self.ax.set_ylim(-100, -20)
                self.ax.set_yticks([-100, -80, -60, -40, -20])
                self.ax.set_yticklabels(['极弱\n-100', '弱\n-80', '中\n-60', '良\n-40', '强\n-20'],
                                       fontsize=8)
                
                # 网格
                self.ax.grid(True, linestyle='--', alpha=0.5)
                
                # 图例
                self.ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), 
                              fontsize=9, framealpha=0.9)
                
                # 标题
                scan_count = sum(1 for v in self.wifi_signals.values() if any(x > -100 for x in v))
                self.ax.set_title(f'WiFi信号雷达扫描 (实时)\n监控{len(self.selected_ssids)}个网络', 
                                 fontsize=12, fontweight='bold', pad=15)
                
                self.canvas.draw()
                
        except Exception as e:
            print(f"更新雷达图失败: {e}")
    
    def _update_speed(self, value):
        """更新扫描速度"""
        self.rotation_speed = float(value)
        self.speed_label.config(text=f"{self.rotation_speed:.1f}x")


# 保持向后兼容的类名
class NetworkOverviewTab(WifiRadarAnalyzer):
    """网络概览标签页（兼容旧接口）"""
    pass
