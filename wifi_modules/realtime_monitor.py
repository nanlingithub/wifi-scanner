"""
实时监控标签页
功能：WiFi频谱图、后台监控、数据导出、统计分析
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
import json
import csv
from datetime import datetime
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.lines
import numpy as np

from .theme import ModernTheme, ModernButton
from . import font_config  # 配置中文字体
from .alerts import SignalAlert  # 声音警报
from .analytics import SignalTrendAnalyzer  # 趋势分析


class RealtimeMonitorTab:
    """实时监控标签页"""
    
    def __init__(self, parent, wifi_analyzer):
        self.parent = parent
        self.wifi_analyzer = wifi_analyzer
        self.frame = ttk.Frame(parent)
        
        # 监控数据
        self.monitoring = False
        self.monitor_thread = None
        self.monitor_data = []  # 存储监控数据
        self.max_data_points = 100
        
        # P1修复: 添加线程锁保护共享数据
        self._data_lock = threading.Lock()
        
        # 声音警报
        self.alert_manager = SignalAlert()
        self.alert_enabled = tk.BooleanVar(value=True)
        self.alert_mute = tk.BooleanVar(value=False)
        
        # 趋势分析
        self.trend_analyzer = SignalTrendAnalyzer()
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        # 顶部控制栏
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        self.start_btn = ModernButton(control_frame, text="▶ 开始监控", 
                                      command=self._start_monitor, style='success')
        self.start_btn.pack(side='left', padx=5)
        
        self.stop_btn = ModernButton(control_frame, text="⏹ 停止监控", 
                                     command=self._stop_monitor, style='danger', state='disabled')
        self.stop_btn.pack(side='left', padx=5)
        
        ModernButton(control_frame, text="🗑️ 清空数据", 
                    command=self._clear_data, style='secondary').pack(side='left', padx=5)
        
        ModernButton(control_frame, text="💾 导出CSV", 
                    command=lambda: self._export_data('csv'), style='primary').pack(side='left', padx=5)
        
        ModernButton(control_frame, text="💾 导出JSON", 
                    command=lambda: self._export_data('json'), style='primary').pack(side='left', padx=5)
        
        ModernButton(control_frame, text="📊 统计分析", 
                    command=self._show_statistics, style='warning').pack(side='left', padx=5)
        
        ModernButton(control_frame, text="📈 趋势分析", 
                    command=self._show_trend_analysis, style='info').pack(side='left', padx=5)
        
        
        # 警报控制
        ttk.Separator(control_frame, orient='vertical').pack(side='left', fill='y', padx=10)
        
        alert_check = ttk.Checkbutton(control_frame, text="🔔 声音警报", 
                                     variable=self.alert_enabled,
                                     command=self._toggle_alert)
        alert_check.pack(side='left', padx=5)
        
        mute_check = ttk.Checkbutton(control_frame, text="🔇 静音", 
                                    variable=self.alert_mute,
                                    command=self._toggle_mute)
        mute_check.pack(side='left', padx=5)
        
        ModernButton(control_frame, text="⚙️ 警报设置", 
                    command=self._show_alert_settings, style='secondary').pack(side='left', padx=5)
        ttk.Label(control_frame, text="采样间隔:", font=('Microsoft YaHei', 9)).pack(side='left', padx=(20, 5))
        self.interval_var = tk.StringVar(value="1秒")
        interval_combo = ttk.Combobox(control_frame, textvariable=self.interval_var,
                                     values=["1秒", "2秒", "5秒", "10秒"], width=8, state='readonly')
        interval_combo.pack(side='left', padx=5)
        
        # 主内容区 - 上下分栏
        main_paned = ttk.PanedWindow(self.frame, orient='vertical')
        main_paned.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 上部：频谱图
        chart_frame = ttk.LabelFrame(main_paned, text="📡 WiFi频谱图", padding=5)
        main_paned.add(chart_frame, weight=2)
        
        self.figure = Figure(figsize=(12, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, chart_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # 下部：监控数据列表
        data_frame = ttk.LabelFrame(main_paned, text="📋 监控数据", padding=5)
        main_paned.add(data_frame, weight=1)
        
        # 创建Treeview
        columns = ("时间", "SSID", "信号强度", "频段", "信道", "BSSID")
        self.monitor_tree = ttk.Treeview(data_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.monitor_tree.heading(col, text=col)
            width = 150 if col == "时间" else 200 if col == "SSID" else 100
            self.monitor_tree.column(col, width=width, anchor='center' if col != 'SSID' else 'w')
        
        scrollbar = ttk.Scrollbar(data_frame, orient='vertical', command=self.monitor_tree.yview)
        self.monitor_tree.configure(yscrollcommand=scrollbar.set)
        
        self.monitor_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 状态栏
        status_frame = ttk.Frame(self.frame)
        status_frame.pack(fill='x', padx=10, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="状态: 就绪", 
                                     font=('Microsoft YaHei', 9))
        self.status_label.pack(side='left')
        
        self._draw_empty_chart()
    
    def _estimate_bandwidth(self, band, channel):
        """估算WiFi频宽（基于频段和信道）"""
        if band == 'N/A' or channel == 'N/A':
            return '20MHz'
        
        # 2.4GHz频段：通常为20MHz或40MHz
        if band == '2.4GHz':
            # 如果是相邻信道，可能使用绑定信道（40MHz）
            # 默认使用20MHz
            return '20/40MHz'
        
        # 5GHz频段：支持20/40/80/160MHz
        elif band == '5GHz':
            try:
                ch = int(channel)
                # 160MHz信道：36-64, 100-128
                if (36 <= ch <= 64) or (100 <= ch <= 128):
                    return '20/40/80/160MHz'
                # 80MHz信道
                elif ch in [36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112, 116, 120, 124, 128, 149, 153, 157, 161]:
                    return '20/40/80MHz'
                else:
                    return '20/40MHz'
            except Exception as e:  # P2修复: 指定异常类型
                print(f'[警告] 频段分析失败但已使用默认值: {e}')  # P2修复: 添加日志
                return '20/40/80MHz'
        
        # 6GHz频段：支持20/40/80/160/320MHz
        elif band == '6GHz':
            return '20-320MHz'
        
        return '20MHz'
    
    def _start_monitor(self):
        """开始监控"""
        if not self.monitoring:
            self.monitoring = True
            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            self.status_label.config(text="状态: 监控中...")
            
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
    
    def _stop_monitor(self):
        """停止监控"""
        self.monitoring = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.status_label.config(text=f"状态: 已停止 (共{len(self.monitor_data)}条数据)")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                interval = int(self.interval_var.get().replace('秒', ''))
                
                # 扫描网络
                networks = self.wifi_analyzer.scan_wifi_networks(force_refresh=True)
                timestamp = datetime.now()
                
                # 记录数据
                for network in networks:
                    # 提取信号强度（dBm）
                    signal_percent = network.get('signal_percent', 0)
                    # 从百分比反推dBm值（近似）：percent = 2 * (signal_dbm + 100)
                    if isinstance(signal_percent, int) and signal_percent > 0:
                        signal_dbm = (signal_percent / 2) - 100
                    else:
                        signal_dbm = -100
                    
                    # 估算频宽（根据频段和信道）
                    band = network.get('band', 'N/A')
                    channel = network.get('channel', 'N/A')
                    bandwidth = self._estimate_bandwidth(band, channel)
                    
                    # 处理SSID（包括隐藏SSID）
                    ssid_raw = network.get('ssid', '')
                    if not ssid_raw or ssid_raw.strip() == '':
                        # 隐藏SSID：使用BSSID的后6位作为标识
                        bssid = network.get('bssid', 'N/A')
                        if bssid and bssid != 'N/A':
                            ssid_display = f"<隐藏:{bssid[-8:]}>"
                        else:
                            ssid_display = '<隐藏网络>'
                    else:
                        ssid_display = ssid_raw
                    
                    data_point = {
                        'timestamp': timestamp,
                        'ssid': ssid_display,
                        'signal': signal_dbm,  # 使用计算的dBm值
                        'signal_percent': signal_percent,
                        'band': band,
                        'channel': channel,
                        'bssid': network.get('bssid', 'N/A'),
                        'bandwidth': bandwidth  # 增加频宽信息
                    }
                    
                    # P1修复: 使用锁保护共享数据
                    with self._data_lock:
                        # P1修复: 限制数据点数量防止内存泄漏
                        MAX_DATA_POINTS = 1000
                        if len(self.monitor_data) >= MAX_DATA_POINTS:
                            self.monitor_data = self.monitor_data[-MAX_DATA_POINTS//2:]  # 保留后半部分
                        self.monitor_data.append(data_point)
                    
                    # 添加到趋势分析器
                    self.trend_analyzer.add_data_point(network.get('ssid', 'N/A'), signal_dbm)
                    
                    # 检查信号警报（仅检查当前连接的WiFi）
                    current_wifi = self.wifi_analyzer.get_current_wifi_info()
                    if current_wifi and network.get('ssid') == current_wifi.get('ssid'):
                        alert_type = self.alert_manager.check_signal(signal_dbm)
                        if alert_type:
                            # 在UI线程显示提示
                            self.parent.after(0, lambda: self._show_alert_notification(alert_type, signal_dbm))
                
                # 限制数据量
                if len(self.monitor_data) > self.max_data_points * 20:
                    self.monitor_data = self.monitor_data[-self.max_data_points * 20:]
                
                # 更新UI
                self.parent.after(0, self._update_ui)
                
                time.sleep(interval)
                
            except Exception as e:
                print(f"监控错误: {e}")
                time.sleep(5)
    
    def _update_ui(self):
        """更新UI"""
        # 更新列表（只显示最近50条）
        self.monitor_tree.delete(*self.monitor_tree.get_children())
        
        recent_data = self.monitor_data[-50:]
        for data in reversed(recent_data):
            signal_dbm = data['signal']
            signal_percent = data['signal_percent']
            # 格式化信号显示
            signal_display = f"{signal_dbm:.0f} dBm ({signal_percent}%)"
            
            values = (
                data['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                data['ssid'],
                signal_display,
                data['band'],
                data['channel'],
                data['bssid']
            )
            self.monitor_tree.insert('', 'end', values=values)
        
        # 更新频谱图
        self._update_spectrum()
        
        # 更新状态
        self.status_label.config(text=f"状态: 监控中... (已记录{len(self.monitor_data)}条数据)")
    
    def _update_spectrum(self):
        """更新频谱图（黑底绿线频谱图，显示Top 10 SSID）"""
        if not self.monitor_data:
            return
        
        # 优化：仅当频段数量变化时才清空重绘
        recent_data = self.monitor_data[-100:]
        band_check = set(data['band'] for data in recent_data if data['band'] in ['2.4GHz', '5GHz', '6GHz'])
        
        # 检测是否需要重新布局
        current_subplots = len(self.figure.axes)
        need_redraw = current_subplots != len(band_check)
        
        if need_redraw:
            self.figure.clear()
        else:
            # 仅清除各个子图的内容，保留布局
            for ax in self.figure.axes:
                ax.clear()
        
        # 按频段分组，同时记录所有SSID及其信号强度（优化：使用defaultdict减少判断）
        from collections import defaultdict
        band_data = {'2.4GHz': defaultdict(list), '5GHz': defaultdict(list), '6GHz': defaultdict(list)}
        band_all_ssids = {'2.4GHz': {}, '5GHz': {}, '6GHz': {}}  # 记录所有SSID: {ssid: (max_signal, channel, bandwidth)}
        
        # 优化：一次遍历完成所有数据处理
        for data in recent_data:
            band = data['band']
            if band not in band_data:
                continue
                
            channel = data['channel']
            if channel == 'N/A' or not channel.isdigit():
                continue
                
            ch_num = int(channel)
            signal = data['signal'] if isinstance(data['signal'], (int, float)) else -100
            ssid = data['ssid']
            bandwidth = data.get('bandwidth', '20MHz')
            
            # 记录信号强度（用于绘制频谱线）
            band_data[band][ch_num].append(signal)
            
            # 记录每个SSID的最强信号、信道和频宽（包括隐藏SSID）
            # 移除N/A过滤，保留所有有效信号
            if ssid and ssid.strip() != '':
                if ssid not in band_all_ssids[band] or signal > band_all_ssids[band][ssid][0]:
                    band_all_ssids[band][ssid] = (signal, ch_num, bandwidth)
        full_channels = {
            '2.4GHz': list(range(1, 14)),  # 1-13信道（中国）
            '5GHz': [36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112, 116, 120, 124, 128, 132, 136, 140, 149, 153, 157, 161, 165],
            '6GHz': list(range(1, 234, 4))  # 6GHz信道
        }
        
        # 绘制子图
        active_bands = [band for band in ['2.4GHz', '5GHz', '6GHz'] if band_data[band]]
        
        if not active_bands:
            self._draw_empty_chart()
            return
        
        for idx, band in enumerate(active_bands, 1):
            ax = self.figure.add_subplot(len(active_bands), 1, idx)
            
            # 设置黑底样式
            ax.set_facecolor('#000000')
            self.figure.patch.set_facecolor('#1a1a1a')
            
            # 使用完整的信道列表
            channels = full_channels.get(band, [])
            if not channels:
                continue
            
            # 计算每个信道的平均和最大信号强度（优化：使用列表推导式和numpy向量化）
            avg_signals = [np.mean(band_data[band][ch]) if ch in band_data[band] and band_data[band][ch] else -100 
                          for ch in channels]
            max_signals = [max(band_data[band][ch]) if ch in band_data[band] and band_data[band][ch] else -100 
                          for ch in channels]
            
            # === 频谱分析仪风格显示（高斯曲线峰值 - 独立山峰） ===
            # 收集所有网络的信息（用于计算带宽）
            network_info = {}
            for ssid, (signal, ch_num, bandwidth_str) in band_all_ssids[band].items():
                if ch_num in channels:
                    # 解析带宽（20MHz, 40MHz, 80MHz, 160MHz）
                    bw_value = 20  # 默认20MHz
                    if 'MHz' in bandwidth_str:
                        try:
                            bw_value = int(bandwidth_str.replace('MHz', '').strip())
                        except Exception as e:  # P2修复: 指定异常类型
                            print(f'[警告] 带宽解析失败，使用默认值20MHz: {e}')  # P2修复: 添加日志
                    network_info[ch_num] = {'signal': signal, 'bandwidth': bw_value, 'ssid': ssid}
            
            # 为每个信道的信号独立绘制高斯峰值（不叠加，保持独立）
            if channels:
                # 为每个有信号的信道单独绘制山峰
                for i, (ch, avg_sig, max_sig) in enumerate(zip(channels, avg_signals, max_signals)):
                    if avg_sig > -100:  # 只处理有信号的信道
                        # 获取带宽信息（影响峰宽）
                        bw = network_info.get(ch, {}).get('bandwidth', 20)
                        
                        # 根据带宽计算高斯峰的标准差（sigma）
                        if band == '2.4GHz':
                            sigma = 0.5 * (bw / 20)  # 2.4GHz信道间隔小，峰较窄
                        elif band == '5GHz':
                            sigma = 1.5 * (bw / 20)  # 5GHz信道间隔4，峰宽适中
                        else:  # 6GHz
                            sigma = 1.0 * (bw / 20)
                        
                        # 为当前信号生成独立的X轴范围（峰值周围±3sigma）
                        x_range = 3 * sigma
                        x_peak = np.linspace(ch - x_range, ch + x_range, 100)
                        
                        # 生成高斯曲线（钟形峰值）
                        peak_height = avg_sig - (-100)  # 转换为正值高度
                        max_height = max_sig - (-100)
                        
                        # 高斯分布函数
                        gaussian_curve = np.exp(-0.5 * ((x_peak - ch) / sigma) ** 2)
                        
                        # 计算Y值
                        y_avg_peak = -100 + peak_height * gaussian_curve
                        y_max_peak = -100 + max_height * gaussian_curve
                        
                        # 根据信号强度选择颜色
                        if avg_sig > -50:
                            color = '#00ff00'  # 优秀-亮绿
                            alpha = 0.8
                        elif avg_sig > -70:
                            color = '#88ff00'  # 良好-黄绿
                            alpha = 0.6
                        else:
                            color = '#ffff00'  # 一般-黄色
                            alpha = 0.4
                        
                        # 绘制填充的独立山峰（从基线-100到峰值）
                        ax.fill_between(x_peak, -100, y_avg_peak, 
                                       color=color, alpha=alpha * 0.5, linewidth=0)
                        
                        # 绘制山峰轮廓线（实线）
                        ax.plot(x_peak, y_avg_peak, color=color, linewidth=2.5, 
                               alpha=alpha, zorder=5)
                        
                        # 绘制峰值保持线（虚线）
                        ax.plot(x_peak, y_max_peak, color='#88ff88', linewidth=1.5, 
                               linestyle='--', alpha=0.5, zorder=4)
                        
                        # 在峰顶添加标记点
                        ax.plot(ch, avg_sig, 'o', color=color, 
                               markersize=6, markeredgecolor='#ffffff', 
                               markeredgewidth=1.5, alpha=0.95, zorder=6)
            
            # 获取当前频段Top 10 SSID
            top_ssids = sorted(band_all_ssids[band].items(), 
                             key=lambda x: x[1][0], reverse=True)[:10]
            
            # 标注Top 10 SSID（在弧形顶部）
            labeled_channels = set()  # 记录已标注的信道，避免重叠
            for ssid, (signal, ch_num, bandwidth) in top_ssids:
                if ch_num in channels and ch_num not in labeled_channels:
                    avg_signal = np.mean(band_data[band][ch_num])
                    
                    # 截断过长的SSID
                    display_ssid = ssid[:10] + '...' if len(ssid) > 10 else ssid
                    
                    # 计算峰值顶部位置（用于标注）
                    peak_top_y = avg_signal  # 峰值就是信号强度本身
                    
                    # 根据信号强度选择标签颜色
                    if signal > -50:
                        label_color = '#00ff00'
                    elif signal > -70:
                        label_color = '#88ff00'
                    else:
                        label_color = '#ffff00'
                    
                    # 显示信道号、SSID、信号强度和频宽
                    label_text = f'CH{ch_num}\n{display_ssid}\n{signal:.0f}dBm\n{bandwidth}'
                    ax.annotate(label_text, 
                               xy=(ch_num, peak_top_y), 
                               xytext=(0, 10),
                               textcoords='offset points',
                               ha='center',
                               fontsize=6.5,
                               color=label_color,
                               bbox=dict(boxstyle='round,pad=0.3', 
                                       facecolor='#000000', 
                                       edgecolor=label_color,
                                       alpha=0.9,
                                       linewidth=1.2))
                    
                    # 添加指示线连接峰值顶部和标签（垂直虚线）
                    ax.plot([ch_num, ch_num], [peak_top_y, peak_top_y + 8], 
                           color=label_color, linewidth=1, alpha=0.7, linestyle=':')
                    
                    labeled_channels.add(ch_num)
            
            # 设置坐标轴样式（绿色）
            ax.spines['bottom'].set_color('#00ff00')
            ax.spines['top'].set_color('#00ff00') 
            ax.spines['left'].set_color('#00ff00')
            ax.spines['right'].set_color('#00ff00')
            ax.tick_params(colors='#00ff00', which='both')
            
            # 设置X轴刻度（根据频段调整显示密度）
            if band == '2.4GHz':
                ax.set_xticks(channels)  # 显示所有信道
                ax.set_xticklabels(channels, fontsize=8)
            elif band == '5GHz':
                # 5GHz信道较多，只显示关键信道标签
                ax.set_xticks(channels)
                labels = [str(ch) if ch % 4 == 0 or ch in [36, 165] else '' for ch in channels]
                ax.set_xticklabels(labels, fontsize=8)
            else:
                ax.set_xticks(channels[::10])  # 6GHz每10个显示一个
            
            # 设置X轴范围（优化：统一使用合理留白，避免信号被截断）
            if channels:
                if band == '2.4GHz':
                    # 2.4G信道间隔1，左右各留0.5单位
                    ax.set_xlim(min(channels) - 0.5, max(channels) + 0.5)
                elif band == '5GHz':
                    # 5GHz信道间隔4，左右各留2个单位（约半个信道间隔）
                    ax.set_xlim(min(channels) - 2, max(channels) + 2)
                else:
                    # 6GHz使用默认留白
                    ax.set_xlim(min(channels) - 1, max(channels) + 1)
            
            # 设置标签和标题（绿色文字）
            ax.set_xlabel('信道', color='#00ff00', fontsize=10)
            ax.set_ylabel('信号强度 (dBm)', color='#00ff00', fontsize=10)
            
            # 标题中显示Top 10数量
            top_count = len(top_ssids)
            ax.set_title(f'{band}频段实时频谱 - 频谱分析仪模式 (Top {top_count} SSID)', 
                        fontsize=12, fontweight='bold', color='#00ff00', pad=10)
            
            # 设置Y轴范围（为弧形显示预留空间）
            ax.set_ylim(-105, -15)
            
            # 添加基线参考线
            ax.axhline(y=-100, color='#00ff00', linestyle='-', alpha=0.4, linewidth=1.5, label='基线')
            
            # 添加信号质量参考线（暗绿色虚线）
            ax.axhline(y=-50, color='#00ff00', linestyle=':', alpha=0.3, linewidth=1)
            ax.axhline(y=-70, color='#00ff00', linestyle=':', alpha=0.3, linewidth=1)
            
            # 添加参考线标签
            ax.text(min(channels) if channels else 1, -50, ' 优秀(-50dBm)', 
                   color='#00ff00', fontsize=7, verticalalignment='center', alpha=0.6)
            ax.text(min(channels) if channels else 1, -70, ' 良好(-70dBm)', 
                   color='#00ff00', fontsize=7, verticalalignment='center', alpha=0.6)
            
            # 网格（暗绿色）
            ax.grid(True, alpha=0.2, color='#00ff00', linestyle=':', axis='x')  # 只显示垂直网格线
            
            # 图例（绿色文字，显示独立峰值）
            import matplotlib.patches
            legend_elements = [
                plt.Line2D([0], [0], color='#00ff00', linewidth=2.5, label='强信号 (>-50dBm)'),
                plt.Line2D([0], [0], color='#88ff00', linewidth=2.5, label='中信号 (-50~-70dBm)'),
                plt.Line2D([0], [0], color='#ffff00', linewidth=2.5, label='弱信号 (<-70dBm)'),
                plt.Line2D([0], [0], color='#88ff88', linewidth=1.5, linestyle='--', label='峰值保持')
            ]
            legend = ax.legend(handles=legend_elements, loc='upper right', fontsize=7, 
                              facecolor='#000000', edgecolor='#00ff00', framealpha=0.85)
            # 设置图例文字颜色为绿色
            if legend:
                for text in legend.get_texts():
                    text.set_color('#00ff00')
        
        self.figure.tight_layout()
        # 优化：使用draw_idle避免阻塞UI线程
        self.canvas.draw_idle()
    
    def _draw_empty_chart(self):
        """绘制空图表（黑底绿字）"""
        self.figure.clear()
        
        # 设置黑底
        self.figure.patch.set_facecolor('#1a1a1a')
        
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('#000000')
        
        # 绿色文字提示
        ax.text(0.5, 0.5, '等待监控数据...', 
               ha='center', va='center', fontsize=16,
               color='#00ff00', weight='bold')
        
        # 隐藏坐标轴但保留黑色背景
        ax.axis('off')
        self.canvas.draw()
    
    def _clear_data(self):
        """清空数据"""
        if messagebox.askyesno("确认", "确定要清空所有监控数据吗?"):
            # P1修复: 使用锁保护共享数据
            with self._data_lock:
                self.monitor_data.clear()
            self.monitor_tree.delete(*self.monitor_tree.get_children())
            self._draw_empty_chart()
            self.status_label.config(text="状态: 数据已清空")
    
    def _export_data(self, format_type):
        """导出数据"""
        if not self.monitor_data:
            messagebox.showwarning("提示", "没有可导出的数据")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_name = f"wifi_monitor_{timestamp}.{format_type}"
        
        filename = filedialog.asksaveasfilename(
            defaultextension=f".{format_type}",
            initialfile=default_name,
            filetypes=[(f"{format_type.upper()}文件", f"*.{format_type}"), ("所有文件", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            if format_type == 'csv':
                self._export_csv(filename)
            elif format_type == 'json':
                self._export_json(filename)
            
            messagebox.showinfo("成功", f"数据已导出到:\n{filename}")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")
    
    def _export_csv(self, filename):
        """导出为CSV"""
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['时间', 'SSID', '信号强度(dBm)', '信号强度(%)', '频段', '信道', 'BSSID'])
            
            for data in self.monitor_data:
                writer.writerow([
                    data['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                    data['ssid'],
                    data['signal'],
                    data['signal_percent'],
                    data['band'],
                    data['channel'],
                    data['bssid']
                ])
    
    def _export_json(self, filename):
        """导出为JSON"""
        export_data = []
        for data in self.monitor_data:
            export_data.append({
                'timestamp': data['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                'ssid': data['ssid'],
                'signal_dbm': data['signal'],
                'signal_percent': data['signal_percent'],
                'band': data['band'],
                'channel': data['channel'],
                'bssid': data['bssid']
            })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    def _show_statistics(self):
        """显示统计信息"""
        if not self.monitor_data:
            # 提供更详细的提示信息
            if not self.monitoring:
                message = "没有可统计的数据\n\n请先点击'开始监控'按钮，等待几秒钟收集WiFi数据后再查看统计信息。"
            else:
                message = "监控已启动，但暂时没有数据\n\n可能原因：\n1. 监控刚启动，请稍等片刻\n2. WiFi扫描失败，请检查WiFi适配器\n3. 数据被清空，请等待重新收集"
            
            messagebox.showwarning("提示", message)
            return
        
        # 统计分析
        unique_ssids = set(d['ssid'] for d in self.monitor_data)
        signals = [d['signal'] for d in self.monitor_data]
        
        stats = f"""=== 监控统计 ===

数据点数: {len(self.monitor_data)}
监控网络数: {len(unique_ssids)}
时间跨度: {self.monitor_data[0]['timestamp'].strftime('%H:%M:%S')} - {self.monitor_data[-1]['timestamp'].strftime('%H:%M:%S')}

信号强度统计:
  最大值: {max(signals)} dBm
  最小值: {min(signals)} dBm
  平均值: {np.mean(signals):.1f} dBm
  标准差: {np.std(signals):.1f} dBm

频段分布:
"""
        
        band_count = {}
        for data in self.monitor_data:
            band = data['band']
            band_count[band] = band_count.get(band, 0) + 1
        
        for band, count in sorted(band_count.items()):
            percentage = count / len(self.monitor_data) * 100
            stats += f"  {band}: {count} ({percentage:.1f}%)\n"
        
        # 创建统计窗口
        stats_window = tk.Toplevel(self.frame)
        stats_window.title("统计分析")
        stats_window.geometry("400x400")
        
        text = tk.Text(stats_window, font=('Microsoft YaHei', 10), padx=10, pady=10)
        text.pack(fill='both', expand=True)
        text.insert('1.0', stats)
        text.config(state='disabled')
    
    def _toggle_alert(self):
        """切换警报启用状态"""
        if self.alert_enabled.get():
            self.alert_manager.enable()
        else:
            self.alert_manager.disable()
    
    def _toggle_mute(self):
        """切换静音模式"""
        is_muted = self.alert_manager.toggle_mute()
        self.alert_mute.set(is_muted)
    
    def _show_alert_notification(self, alert_type, signal_dbm):
        """显示警报通知"""
        messages = {
            'warning': f'⚠️ 信号警告\n\n当前信号强度: {signal_dbm:.1f} dBm\n信号较弱，可能影响网络体验',
            'critical': f'🚨 信号严重警告\n\n当前信号强度: {signal_dbm:.1f} dBm\n信号很弱，建议调整位置或检查路由器',
            'recover': f'✅ 信号恢复\n\n当前信号强度: {signal_dbm:.1f} dBm\n信号已恢复正常',
        }
        
        message = messages.get(alert_type, '')
        if message:
            # 更新状态栏显示警报信息
            self.status_label.config(text=f"状态: {message.split(chr(10))[0]}")
    
    def _show_alert_settings(self):
        """显示警报设置对话框"""
        settings_window = tk.Toplevel(self.parent)
        settings_window.title("警报设置")
        settings_window.geometry("450x350")
        settings_window.transient(self.parent)
        settings_window.grab_set()
        
        # 标题
        ttk.Label(settings_window, text="🔔 声音警报设置", 
                 font=('Microsoft YaHei', 14, 'bold')).pack(pady=10)
        
        # 设置框架
        frame = ttk.Frame(settings_window, padding=20)
        frame.pack(fill='both', expand=True)
        
        # 警告阈值设置
        ttk.Label(frame, text="⚠️ 警告阈值 (dBm):", 
                 font=('Microsoft YaHei', 10)).grid(row=0, column=0, sticky='w', pady=10)
        
        warning_var = tk.IntVar(value=self.alert_manager.warning_threshold)
        warning_scale = ttk.Scale(frame, from_=-90, to=-50, variable=warning_var, 
                                 orient='horizontal', length=200)
        warning_scale.grid(row=0, column=1, padx=10)
        
        warning_label = ttk.Label(frame, text=f"{warning_var.get()} dBm")
        warning_label.grid(row=0, column=2)
        
        # 严重警告阈值
        ttk.Label(frame, text="🚨 严重警告阈值 (dBm):", 
                 font=('Microsoft YaHei', 10)).grid(row=1, column=0, sticky='w', pady=10)
        
        critical_var = tk.IntVar(value=self.alert_manager.critical_threshold)
        critical_scale = ttk.Scale(frame, from_=-100, to=-60, variable=critical_var, 
                                  orient='horizontal', length=200)
        critical_scale.grid(row=1, column=1, padx=10)
        
        critical_label = ttk.Label(frame, text=f"{critical_var.get()} dBm")
        critical_label.grid(row=1, column=2)
        
        # 添加提示标签
        hint_label = ttk.Label(frame, text="提示：严重警告阈值必须小于警告阈值", 
                              font=('Microsoft YaHei', 8), foreground='gray')
        hint_label.grid(row=2, column=0, columnspan=3, sticky='w', pady=(0, 10))
        
        def update_warning_label(*args):
            val = warning_var.get()
            warning_label.config(text=f"{val} dBm")
            # 如果警告值<=严重值，自动调整严重值
            if val <= critical_var.get():
                critical_var.set(val - 10)  # 保持10dBm差距
        
        def update_critical_label(*args):
            val = critical_var.get()
            critical_label.config(text=f"{val} dBm")
            # 如果严重值>=警告值，自动调整警告值
            if val >= warning_var.get():
                warning_var.set(val + 10)  # 保持10dBm差距
        
        warning_var.trace('w', update_warning_label)
        critical_var.trace('w', update_critical_label)
        
        # 冷却时间
        ttk.Label(frame, text="⏱️ 警报间隔 (秒):", 
                 font=('Microsoft YaHei', 10)).grid(row=3, column=0, sticky='w', pady=10)
        
        cooldown_var = tk.IntVar(value=self.alert_manager.alert_cooldown)
        cooldown_spin = ttk.Spinbox(frame, from_=1, to=60, textvariable=cooldown_var, width=10)
        cooldown_spin.grid(row=3, column=1, sticky='w', padx=10)
        
        # 测试按钮
        test_frame = ttk.Frame(frame)
        test_frame.grid(row=4, column=0, columnspan=3, pady=15)
        
        ModernButton(test_frame, text="🔊 测试警告音", 
                    command=lambda: self.alert_manager.test_alert('warning'),
                    style='warning').pack(side='left', padx=5)
        
        ModernButton(test_frame, text="🚨 测试严重警告音", 
                    command=lambda: self.alert_manager.test_alert('critical'),
                    style='danger').pack(side='left', padx=5)
        
        # 底部按钮
        button_frame = ttk.Frame(settings_window)
        button_frame.pack(fill='x', padx=20, pady=10)
        
        def save_settings():
            warning = warning_var.get()
            critical = critical_var.get()
            
            # 验证阈值合理性
            if warning <= critical:
                messagebox.showerror("错误", 
                    f"警告阈值({warning} dBm)必须大于严重警告阈值({critical} dBm)\n\n"
                    "请调整设置后再保存")
                return
            
            if critical < -100 or critical > -60:
                messagebox.showerror("错误", "严重警告阈值必须在 -100 到 -60 dBm 之间")
                return
            
            if warning < -90 or warning > -50:
                messagebox.showerror("错误", "警告阈值必须在 -90 到 -50 dBm 之间")
                return
            
            # 保存设置
            self.alert_manager.set_thresholds(warning, critical)
            self.alert_manager.alert_cooldown = cooldown_var.get()
            
            messagebox.showinfo("成功", 
                f"警报设置已保存\n\n"
                f"警告阈值: {warning} dBm\n"
                f"严重警告阈值: {critical} dBm\n"
                f"警报间隔: {cooldown_var.get()} 秒")
            settings_window.destroy()
        
        ModernButton(button_frame, text="✅ 保存", command=save_settings, 
                    style='success').pack(side='left', padx=5)
        
        ModernButton(button_frame, text="❌ 取消", command=settings_window.destroy, 
                    style='secondary').pack(side='left', padx=5)
    
    def _show_trend_analysis(self):
        """显示趋势分析窗口"""
        trend_window = tk.Toplevel(self.parent)
        trend_window.title("📈 信号趋势分析")
        trend_window.geometry("1200x700")
        trend_window.transient(self.parent)
        
        # 顶部控制栏
        control_frame = ttk.Frame(trend_window, padding=10)
        control_frame.pack(fill='x')
        
        ttk.Label(control_frame, text="选择WiFi:", 
                 font=('Microsoft YaHei', 10)).pack(side='left', padx=5)
        
        # 获取可用的SSID列表
        available_ssids = self.trend_analyzer.get_available_ssids(hours=168)  # 7天
        if not available_ssids:
            messagebox.showinfo("提示", "暂无历史数据\n\n请先开始监控以收集数据")
            trend_window.destroy()
            return
        
        ssid_var = tk.StringVar(value=available_ssids[0])
        ssid_combo = ttk.Combobox(control_frame, textvariable=ssid_var,
                                  values=available_ssids, width=30, state='readonly')
        ssid_combo.pack(side='left', padx=5)
        
        ttk.Label(control_frame, text="时间范围:", 
                 font=('Microsoft YaHei', 10)).pack(side='left', padx=(20, 5))
        
        hours_var = tk.StringVar(value="24小时")
        hours_combo = ttk.Combobox(control_frame, textvariable=hours_var,
                                   values=["1小时", "6小时", "12小时", "24小时", "48小时", "7天"],
                                   width=10, state='readonly')
        hours_combo.pack(side='left', padx=5)
        
        # 图表容器
        chart_frame = ttk.Frame(trend_window)
        chart_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
        
        canvas_container = ttk.Frame(chart_frame)
        canvas_container.pack(fill='both', expand=True)
        
        # 统计信息框
        stats_frame = ttk.LabelFrame(trend_window, text="📊 统计信息", padding=10)
        stats_frame.pack(fill='x', padx=10, pady=5)
        
        stats_text = tk.Text(stats_frame, height=6, font=('Microsoft YaHei', 9))
        stats_text.pack(fill='x')
        
        def update_chart():
            """更新图表"""
            # 清空容器
            for widget in canvas_container.winfo_children():
                widget.destroy()
            
            ssid = ssid_var.get()
            hours_str = hours_var.get()
            hours_map = {"1小时": 1, "6小时": 6, "12小时": 12, 
                        "24小时": 24, "48小时": 48, "7天": 168}
            hours = hours_map.get(hours_str, 24)
            
            # 生成图表
            fig = self.trend_analyzer.generate_trend_chart(ssid, hours)
            canvas = FigureCanvasTkAgg(fig, canvas_container)
            canvas.draw()
            canvas.get_tk_widget().pack(fill='both', expand=True)
            
            # 添加工具栏
            toolbar = NavigationToolbar2Tk(canvas, canvas_container)
            toolbar.update()
            
            # 更新统计信息
            trend_data = self.trend_analyzer.get_trend_data(ssid, hours)
            if trend_data['stats']:
                stats = trend_data['stats']
                stats_info = f"""SSID: {ssid}
时间范围: 最近{hours_str}
数据点数: {stats['data_points']}
时间跨度: {stats['time_span']:.1f} 小时

信号强度统计:
  最大值: {stats['max']:.1f} dBm (时间: {stats['max_time'].strftime('%Y-%m-%d %H:%M:%S')})
  最小值: {stats['min']:.1f} dBm (时间: {stats['min_time'].strftime('%Y-%m-%d %H:%M:%S')})
  平均值: {stats['mean']:.1f} dBm
  标准差: {stats['std']:.1f} dBm
"""
                stats_text.delete('1.0', 'end')
                stats_text.insert('1.0', stats_info)
        
        # 刷新和导出按钮
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(side='right', padx=5)
        
        ModernButton(button_frame, text="🔄 刷新", 
                    command=update_chart, style='primary').pack(side='left', padx=2)
        
        def export_data():
            ssid = ssid_var.get()
            hours_str = hours_var.get()
            hours_map = {"1小时": 1, "6小时": 6, "12小时": 12, 
                        "24小时": 24, "48小时": 48, "7天": 168}
            hours = hours_map.get(hours_str, 24)
            
            try:
                filename = self.trend_analyzer.export_to_csv(ssid, hours)
                messagebox.showinfo("导出成功", f"数据已导出到:\n{filename}")
            except Exception as e:
                messagebox.showerror("导出失败", str(e))
        
        ModernButton(button_frame, text="💾 导出CSV", 
                    command=export_data, style='success').pack(side='left', padx=2)
        
        def clear_data():
            if messagebox.askyesno("确认", f"确定要清空 {ssid_var.get()} 的历史数据吗？"):
                self.trend_analyzer.clear_history(ssid_var.get())
                messagebox.showinfo("成功", "历史数据已清空")
                trend_window.destroy()
        
        ModernButton(button_frame, text="🗑️ 清空数据", 
                    command=clear_data, style='danger').pack(side='left', padx=2)
        
        # 绑定事件
        ssid_combo.bind('<<ComboboxSelected>>', lambda e: update_chart())
        hours_combo.bind('<<ComboboxSelected>>', lambda e: update_chart())
        
        # 初始加载
        update_chart()
    
    def get_frame(self):
        """获取框架"""
        return self.frame

