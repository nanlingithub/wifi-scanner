"""
信道分析标签页（增强版）
功能：全球8个地区的WiFi信道分析、2.4/5/6GHz频段对比、智能推荐
优化：IEEE 802.11标准干扰算法、RSSI加权、DFS标识、信道绑定、热力图、AP规划
新增：WiFi 6E/7协议支持、320MHz信道绑定、6GHz UNII频段
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.patches as mpatches
import numpy as np
from datetime import datetime
from collections import deque

from .theme import ModernTheme, ModernButton, ModernCard, create_section_title
from . import font_config  # 配置中文字体
from .analytics.channel_utilization import ChannelUtilizationAnalyzer


class ChannelAnalysisTab:
    """信道分析标签页（增强版）"""
    
    # WiFi协议标准定义
    WIFI_STANDARDS = {
        'WiFi 4': '802.11n',
        'WiFi 5': '802.11ac',
        'WiFi 6': '802.11ax (2.4/5GHz)',
        'WiFi 6E': '802.11ax (6GHz)',
        'WiFi 7': '802.11be (2.4/5/6GHz)'
    }
    
    # ✅ P1: DFS信道范围（需雷达检测）
    # 根据 IEEE 802.11 标准，5GHz DFS 信道为 UNII-2(52-64) 和 UNII-2E(100-144)
    # 68~96 在任何地区规范中均不存在，已从原 range(52,145,4) 中剔除
    DFS_CHANNELS = [52, 56, 60, 64,                          # UNII-2
                    100, 104, 108, 112, 116, 120, 124, 128,  # UNII-2 Extended
                    132, 136, 140, 144]                      # UNII-2 Extended (高段)
    
    # ✅ WiFi 6E/7: 信道绑定配置（支持20/40/80/160/320MHz）
    CHANNEL_40MHZ_PAIRS = [
        ([36, 40], 38), ([44, 48], 46), ([52, 56], 54),
        ([60, 64], 62), ([100, 104], 102), ([108, 112], 110),
        ([116, 120], 118), ([124, 128], 126), ([132, 136], 134),
        ([149, 153], 151), ([157, 161], 159)
    ]
    
    CHANNEL_80MHZ_GROUPS = [
        ([36, 40, 44, 48], 42), ([52, 56, 60, 64], 58),
        ([100, 104, 108, 112], 106), ([116, 120, 124, 128], 122),
        ([149, 153, 157, 161], 155)
    ]
    
    # WiFi 6E/7: 160MHz信道绑定（5GHz + 6GHz）
    CHANNEL_160MHZ_GROUPS = [
        ([36, 40, 44, 48, 52, 56, 60, 64], 50),
        ([100, 104, 108, 112, 116, 120, 124, 128], 114)
    ]
    
    # WiFi 7: 320MHz超宽信道绑定（仅6GHz）
    CHANNEL_320MHZ_GROUPS = [
        ([1, 5, 9, 13, 17, 21, 25, 29, 33, 37, 41, 45, 49, 53, 57, 61], 31),
        ([65, 69, 73, 77, 81, 85, 89, 93, 97, 101, 105, 109, 113, 117, 121, 125], 95),
        ([129, 133, 137, 141, 145, 149, 153, 157, 161, 165, 169, 173, 177, 181, 185, 189], 159)
    ]
    
    # 6GHz UNII频段划分（WiFi 6E/7）
    UNII_BANDS_6GHZ = {
        'UNII-5': list(range(1, 94, 4)),      # 5925-6425 MHz
        'UNII-6': list(range(97, 118, 4)),    # 6425-6525 MHz
        'UNII-7': list(range(121, 190, 4)),   # 6525-6875 MHz
        'UNII-8': list(range(193, 234, 4))    # 6875-7125 MHz
    }
    
    # 全球WiFi信道配置（更新为WiFi 6E/7标准）
    CHANNEL_REGIONS = {
        "中国": {
            "2.4GHz": list(range(1, 14)),
            "5GHz": [36, 40, 44, 48, 52, 56, 60, 64, 149, 153, 157, 161, 165],
            "6GHz": list(range(1, 234, 4)),  # 更新：支持6GHz全频段
            "protocols": ["WiFi 4", "WiFi 5", "WiFi 6", "WiFi 6E", "WiFi 7"]
        },
        "美国": {
            "2.4GHz": list(range(1, 12)),
            "5GHz": [36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112, 116, 120, 124, 128, 132, 136, 140, 144, 149, 153, 157, 161, 165],
            "6GHz": list(range(1, 234, 4)),  # 5925-7125 MHz
            "protocols": ["WiFi 4", "WiFi 5", "WiFi 6", "WiFi 6E", "WiFi 7"]
        },
        "欧洲": {
            "2.4GHz": list(range(1, 14)),
            "5GHz": [36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112, 116, 120, 124, 128, 132, 136, 140],
            "6GHz": list(range(1, 234, 4)),  # 5945-7125 MHz
            "protocols": ["WiFi 4", "WiFi 5", "WiFi 6", "WiFi 6E", "WiFi 7"]
        },
        "日本": {
            "2.4GHz": list(range(1, 15)),
            "5GHz": [36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112, 116, 120, 124, 128, 132, 136, 140],
            "6GHz": list(range(1, 190, 4)),  # 部分6GHz频段
            "protocols": ["WiFi 4", "WiFi 5", "WiFi 6", "WiFi 6E"]
        },
        "韩国": {
            "2.4GHz": list(range(1, 14)),
            "5GHz": [36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112, 116, 120, 124, 128, 149, 153, 157, 161, 165],
            "6GHz": list(range(1, 234, 4)),
            "protocols": ["WiFi 4", "WiFi 5", "WiFi 6", "WiFi 6E", "WiFi 7"]
        },
        "英国": {
            "2.4GHz": list(range(1, 14)),
            "5GHz": [36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112, 116, 120, 124, 128, 132, 136, 140],
            "6GHz": list(range(1, 234, 4)),
            "protocols": ["WiFi 4", "WiFi 5", "WiFi 6", "WiFi 6E", "WiFi 7"]
        },
        "澳大利亚": {
            "2.4GHz": list(range(1, 14)),
            "5GHz": [36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112, 116, 120, 124, 128, 132, 136, 140, 149, 153, 157, 161, 165],
            "6GHz": list(range(1, 190, 4)),
            "protocols": ["WiFi 4", "WiFi 5", "WiFi 6", "WiFi 6E"]
        },
        "印度": {
            "2.4GHz": list(range(1, 14)),
            "5GHz": [36, 40, 44, 48, 52, 56, 60, 64, 149, 153, 157, 161, 165],
            "6GHz": list(range(1, 94, 4)),  # 仅UNII-5频段
            "protocols": ["WiFi 4", "WiFi 5", "WiFi 6", "WiFi 6E"]
        }
    }
    
    def __init__(self, parent, wifi_analyzer):
        self.parent = parent
        self.wifi_analyzer = wifi_analyzer
        self.frame = ttk.Frame(parent)
        self.channel_usage = {}  # 信道占用情况（增强：包含weight）
        self.utilization_analyzer = ChannelUtilizationAnalyzer()  # 利用率分析器
        self.last_networks = []  # 保存最近扫描的网络列表
        
        # ✅ P2: 时间序列趋势追踪
        self.channel_history = deque(maxlen=288)  # 24小时历史（5分钟间隔）
        
        # ✅ WiFi 6E/7: 信道绑定检测结果（扩展支持）
        self.bonding_stats = {
            '20MHz': 0,   # 标准信道
            '40MHz': 0,   # WiFi 4/5/6
            '80MHz': 0,   # WiFi 5/6
            '160MHz': 0,  # WiFi 6/6E
            '320MHz': 0   # WiFi 7
        }
        
        # ✅ Phase 1优化: 实时监控
        self.realtime_monitoring = False
        self.monitor_thread = None
        self.monitor_interval = 10  # 默认10秒
        import threading as _threading
        self._monitor_stop_event = _threading.Event()
        self.last_scan_time = None
        self.quality_history = deque(maxlen=50)  # 质量历史
        
        # ✅ Phase 2优化: 异步热力图生成器
        self.heatmap_generator = AsyncHeatmapGenerator(cache_size=10)
        
        # ✅ Phase 2优化: 质量告警系统
        self.quality_alert_enabled = False
        self.alert_thresholds = {
            'interference_score': 40,  # 干扰评分低于40告警
            'channel_congestion': 5,   # 信道超过5个网络告警
            'quality_drop': 20         # 质量下降超过20分告警
        }
        self.baseline_quality = {}  # 质量基线（首次扫描）
        self.alert_history = deque(maxlen=50)  # 告警历史
        
        # ✅ Phase 2优化: 6GHz专项优化
        self.ghz6_coverage_model = None
        self.ghz6_attenuation_db_per_wall = 8.0  # 6GHz穿墙衰减（dB）
        self.ghz5_attenuation_db_per_wall = 5.0  # 5GHz穿墙衰减（dB）
        
        self._setup_ui()
    
    def get_wifi_protocol_info(self, channel, band, bandwidth=20):
        """获取WiFi协议信息"""
        protocols = []
        
        if band == '2.4GHz':
            protocols = ['WiFi 4', 'WiFi 6']
            if bandwidth >= 40:
                protocols = ['WiFi 6']
        elif band == '5GHz':
            if bandwidth >= 160:
                protocols = ['WiFi 6']
            elif bandwidth >= 80:
                protocols = ['WiFi 5', 'WiFi 6']
            elif bandwidth >= 40:
                protocols = ['WiFi 4', 'WiFi 5', 'WiFi 6']
            else:
                protocols = ['WiFi 4', 'WiFi 5', 'WiFi 6']
        elif band == '6GHz':
            if bandwidth >= 320:
                protocols = ['WiFi 7']
            elif bandwidth >= 160:
                protocols = ['WiFi 6E', 'WiFi 7']
            else:
                protocols = ['WiFi 6E', 'WiFi 7']
        
        return protocols
    
    def _setup_ui(self):
        """设置UI"""
        # 顶部控制栏
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(control_frame, text="选择地区:", font=('Microsoft YaHei', 10)).pack(side='left', padx=5)
        
        self.region_var = tk.StringVar(value="中国")
        regions = ["全部地区对比"] + list(self.CHANNEL_REGIONS.keys())
        region_combo = ttk.Combobox(control_frame, textvariable=self.region_var,
                                    values=regions, width=15, state='readonly')
        region_combo.pack(side='left', padx=5)
        region_combo.bind('<<ComboboxSelected>>', lambda e: self._analyze_channels())
        
        ModernButton(control_frame, text="🔍 分析信道", 
                    command=self._analyze_channels, style='primary').pack(side='left', padx=5)
        
        ModernButton(control_frame, text="💡 智能推荐", 
                    command=self._recommend_channel, style='success').pack(side='left', padx=5)
        
        ModernButton(control_frame, text="📊 利用率仪表盘", 
                    command=self._show_utilization_dashboard, style='info').pack(side='left', padx=5)
        
        # ✅ WiFi 6E/7: 协议支持信息
        ModernButton(control_frame, text="📡 WiFi协议", 
                    command=self._show_protocol_info, style='info').pack(side='left', padx=5)
        
        # ✅ P2: 新增功能按钮
        ModernButton(control_frame, text="🔥 干扰热力图", 
                    command=self._show_heatmap, style='warning').pack(side='left', padx=5)
        
        ModernButton(control_frame, text="📈 历史趋势", 
                    command=self._show_trend_chart, style='info').pack(side='left', padx=5)
        
        ModernButton(control_frame, text="🏢 AP规划", 
                    command=self._show_ap_planner, style='primary').pack(side='left', padx=5)
        
        # ✅ Phase 2优化: 质量告警系统按钮
        ModernButton(control_frame, text="🔔 质量告警", 
                    command=self._show_quality_alert_config, style='danger').pack(side='left', padx=5)
        
        # ✅ Phase 2优化: 6GHz专项优化按钮
        ModernButton(control_frame, text="🌐 6GHz优化", 
                    command=self._show_6ghz_optimization, style='success').pack(side='left', padx=5)
        
        # ✅ Phase 1优化: 实时监控控制面板
        monitor_frame = ttk.LabelFrame(control_frame, text="🔄 实时监控", padding=5)
        monitor_frame.pack(side='right', padx=10)
        
        self.realtime_monitor_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(monitor_frame, text="启用", 
                       variable=self.realtime_monitor_var,
                       command=self._toggle_realtime_monitor).pack(side='left', padx=3)
        
        ttk.Label(monitor_frame, text="间隔:", font=('Microsoft YaHei', 9)).pack(side='left', padx=3)
        self.monitor_interval_var = tk.StringVar(value="10秒")
        interval_combo = ttk.Combobox(monitor_frame, textvariable=self.monitor_interval_var,
                                     values=["5秒", "10秒", "30秒", "60秒"],
                                     width=6, state='readonly')
        interval_combo.pack(side='left', padx=3)
        interval_combo.bind('<<ComboboxSelected>>', self._update_monitor_interval)
        
        self.monitor_status_label = ttk.Label(monitor_frame, text="⏸️ 未启动", 
                                             font=('Microsoft YaHei', 9), foreground='gray')
        self.monitor_status_label.pack(side='left', padx=5)
        
        # 图表区域
        self.figure = Figure(figsize=(12, 8), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, self.frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=5)
        
        # 分析结果文本
        result_frame = ttk.LabelFrame(self.frame, text="📊 分析结果", padding=10)
        result_frame.pack(fill='x', padx=10, pady=5)
        
        self.result_text = tk.Text(result_frame, height=6, font=('Microsoft YaHei', 9))
        self.result_text.pack(fill='x')
        
        self._draw_empty_chart()
    
    def _analyze_channels(self):
        """分析信道占用（增强：RSSI加权）"""
        try:
            # 扫描网络
            networks = self.wifi_analyzer.scan_wifi_networks(force_refresh=True)
            self.last_networks = networks  # 保存网络列表供利用率分析使用
            
            # ✅ P0: RSSI加权统计
            self.channel_usage = {'2.4GHz': {}, '5GHz': {}, '6GHz': {}}
            
            for network in networks:
                channel = network.get('channel', 'N/A')
                band = network.get('band', 'N/A')
                
                if channel != 'N/A' and str(channel).isdigit():
                    ch_num = int(channel)
                    
                    # ✅ P0: 计算RSSI权重
                    signal_dbm = self._parse_signal_dbm(network.get('signal', '-100'))
                    weight = max(0, min(1, (signal_dbm + 90) / 60))  # -30dBm=1.0, -90dBm=0.0
                    
                    if band in self.channel_usage:
                        if ch_num not in self.channel_usage[band]:
                            self.channel_usage[band][ch_num] = {'count': 0, 'weight': 0}
                        
                        self.channel_usage[band][ch_num]['count'] += 1
                        self.channel_usage[band][ch_num]['weight'] += weight
            
            # ✅ P1: 检测信道绑定
            self.bonding_stats = self._detect_channel_bonding(networks)
            
            # ✅ P2: 记录历史快照
            self.channel_history.append((datetime.now(), self.channel_usage.copy()))
            
            # 绘制图表
            region = self.region_var.get()
            if region == "全部地区对比":
                self._draw_global_comparison()
            else:
                self._draw_single_region(region)
            
            # 显示分析结果
            self._show_analysis_result()
            
        except Exception as e:
            messagebox.showerror("错误", f"分析失败: {str(e)}")
    
    def _get_channel_count(self, band, channel):
        """安全获取信道占用数量"""
        data = self.channel_usage.get(band, {}).get(channel, 0)
        if isinstance(data, dict):
            return data.get('count', 0)
        return data if isinstance(data, int) else 0
    
    def _draw_single_region(self, region):
        """绘制单个地区的信道分析"""
        self.figure.clear()
        
        region_channels = self.CHANNEL_REGIONS.get(region, {})
        bands = ['2.4GHz', '5GHz', '6GHz']
        
        # 确定需要几个子图
        subplot_count = sum(1 for band in bands if region_channels.get(band))
        
        if subplot_count == 0:
            self._draw_empty_chart()
            return
        
        plot_idx = 1
        
        for band in bands:
            channels = region_channels.get(band, [])
            if not channels:
                continue
            
            ax = self.figure.add_subplot(subplot_count, 1, plot_idx)
            plot_idx += 1
            
            # 准备数据
            usage_data = [self.channel_usage.get(band, {}).get(ch, {'count': 0, 'weight': 0}) for ch in channels]
            usage_counts = [data.get('count', 0) if isinstance(data, dict) else data for data in usage_data]
            
            # 绘制柱状图
            colors = ['#e74c3c' if count > 3 else '#f39c12' if count > 1 else '#27ae60' 
                     for count in usage_counts]
            
            bars = ax.bar(range(len(channels)), usage_counts, color=colors, alpha=0.7)
            
            # 设置标签
            ax.set_xlabel('信道')
            ax.set_ylabel('占用数量')
            ax.set_title(f'{region} - {band}频段信道占用情况', 
                        fontsize=12, fontweight='bold')
            ax.set_xticks(range(len(channels)))
            ax.set_xticklabels(channels, rotation=45 if len(channels) > 20 else 0)
            ax.grid(axis='y', alpha=0.3)
            
            # 添加数值标签
            for bar, count in zip(bars, usage_counts):
                if count > 0:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{int(count)}', ha='center', va='bottom', fontsize=8)
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def _draw_global_comparison(self):
        """绘制全球地区对比"""
        self.figure.clear()
        
        regions = list(self.CHANNEL_REGIONS.keys())
        bands = ['2.4GHz', '5GHz']
        
        for idx, band in enumerate(bands, 1):
            ax = self.figure.add_subplot(2, 1, idx)
            
            # 统计每个地区的信道数量和占用情况
            region_data = []
            for region in regions:
                channels = self.CHANNEL_REGIONS[region].get(band, [])
                total_channels = len(channels)
                # 修复：正确获取字典中的count值
                used_channels = sum(1 for ch in channels 
                                   if self._get_channel_count(band, ch) > 0)
                region_data.append((total_channels, used_channels))
            
            # 绘制分组柱状图
            x = np.arange(len(regions))
            width = 0.35
            
            total_bars = ax.bar(x - width/2, [d[0] for d in region_data], width, 
                               label='可用信道', color='#3498db', alpha=0.7)
            used_bars = ax.bar(x + width/2, [d[1] for d in region_data], width,
                              label='已占用信道', color='#e74c3c', alpha=0.7)
            
            ax.set_xlabel('地区')
            ax.set_ylabel('信道数量')
            ax.set_title(f'全球{band}频段信道对比', 
                        fontsize=12, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels(regions, rotation=45)
            ax.legend()
            ax.grid(axis='y', alpha=0.3)
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def _draw_empty_chart(self):
        """绘制空图表"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, '点击"分析信道"开始', 
               ha='center', va='center', fontsize=16,
)
        ax.axis('off')
        self.canvas.draw()
    
    def _show_analysis_result(self):
        """✅ Phase 1优化: 显示分析结果（增强版）"""
        self.result_text.delete('1.0', 'end')
        
        result = "╔══════════════════════════════════════════════════════════╗\n"
        result += "║              📊 信道分析结果（增强版）                  ║\n"
        result += "╚══════════════════════════════════════════════════════════╝\n\n"
        
        _quality_scores = []  # ✅ P1修复: 收集各频段最佳评分，用于写入quality_history
        for band in ['2.4GHz', '5GHz', '6GHz']:
            usage = self.channel_usage.get(band, {})
            if not usage:
                continue
            
            # 计算干扰评分
            region = self.region_var.get()
            if region != "全部地区对比":
                available = self.CHANNEL_REGIONS.get(region, {}).get(band, [])
                if available:
                    # 找最佳信道
                    scores = {}
                    for ch in available:
                        scores[ch] = self._calculate_interference_score(ch, usage, band)
                    
                    best_channel = max(scores.items(), key=lambda x: x[1])
                    best_score = best_channel[1]
                    _quality_scores.append(best_score)  # ✅ 收集频段最佳评分
                    
                    result += f"{'📶' if band == '2.4GHz' else '📡' if band == '5GHz' else '🌐'} {band}频段:\n"
                    result += f"  • 占用信道: {len(usage)} 个\n"
                    
                    # 安全提取count值进行比较
                    most_used = max(usage.items(), key=lambda x: self._get_channel_count(band, x[0]))
                    count = self._get_channel_count(band, most_used[0])
                    
                    # 计算拥挤度
                    congestion = "严重拥挤" if count > 5 else "中等拥挤" if count > 2 else "较空闲"
                    result += f"  • 最拥挤: 信道{most_used[0]} ({count}个网络) - {congestion}\n"
                    
                    # 推荐信道
                    result += f"  • 推荐信道: {best_channel[0]} ⭐\n"
                    result += f"  • 干扰评分: {best_score:.1f}/100 {self._get_score_emoji(best_score)}\n"
                    
                    # 找出空闲信道
                    free_channels = [ch for ch in available if ch not in usage]
                    if free_channels:
                        result += f"  • 空闲信道: {', '.join(map(str, free_channels[:5]))}"
                        if len(free_channels) > 5:
                            result += f" 等{len(free_channels)}个"
                        result += "\n"
                    
                    result += "\n"
                    
                    # ✅ P0修复: 对最拥挤信道触发质量告警（原方法定义但从未被调用）
                    congested_score = scores.get(most_used[0], best_score)
                    self._check_quality_alerts(most_used[0], band, congested_score, count)
        
        # ✅ P1修复: 将整体质量评分写入quality_history（声明后从未写入数据）
        if _quality_scores:
            self.quality_history.append((datetime.now(), sum(_quality_scores) / len(_quality_scores)))
        
        # 信道绑定统计
        if any(self.bonding_stats.values()):
            result += "⚡ 信道绑定统计:\n"
            for width, count in self.bonding_stats.items():
                if count > 0:
                    result += f"  • {width}: {count}个网络\n"
            result += "\n"
        
        # 实时监控状态
        if hasattr(self, 'realtime_monitor_var'):
            if self.realtime_monitor_var.get():
                result += "🔄 实时监控:\n"
                result += f"  • 状态: ✅ 运行中\n"
                result += f"  • 间隔: {self.monitor_interval}秒\n"
                if self.last_scan_time:
                    result += f"  • 上次扫描: {self.last_scan_time.strftime('%H:%M:%S')}\n"
                    result += f"  • 下次扫描: 见上方状态栏\n"  # ✅ P2修复: 去除重复计算
            else:
                result += "🔄 实时监控: ⏸️ 未启用\n"
            result += "\n"
        
        result += "─────────────────────────────────────────────────────────\n"
        
        self.result_text.insert('1.0', result)
    
    def _recommend_channel(self):
        """✅ Phase 1优化: 智能推荐信道（增强版）"""
        if not self.channel_usage:
            messagebox.showwarning("提示", "请先点击'分析信道'")
            return
        
        region = self.region_var.get()
        if region == "全部地区对比":
            messagebox.showinfo("提示", "请选择具体地区进行推荐")
            return
        
        recommendations = []
        recommendations.append("╔══════════════════════════════════════════════════╗\n")
        recommendations.append("║           🎯 智能信道推荐（增强版）             ║\n")
        recommendations.append("╚══════════════════════════════════════════════════╝\n\n")
        
        for band in ['2.4GHz', '5GHz', '6GHz']:
            channels = self.CHANNEL_REGIONS.get(region, {}).get(band, [])
            if not channels:
                continue
            
            usage = self.channel_usage.get(band, {})
            
            # ✅ P0: 修正干扰算法（IEEE 802.11标准）
            scores = {}
            for ch in channels:
                score = self._calculate_interference_score(ch, usage, band)
                scores[ch] = score
            
            # 推荐评分最高的3个
            if scores:
                top_channels = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
                
                icon = "📶" if band == "2.4GHz" else "📡" if band == "5GHz" else "🌐"
                recommendations.append(f"{icon} {band}频段推荐:\n")
                
                for idx, (ch, score) in enumerate(top_channels, 1):
                    emoji_rating = self._get_score_emoji(score)
                    
                    # 计算预期吞吐量（考虑频段、信道宽度、当前干扰评分）
                    # 基准值基于主流 WiFi 6(802.11ax) 单空间流参考值
                    # 2.4GHz: 20MHz=286Mbps; 5GHz: 80MHz=600Mbps, 160MHz=1201Mbps
                    # 6GHz:  80MHz=1200Mbps, 160MHz=2401Mbps, 320MHz=4803Mbps（WiFi7）
                    bonding = self.bonding_stats  # {'20MHz':n, '40MHz':n, '80MHz':n, '160MHz':n, '320MHz':n}
                    if band == '2.4GHz':
                        # 2.4GHz 仅支持 20/40MHz；40MHz 在密集环境中慎用
                        has_40 = bonding.get('40MHz', 0) > 0
                        base = 573 if has_40 else 286  # WiFi6 双流参考
                        max_throughput = int(base * (score / 100) * 0.6)  # 实际约为理论值60%
                        max_throughput = max(20, max_throughput)
                    elif band == '5GHz':
                        if bonding.get('160MHz', 0) > 0:
                            base = 2402
                        elif bonding.get('80MHz', 0) > 0:
                            base = 1201
                        elif bonding.get('40MHz', 0) > 0:
                            base = 600
                        else:
                            base = 286  # 20MHz 单流
                        max_throughput = int(base * (score / 100) * 0.6)
                        max_throughput = max(50, max_throughput)
                    else:  # 6GHz (WiFi 6E / WiFi 7)
                        if bonding.get('320MHz', 0) > 0:
                            base = 9608  # WiFi7 最大
                        elif bonding.get('160MHz', 0) > 0:
                            base = 4804
                        elif bonding.get('80MHz', 0) > 0:
                            base = 2402
                        else:
                            base = 1201  # 80MHz 默认最小
                        max_throughput = int(base * (score / 100) * 0.6)
                        max_throughput = max(200, max_throughput)
                    
                    recommendations.append(f"  {idx}. 信道 {ch} {'⭐' if idx == 1 else ''}\n")
                    recommendations.append(f"     • 干扰评分: {score:.1f}/100 {emoji_rating}\n")
                    recommendations.append(f"     • 预期吞吐: ~{max_throughput} Mbps\n")
                    
                    # ✅ Phase 2优化: 非WiFi干扰源检测
                    if band == '2.4GHz':
                        interference = self._detect_non_wifi_interference(ch, band)
                        if interference['source'] != 'None':
                            recommendations.append(f"     ⚠️ {interference['source']} (概率:{interference['probability']}%)\n")
                            recommendations.append(f"        建议: {interference['suggestion']}\n")
                    
                    # DFS提示
                    if ch in self.DFS_CHANNELS:
                        recommendations.append(f"     ⚠️ DFS信道（需60秒雷达检测）\n")
                    
                recommendations.append("\n")
        
        # 综合建议
        recommendations.append("💡 使用建议:\n")
        recommendations.append("  • 优先选择评分🟢优秀(>80)的信道\n")
        recommendations.append("  • 避免使用🔴较差(<40)的拥挤信道\n")
        recommendations.append("  • DFS信道需等待雷达检测，企业慎用\n")
        recommendations.append("  • 启用实时监控可自动检测干扰变化\n")
        recommendations.append("  • 2.4GHz频段注意微波炉/蓝牙干扰\n")
        
        if recommendations:
            messagebox.showinfo("智能推荐", "".join(recommendations))
        else:
            messagebox.showinfo("提示", "暂无推荐数据")
    
    def _show_utilization_dashboard(self):
        """显示信道利用率仪表盘"""
        if not self.last_networks:
            messagebox.showwarning("提示", "请先点击'分析信道'扫描网络")
            return
        
        # 创建新窗口
        dashboard = tk.Toplevel(self.parent)
        dashboard.title("📊 信道利用率仪表盘")
        dashboard.geometry("1200x800")
        
        # 转换数据格式供分析器使用
        networks_for_analyzer = []
        for net in self.last_networks:
            channel = net.get('channel', 'N/A')
            if channel != 'N/A' and str(channel).isdigit():
                networks_for_analyzer.append({
                    'ssid': net.get('ssid', 'Unknown'),
                    'channel': int(channel),
                    'signal': net.get('signal_percent', 0),
                    'bssid': net.get('bssid', 'Unknown')
                })
        
        # 分析数据
        result = self.utilization_analyzer.analyze_channels(networks_for_analyzer)
        
        # 顶部信息栏
        info_frame = ttk.LabelFrame(dashboard, text="📈 分析摘要", padding=10)
        info_frame.pack(fill='x', padx=10, pady=5)
        
        info_text = f"""
总计网络: {result['total_networks']} 个
  • 2.4GHz: {result['total_24ghz']} 个 ({result['total_24ghz']/result['total_networks']*100:.1f}% 占比)
  • 5GHz: {result['total_5ghz']} 个 ({result['total_5ghz']/result['total_networks']*100:.1f}% 占比)

最拥挤信道:
  • 2.4GHz: 信道 {result['most_congested_24'][0]} ({result['most_congested_24'][1]} 个网络)
  • 5GHz: 信道 {result['most_congested_5'][0]} ({result['most_congested_5'][1]} 个网络)

智能推荐:
  • 2.4GHz: 信道 {result['recommended_24']}
  • 5GHz: 信道 {result['recommended_5']}
        """.strip()
        
        tk.Label(info_frame, text=info_text, justify='left', 
                font=('Microsoft YaHei', 10), bg='white').pack(fill='x')
        
        # 图表区域 - 使用Notebook分页
        notebook = ttk.Notebook(dashboard)
        notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 页面1: 频段分布饼图
        tab1 = ttk.Frame(notebook)
        notebook.add(tab1, text="📊 频段分布")
        
        fig_pie = self.utilization_analyzer.generate_pie_chart()
        canvas_pie = FigureCanvasTkAgg(fig_pie, tab1)
        canvas_pie.draw()
        canvas_pie.get_tk_widget().pack(fill='both', expand=True)
        toolbar_pie = NavigationToolbar2Tk(canvas_pie, tab1)
        toolbar_pie.update()
        
        # 页面2: 2.4GHz柱状图
        tab2 = ttk.Frame(notebook)
        notebook.add(tab2, text="📶 2.4GHz信道")
        
        fig_24 = self.utilization_analyzer.generate_bar_chart(band='2.4GHz')
        canvas_24 = FigureCanvasTkAgg(fig_24, tab2)
        canvas_24.draw()
        canvas_24.get_tk_widget().pack(fill='both', expand=True)
        toolbar_24 = NavigationToolbar2Tk(canvas_24, tab2)
        toolbar_24.update()
        
        # 页面3: 5GHz柱状图
        tab3 = ttk.Frame(notebook)
        notebook.add(tab3, text="📡 5GHz信道")
        
        fig_5 = self.utilization_analyzer.generate_bar_chart(band='5GHz')
        canvas_5 = FigureCanvasTkAgg(fig_5, tab3)
        canvas_5.draw()
        canvas_5.get_tk_widget().pack(fill='both', expand=True)
        toolbar_5 = NavigationToolbar2Tk(canvas_5, tab3)
        toolbar_5.update()
        
        # 底部按钮栏
        button_frame = ttk.Frame(dashboard)
        button_frame.pack(fill='x', padx=10, pady=5)
        
        ModernButton(button_frame, text="💾 导出报告", 
                    command=lambda: self._export_utilization_report(result),
                    style='primary').pack(side='left', padx=5)
        
        ModernButton(button_frame, text="🔄 刷新数据", 
                    command=lambda: [dashboard.destroy(), self._analyze_channels(), self._show_utilization_dashboard()],
                    style='info').pack(side='left', padx=5)
        
        ModernButton(button_frame, text="❌ 关闭", 
                    command=dashboard.destroy,
                    style='danger').pack(side='right', padx=5)
    
    def _export_utilization_report(self, result: dict):
        """导出利用率报告"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"channel_utilization_report_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.utilization_analyzer.get_summary_text())
                f.write("\n\n详细数据:\n")
                f.write(f"2.4GHz信道分布: {result['channels_24ghz']}\n")
                f.write(f"5GHz信道分布: {result['channels_5ghz']}\n")
            
            messagebox.showinfo("成功", f"报告已导出: {filename}")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")
    
    def _parse_signal_dbm(self, signal_str) -> int:
        """解析信号强度为dBm"""
        try:
            if 'dBm' in str(signal_str):
                return int(str(signal_str).replace(' dBm', ''))
            return int(signal_str)
        except (ValueError, AttributeError, TypeError):
            # 信号值解析失败，返回默认弱信号
            return -100
    
    def _get_bonded_group(self, ch: int) -> list:
        """获取信道可能的绑定组"""
        # 检查80MHz组
        for group, _ in self.CHANNEL_80MHZ_GROUPS:
            if ch in group:
                return group
        
        # 检查40MHz对
        for pair, _ in self.CHANNEL_40MHZ_PAIRS:
            if ch in pair:
                return pair
        
        return [ch]
    
    def _detect_channel_bonding(self, networks: list) -> dict:
        """✅ P1: 检测信道绑定使用情况"""
        bonding_stats = {'20MHz': 0, '40MHz': 0, '80MHz': 0, '160MHz': 0}
        
        for network in networks:
            bandwidth = self._infer_bandwidth(network)
            if bandwidth in bonding_stats:
                bonding_stats[bandwidth] += 1
        
        return bonding_stats
    
    def _infer_bandwidth(self, network: dict) -> str:
        """推断信道带宽"""
        wifi_standard = network.get('wifi_standard', '')
        band = network.get('band', '')
        
        if '6' in wifi_standard or 'ax' in wifi_standard.lower():
            return '80MHz'  # WiFi 6默认80MHz
        elif '5' in wifi_standard or 'ac' in wifi_standard.lower():
            return '80MHz'  # WiFi 5常用80MHz
        elif '4' in wifi_standard or 'n' in wifi_standard.lower():
            if band == '5GHz':
                return '40MHz'  # 5GHz WiFi 4常用40MHz
            else:
                return '20MHz'  # 2.4GHz WiFi 4常用20MHz
        else:
            return '20MHz'
    
    def _recommend_non_overlapping_channels(self, band: str) -> list:
        """✅ P1: 推荐非重叠信道组合"""
        if band == '2.4GHz':
            # 经典1/6/11组合（中国1-13信道）
            standard_sets = [
                [1, 6, 11],       # 美国标准
                [1, 5, 9, 13]     # 中国4信道配置
            ]
            
            # 评估每个组合的干扰程度
            best_set = []
            min_interference = float('inf')
            
            for channel_set in standard_sets:
                total_interference = 0
                for ch in channel_set:
                    usage = self.channel_usage.get(band, {})
                    if ch in usage:
                        ch_data = usage[ch]
                        if isinstance(ch_data, dict):
                            total_interference += ch_data['weight']
                        else:
                            total_interference += ch_data
                
                if total_interference < min_interference:
                    min_interference = total_interference
                    best_set = channel_set
            
            return best_set
        
        elif band == '5GHz':
            # 推荐UNII-1和UNII-3频段（避开DFS）
            preferred_channels = [36, 40, 44, 48, 149, 153, 157, 161]
            usage = self.channel_usage.get(band, {})
            
            # 按使用率排序
            sorted_channels = sorted(
                preferred_channels,
                key=lambda ch: usage.get(ch, {}).get('weight', 0) if isinstance(usage.get(ch), dict) else usage.get(ch, 0)
            )
            
            return sorted_channels[:4]
        
        return []
    
    def _show_heatmap(self):
        """✅ Phase 2优化: 显示干扰热力图（异步+缓存）"""
        if not self.channel_usage:
            messagebox.showwarning("提示", "请先点击'分析信道'扫描网络")
            return
        
        # 创建热力图窗口
        heatmap_window = tk.Toplevel(self.parent)
        heatmap_window.title("🔥 信道干扰热力图（异步计算）")
        heatmap_window.geometry("1000x850")
        
        # 状态标签
        status_frame = ttk.Frame(heatmap_window)
        status_frame.pack(fill='x', padx=10, pady=5)
        
        status_label = ttk.Label(status_frame, text="⏳ 正在计算热力图...", 
                                font=('Microsoft YaHei', 10), foreground='orange')
        status_label.pack(side='left')
        
        cache_label = ttk.Label(status_frame, text="", 
                               font=('Microsoft YaHei', 9), foreground='gray')
        cache_label.pack(side='right')
        
        # 创建图表框架
        chart_frame = ttk.Frame(heatmap_window)
        chart_frame.pack(fill='both', expand=True)
        
        # 创建图表
        fig = Figure(figsize=(10, 8))
        
        # 2.4GHz热力图
        ax1 = fig.add_subplot(2, 1, 1)
        # 5GHz热力图
        ax2 = fig.add_subplot(2, 1, 2)
        
        canvas = FigureCanvasTkAgg(fig, chart_frame)
        canvas.get_tk_widget().pack(fill='both', expand=True)
        
        toolbar = NavigationToolbar2Tk(canvas, chart_frame)
        toolbar.update()
        
        # 计数器
        completed = {'2.4GHz': False, '5GHz': False}
        
        def update_status():
            """更新状态"""
            if completed['2.4GHz'] and completed['5GHz']:
                status_label.config(text="✅ 热力图生成完成", foreground='green')
        
        # 异步生成2.4GHz热力图
        def on_2ghz_ready(matrix, from_cache=False):
            """2.4GHz热力图就绪回调"""
            try:
                self._draw_heatmap_2ghz_async(ax1, matrix)
                completed['2.4GHz'] = True
                
                if from_cache:
                    cache_label.config(text="📊 2.4GHz: 缓存命中")
                
                fig.tight_layout()
                canvas.draw()
                update_status()
            except Exception as e:
                print(f"2.4GHz热力图绘制错误: {e}")
        
        # 异步生成5GHz热力图
        def on_5ghz_ready(matrix, from_cache=False):
            """5GHz热力图就绪回调"""
            try:
                self._draw_heatmap_5ghz_async(ax2, matrix)
                completed['5GHz'] = True
                
                if from_cache:
                    current = cache_label.cget('text')
                    cache_label.config(text=current + " | 📊 5GHz: 缓存命中")
                
                fig.tight_layout()
                canvas.draw()
                update_status()
            except Exception as e:
                print(f"5GHz热力图绘制错误: {e}")
        
        # 启动异步计算
        channels_2ghz = list(range(1, 14))
        usage_2ghz = self.channel_usage.get('2.4GHz', {})
        
        channels_5ghz = [36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112, 
                        116, 120, 124, 128, 132, 136, 140, 149, 153, 157, 161, 165]
        usage_5ghz = self.channel_usage.get('5GHz', {})
        
        self.heatmap_generator.generate_async(
            channels_2ghz, usage_2ghz, '2.4GHz', on_2ghz_ready,
            frame=self.frame
        )
        
        self.heatmap_generator.generate_async(
            channels_5ghz, usage_5ghz, '5GHz', on_5ghz_ready,
            dfs_channels=self.DFS_CHANNELS, frame=self.frame
        )
    
    def _draw_heatmap_2ghz_async(self, ax, matrix):
        """✅ Phase 2优化: 异步绘制2.4GHz热力图（使用预计算矩阵）"""
        channels = list(range(1, 14))
        
        # 绘制热力图
        im = ax.imshow(matrix, cmap='RdYlGn_r', aspect='auto', interpolation='bilinear')
        
        ax.set_xticks(range(len(channels)))
        ax.set_xticklabels(channels)
        ax.set_yticks(range(len(channels)))
        ax.set_yticklabels(channels)
        ax.set_xlabel('信道')
        ax.set_ylabel('受影响信道')
        ax.set_title('2.4GHz信道干扰热力图\n（颜色越深=干扰越强）', fontweight='bold')
        
        # 添加颜色条
        cbar = ax.figure.colorbar(im, ax=ax)
        cbar.set_label('干扰强度')
    
    def _draw_heatmap_5ghz_async(self, ax, matrix):
        """✅ Phase 2优化: 异步绘制5GHz热力图（使用预计算矩阵）"""
        channels = [36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112, 
                   116, 120, 124, 128, 132, 136, 140, 149, 153, 157, 161, 165]
        
        # 绘制热力图
        im = ax.imshow(matrix, cmap='RdYlGn_r', aspect='auto', interpolation='nearest')
        
        ax.set_xticks(range(len(channels)))
        ax.set_xticklabels(channels, rotation=45, fontsize=8)
        ax.set_yticks(range(len(channels)))
        ax.set_yticklabels(channels, fontsize=8)
        ax.set_xlabel('信道')
        ax.set_ylabel('受影响信道')
        ax.set_title('5GHz信道干扰热力图（考虑信道绑定）⚡ 异步计算', fontweight='bold')
        
        # 标记DFS区域
        dfs_indices = [i for i, ch in enumerate(channels) if ch in self.DFS_CHANNELS]
        if dfs_indices:
            for idx in dfs_indices:
                ax.axhspan(idx - 0.5, idx + 0.5, alpha=0.15, color='orange', zorder=0)
                ax.axvspan(idx - 0.5, idx + 0.5, alpha=0.15, color='orange', zorder=0)
        
        # 添加颜色条
        cbar = ax.figure.colorbar(im, ax=ax)
        cbar.set_label('干扰强度')
    
    def _show_trend_chart(self):
        """✅ P2: 显示历史趋势图"""
        if len(self.channel_history) < 2:
            messagebox.showwarning("提示", "历史数据不足，请多次扫描后再查看趋势")
            return
        
        # 创建趋势窗口
        trend_window = tk.Toplevel(self.parent)
        trend_window.title("📈 信道占用历史趋势")
        trend_window.geometry("1200x800")
        
        # 选择要显示的信道
        select_frame = ttk.Frame(trend_window)
        select_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(select_frame, text="选择频段:").pack(side='left', padx=5)
        band_var = tk.StringVar(value='2.4GHz')
        ttk.Radiobutton(select_frame, text='2.4GHz', variable=band_var, value='2.4GHz').pack(side='left')
        ttk.Radiobutton(select_frame, text='5GHz', variable=band_var, value='5GHz').pack(side='left')
        
        ttk.Label(select_frame, text="信道:").pack(side='left', padx=5)
        channel_var = tk.StringVar(value='1')
        channel_entry = ttk.Entry(select_frame, textvariable=channel_var, width=10)
        channel_entry.pack(side='left', padx=5)
        
        # 图表区域
        fig = Figure(figsize=(12, 6))
        ax = fig.add_subplot(111)
        
        canvas = FigureCanvasTkAgg(fig, trend_window)
        canvas.get_tk_widget().pack(fill='both', expand=True)
        
        def update_chart():
            ax.clear()
            band = band_var.get()
            try:
                channel = int(channel_var.get())
            except Exception as e:  # P2修复: 指定异常类型
                messagebox.showerror("错误", "请输入有效的信道号")
                return
            
            # 提取数据
            times = [h[0] for h in self.channel_history]
            weights = []
            counts = []
            
            for _, usage in self.channel_history:
                ch_data = usage.get(band, {}).get(channel, {})
                if isinstance(ch_data, dict):
                    weights.append(ch_data.get('weight', 0))
                    counts.append(ch_data.get('count', 0))
                else:
                    weights.append(0)
                    counts.append(ch_data if ch_data else 0)
            
            # 绘制双Y轴
            ax.plot(times, counts, marker='o', label='网络数量', color='blue', linewidth=2)
            ax.set_xlabel('时间')
            ax.set_ylabel('网络数量', color='blue')
            ax.tick_params(axis='y', labelcolor='blue')
            
            # 设置时间轴格式化
            if times and isinstance(times[0], datetime):
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
                ax.xaxis.set_major_locator(mdates.AutoDateLocator())
                fig.autofmt_xdate(rotation=30)
            
            ax2 = ax.twinx()
            ax2.plot(times, weights, marker='s', label='信号强度权重', color='red', linewidth=2, linestyle='--')
            ax2.set_ylabel('信号强度权重', color='red')
            ax2.tick_params(axis='y', labelcolor='red')
            
            ax.set_title(f'{band}频段 信道{channel} 占用趋势', fontweight='bold')
            ax.grid(True, alpha=0.3)
            
            # 合并图例
            lines1, labels1 = ax.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
            
            fig.tight_layout()
            canvas.draw()
        
        ModernButton(select_frame, text="刷新图表", command=update_chart, style='primary').pack(side='left', padx=5)
        update_chart()  # 初始绘制
    
    def _show_ap_planner(self):
        """✅ P3: 显示AP部署规划器"""
        # 创建规划窗口
        planner_window = tk.Toplevel(self.parent)
        planner_window.title("🏢 AP信道部署规划")
        planner_window.geometry("1000x800")
        
        # 输入参数
        input_frame = ttk.LabelFrame(planner_window, text="规划参数", padding=10)
        input_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(input_frame, text="AP数量:").pack(side='left', padx=5)
        ap_count_var = tk.StringVar(value='5')
        ttk.Entry(input_frame, textvariable=ap_count_var, width=10).pack(side='left', padx=5)
        
        ttk.Label(input_frame, text="频段:").pack(side='left', padx=5)
        band_var = tk.StringVar(value='5GHz')
        ttk.Combobox(input_frame, textvariable=band_var, values=['2.4GHz', '5GHz'], 
                    width=10, state='readonly').pack(side='left', padx=5)
        
        # 图表区域
        fig = Figure(figsize=(10, 7))
        canvas = FigureCanvasTkAgg(fig, planner_window)
        canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # 结果文本
        result_frame = ttk.LabelFrame(planner_window, text="分配方案", padding=10)
        result_frame.pack(fill='x', padx=10, pady=5)
        
        result_text = tk.Text(result_frame, height=5, font=('Consolas', 10))
        result_text.pack(fill='x')
        
        def plan_channels():
            try:
                ap_count = int(ap_count_var.get())
                band = band_var.get()
            except Exception as e:  # P2修复: 指定异常类型
                messagebox.showerror("错误", "请输入有效的AP数量")
                return
            
            # 生成信道分配
            channels = self._plan_ap_channels(ap_count, band)
            
            # 绘制可视化
            fig.clear()
            ax = fig.add_subplot(111)
            
            # 网格布局
            rows = int(np.ceil(np.sqrt(ap_count)))
            cols = int(np.ceil(ap_count / rows))
            
            for i, channel in enumerate(channels):
                row = i // cols
                col = i % cols
                
                # 绘制AP图标
                color = self._get_channel_color(channel, band)
                circle = mpatches.Circle((col, row), 0.35, color=color, alpha=0.7, ec='black', linewidth=2)
                ax.add_patch(circle)
                
                # 标注信道号
                ax.text(col, row, f'AP{i+1}\nCH{channel}', 
                       ha='center', va='center', fontweight='bold', fontsize=9)
            
            ax.set_xlim(-1, cols)
            ax.set_ylim(-1, rows)
            ax.set_aspect('equal')
            ax.axis('off')
            ax.set_title(f'{band}频段AP信道分配方案（{ap_count}个AP）', fontweight='bold', fontsize=14)
            
            # 添加图例
            if band == '2.4GHz':
                legend_elements = [
                    mpatches.Patch(color='#2ecc71', label='信道1（非重叠）'),
                    mpatches.Patch(color='#3498db', label='信道6（非重叠）'),
                    mpatches.Patch(color='#e74c3c', label='信道11（非重叠）')
                ]
            else:
                legend_elements = [
                    mpatches.Patch(color='#2ecc71', label='UNII-1（非DFS）'),
                    mpatches.Patch(color='#f39c12', label='UNII-2（DFS）'),
                    mpatches.Patch(color='#3498db', label='UNII-3（非DFS）')
                ]
            ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 1))
            
            canvas.draw()
            
            # 显示分配详情
            result_text.delete('1.0', 'end')
            result_text.insert('end', f"信道分配方案（{band}频段）：\n\n")
            for i, ch in enumerate(channels, 1):
                dfs_mark = " ⚠️DFS" if ch in self.DFS_CHANNELS else ""
                result_text.insert('end', f"AP{i}: 信道 {ch}{dfs_mark}\n")
        
        ModernButton(input_frame, text="生成方案", command=plan_channels, style='success').pack(side='left', padx=5)
        ModernButton(input_frame, text="导出报告", command=lambda: self._export_ap_plan(ap_count_var.get(), band_var.get()), 
                    style='primary').pack(side='left', padx=5)
    
    def _plan_ap_channels(self, ap_count: int, band: str) -> list:
        """AP信道分配算法"""
        if band == '2.4GHz':
            # 2.4GHz: 循环使用1/6/11
            base_channels = [1, 6, 11]
            return [base_channels[i % 3] for i in range(ap_count)]
        
        elif band == '5GHz':
            # 5GHz: 优先非DFS信道
            preferred = [36, 40, 44, 48, 149, 153, 157, 161]
            dfs = [52, 56, 60, 64, 100, 104, 108, 112, 116, 120, 124, 128, 132, 136, 140]
            
            channels = []
            for i in range(ap_count):
                if i < len(preferred):
                    channels.append(preferred[i])
                else:
                    # 超出后使用DFS
                    channels.append(dfs[(i - len(preferred)) % len(dfs)])
            
            return channels
        
        return []
    
    def _get_channel_color(self, channel: int, band: str) -> str:
        """获取信道对应的颜色"""
        if band == '2.4GHz':
            if channel == 1:
                return '#2ecc71'
            elif channel == 6:
                return '#3498db'
            elif channel == 11:
                return '#e74c3c'
            else:
                return '#95a5a6'
        else:  # 5GHz
            if channel in [36, 40, 44, 48]:
                return '#2ecc71'  # UNII-1
            elif channel in self.DFS_CHANNELS:
                return '#f39c12'  # DFS
            else:
                return '#3498db'  # UNII-3
    
    def _export_ap_plan(self, ap_count_str: str, band: str):
        """✅ P3: 导出AP部署方案"""
        try:
            ap_count = int(ap_count_str)
            channels = self._plan_ap_channels(ap_count, band)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"AP部署方案_{band}_{ap_count}AP_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("="*60 + "\n")
                f.write("AP信道部署方案\n")
                f.write("="*60 + "\n\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"频段: {band}\n")
                f.write(f"AP数量: {ap_count}\n\n")
                f.write("="*60 + "\n")
                f.write("信道分配详情\n")
                f.write("="*60 + "\n\n")
                
                for i, ch in enumerate(channels, 1):
                    dfs_mark = " [DFS - 需雷达检测]" if ch in self.DFS_CHANNELS else ""
                    f.write(f"AP #{i:02d}: 信道 {ch}{dfs_mark}\n")
                
                if band == '2.4GHz':
                    f.write("\n\n建议说明:\n")
                    f.write("• 使用1/6/11非重叠信道组合\n")
                    f.write("• 相邻AP应使用不同信道避免干扰\n")
                    f.write("• 信道宽度建议20MHz\n")
                else:
                    f.write("\n\n建议说明:\n")
                    f.write("• 优先使用36-48和149-165非DFS信道\n")
                    f.write("• DFS信道需60秒雷达检测时间\n")
                    f.write("• 信道宽度可选40MHz或80MHz\n")
            
            messagebox.showinfo("成功", f"方案已导出: {filename}")
        
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")
    
    def _show_protocol_info(self):
        """显示WiFi协议支持信息"""
        window = tk.Toplevel(self.parent)
        window.title("WiFi协议支持信息")
        window.geometry("900x700")
        
        # 主容器
        main_frame = ttk.Frame(window)
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        # 标题
        title_label = tk.Label(main_frame, text="📡 WiFi 6E/7 协议与信道支持", 
                              font=('Microsoft YaHei UI', 14, 'bold'),
                              fg='#2c3e50')
        title_label.pack(pady=(0, 15))
        
        # 创建Notebook标签页
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill='both', expand=True)
        
        # 标签页1: 协议概览
        protocol_frame = ttk.Frame(notebook)
        notebook.add(protocol_frame, text="协议标准")
        
        protocol_text = tk.Text(protocol_frame, font=('Consolas', 10), wrap='word')
        protocol_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        protocol_info = """
═══════════════════════════════════════════════════════════
                    WiFi协议标准对比
═══════════════════════════════════════════════════════════

📶 WiFi 4 (802.11n) - 2009年
  • 频段: 2.4GHz / 5GHz
  • 最大速率: 600 Mbps
  • 信道宽度: 20MHz / 40MHz
  • MIMO: 最多4x4
  • 适用场景: 基础网络覆盖

📶 WiFi 5 (802.11ac) - 2014年
  • 频段: 5GHz 专用
  • 最大速率: 6.9 Gbps
  • 信道宽度: 20/40/80/160MHz
  • MU-MIMO: 最多8x8（下行）
  • 适用场景: 高速数据传输、4K视频

📶 WiFi 6 (802.11ax 2.4/5GHz) - 2019年
  • 频段: 2.4GHz / 5GHz
  • 最大速率: 9.6 Gbps
  • 信道宽度: 20/40/80/160MHz
  • OFDMA: 多用户并发
  • MU-MIMO: 8x8（上下行）
  • 目标唤醒时间(TWT): 省电优化
  • 适用场景: 高密度环境、智能家居

📶 WiFi 6E (802.11ax 6GHz) - 2020年
  • 频段: 6GHz 频段（5925-7125 MHz）
  • 可用信道: 59个20MHz信道
  • 无遗留设备干扰
  • 支持160MHz宽信道
  • 适用场景: 超低延迟、AR/VR、8K视频

📶 WiFi 7 (802.11be) - 2024年
  • 频段: 2.4GHz / 5GHz / 6GHz
  • 最大速率: 46 Gbps
  • 信道宽度: 20/40/80/160/320MHz
  • 4K-QAM调制
  • 多链路操作(MLO): 同时使用多频段
  • 16x16 MU-MIMO
  • 适用场景: 超高速传输、云游戏、工业4.0

═══════════════════════════════════════════════════════════
"""
        protocol_text.insert('1.0', protocol_info)
        protocol_text.config(state='disabled')
        
        # 标签页2: 信道绑定
        bonding_frame = ttk.Frame(notebook)
        notebook.add(bonding_frame, text="信道绑定")
        
        bonding_text = tk.Text(bonding_frame, font=('Consolas', 10), wrap='word')
        bonding_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        bonding_info = f"""
═══════════════════════════════════════════════════════════
                    信道绑定技术
═══════════════════════════════════════════════════════════

📊 20MHz - 标准信道
  • 所有WiFi协议支持
  • 最稳定、兼容性最好
  • 适用: 基础覆盖

📊 40MHz - WiFi 4/5/6/7
  • 绑定2个20MHz信道
  • 速率翻倍
  • 5GHz配对: {len(self.CHANNEL_40MHZ_PAIRS)}组
  • 适用: 一般高速场景

📊 80MHz - WiFi 5/6/6E/7
  • 绑定4个20MHz信道
  • 5GHz组合: {len(self.CHANNEL_80MHZ_GROUPS)}组
  • 适用: 4K视频、游戏

📊 160MHz - WiFi 6/6E/7
  • 绑定8个20MHz信道
  • 5GHz组合: {len(self.CHANNEL_160MHZ_GROUPS)}组
  • 6GHz: 更多可用信道
  • 适用: 8K视频、AR/VR

📊 320MHz - WiFi 7 专属
  • 绑定16个20MHz信道
  • 仅6GHz频段支持
  • 6GHz组合: {len(self.CHANNEL_320MHZ_GROUPS)}组
  • 适用: 超高速传输、云游戏

═══════════════════════════════════════════════════════════

⚠️ 注意事项:
  1. 信道越宽，速率越高，但干扰风险增加
  2. DFS信道需要60秒雷达检测时间
  3. 6GHz频段无遗留设备干扰，推荐使用
  4. WiFi 7的320MHz需要兼容设备支持

═══════════════════════════════════════════════════════════
"""
        bonding_text.insert('1.0', bonding_info)
        bonding_text.config(state='disabled')
        
        # 标签页3: 6GHz频段
        sixghz_frame = ttk.Frame(notebook)
        notebook.add(sixghz_frame, text="6GHz频段")
        
        sixghz_text = tk.Text(sixghz_frame, font=('Consolas', 10), wrap='word')
        sixghz_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        unii5 = ', '.join(map(str, self.UNII_BANDS_6GHZ['UNII-5'][:10])) + '...'
        unii6 = ', '.join(map(str, self.UNII_BANDS_6GHZ['UNII-6']))
        unii7 = ', '.join(map(str, self.UNII_BANDS_6GHZ['UNII-7'][:10])) + '...'
        unii8 = ', '.join(map(str, self.UNII_BANDS_6GHZ['UNII-8'][:10])) + '...'
        
        sixghz_info = f"""
═══════════════════════════════════════════════════════════
                6GHz频段详解 (WiFi 6E/7)
═══════════════════════════════════════════════════════════

🌐 频段范围: 5925 - 7125 MHz
🌐 总带宽: 1200 MHz
🌐 可用信道: 59个20MHz信道（信道1-233）

─────────────────────────────────────────────────────────

📡 UNII-5 频段 (5925-6425 MHz)
  • 信道范围: 1-93
  • 示例信道: {unii5}
  • 用途: 室内外通用

📡 UNII-6 频段 (6425-6525 MHz)
  • 信道范围: 97-117
  • 信道列表: {unii6}
  • 用途: 低功率室内

📡 UNII-7 频段 (6525-6875 MHz)
  • 信道范围: 121-189
  • 示例信道: {unii7}
  • 用途: 标准功率室内外

📡 UNII-8 频段 (6875-7125 MHz)
  • 信道范围: 193-233
  • 示例信道: {unii8}
  • 用途: 客户端到客户端

─────────────────────────────────────────────────────────

✨ 6GHz频段优势:
  ✓ 无遗留设备干扰（仅WiFi 6E/7）
  ✓ 更多可用信道
  ✓ 支持160MHz和320MHz宽信道
  ✓ 更低延迟
  ✓ 适合AR/VR、8K视频等应用

⚠️ 覆盖特性:
  • 穿墙能力弱于2.4GHz和5GHz
  • 适合高速率短距离场景
  • 建议配合5GHz双频使用

═══════════════════════════════════════════════════════════
"""
        sixghz_text.insert('1.0', sixghz_info)
        sixghz_text.config(state='disabled')
        
        # 标签页4: 地区支持
        region_frame = ttk.Frame(notebook)
        notebook.add(region_frame, text="地区法规")
        
        region_text = tk.Text(region_frame, font=('Consolas', 9), wrap='word')
        region_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        region_info = "═══════════════════════════════════════════════════════════\n"
        region_info += "              各地区WiFi协议支持情况\n"
        region_info += "═══════════════════════════════════════════════════════════\n\n"
        
        for region, config in self.CHANNEL_REGIONS.items():
            region_info += f"🌍 {region}\n"
            region_info += f"  支持协议: {', '.join(config.get('protocols', ['WiFi 4', 'WiFi 5', 'WiFi 6']))}\n"
            region_info += f"  2.4GHz: {len(config['2.4GHz'])}个信道\n"
            region_info += f"  5GHz:   {len(config['5GHz'])}个信道\n"
            region_info += f"  6GHz:   {len(config['6GHz'])}个信道"
            if len(config['6GHz']) > 0:
                region_info += f" ✓ 支持WiFi 6E/7"
            region_info += "\n\n"
        
        region_info += "═══════════════════════════════════════════════════════════\n"
        
        region_text.insert('1.0', region_info)
        region_text.config(state='disabled')
        
        # 底部按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x', pady=(10, 0))
        
        ModernButton(btn_frame, text="关闭", command=window.destroy, 
                    style='primary').pack(side='right')
    
    def _toggle_realtime_monitor(self):
        """✅ Phase 1优化: 切换实时监控状态"""
        if self.realtime_monitor_var.get():
            # 启动监控
            self._monitor_stop_event.clear()
            self.realtime_monitoring = True
            self.last_scan_time = datetime.now()
            self._update_monitor_status("🔄 运行中", "green")
            self._start_monitor_thread()
        else:
            # 停止监控
            self.realtime_monitoring = False
            self._monitor_stop_event.set()
            self._update_monitor_status("⏸️ 已停止", "gray")
    
    def _update_monitor_interval(self, event=None):
        """更新监控间隔"""
        interval_str = self.monitor_interval_var.get()
        self.monitor_interval = int(interval_str.replace('秒', ''))
        
        # ✅ P0修复: 通过递增代次让旧线程自动识别并退出，无需join（避免主线程死锁）
        if self.realtime_monitoring:
            self._monitor_stop_event.set()   # 中断旧线程当前等待
            self._monitor_stop_event.clear()
            self._start_monitor_thread()     # 新代次线程启动，旧线程代次检查失败后退出
    
    def _start_monitor_thread(self):
        """✅ P0修复: 启动监控线程（通过frame.after将Tkinter操作隔离到主线程）"""
        import threading
        
        # 递增代次：旧线程检测到代次变更后自动退出，防止并发双线程写共享数据
        self._monitor_gen = getattr(self, '_monitor_gen', 0) + 1
        current_gen = self._monitor_gen
        
        def monitor_loop():
            while self.realtime_monitoring and self._monitor_gen == current_gen:
                scan_done = threading.Event()
                
                def do_scan(evt=scan_done):
                    """在主线程执行扫描，包含所有Tkinter操作，避免线程安全问题"""
                    try:
                        self._analyze_channels()
                    finally:
                        evt.set()
                
                # 将扫描调度到主线程，后台线程仅等待结果
                self.frame.after(0, do_scan)
                
                # 等待扫描完成，每500ms检查一次停止信号
                while not scan_done.wait(timeout=0.5):
                    if not self.realtime_monitoring or self._monitor_gen != current_gen:
                        return
                
                if not self.realtime_monitoring or self._monitor_gen != current_gen:
                    return
                
                self.last_scan_time = datetime.now()
                next_scan = self.last_scan_time.timestamp() + self.monitor_interval
                self.frame.after(0, lambda ns=next_scan: self._update_monitor_status(
                    f"🔄 运行中 (下次: {datetime.fromtimestamp(ns).strftime('%H:%M:%S')})",
                    "green"
                ))
                
                # 等待下次扫描间隔（可被停止事件中断）
                self._monitor_stop_event.wait(timeout=self.monitor_interval)
        
        def monitor_loop_safe():
            try:
                monitor_loop()
            except Exception as e:
                print(f"监控循环错误: {e}")
                # ✅ P1修复: 异常退出时更新UI，避免状态标签永远显示"运行中"
                self.frame.after(0, lambda: [
                    self._update_monitor_status("❌ 监控异常停止", "red"),
                    self.realtime_monitor_var.set(False)
                ])
        
        self.monitor_thread = threading.Thread(target=monitor_loop_safe, daemon=True)
        self.monitor_thread.start()
    
    def _update_monitor_status(self, text, color):
        """更新监控状态标签"""
        self.monitor_status_label.config(text=text, foreground=color)
    
    def _calculate_interference_score(self, channel: int, usage: dict, band: str) -> float:
        """✅ Phase 1优化: 增强干扰评分算法（含SNR检测 + weight归一化）"""
        score = 100.0

        def _normalized_weight(ch_data) -> float:
            """将 weight（累加值）归一化到 0~1：用 count 做平均避免大密度误判。"""
            if not isinstance(ch_data, dict):
                return 0.0
            count = max(1, ch_data.get('count', 1))
            raw = ch_data.get('weight', 0.0)
            # 平均信号权重（0~1），再乘以网络数量密度因子（每3个网络算满载）
            avg = raw / count
            density = min(1.0, count / 3.0)
            return avg * 0.6 + density * 0.4  # 综合考虑信号强度和网络密度

        # 1. 当前信道占用扣分
        if channel in usage:
            nw = _normalized_weight(usage[channel])
            score -= nw * 50  # 最多扣 50 分（满载且强信号）

        # 2. 邻近信道干扰
        if band == '2.4GHz':
            # 2.4GHz: 22MHz 信道带宽，±4 信道内存在重叠干扰（IEEE 802.11 标准）
            for offset in range(-4, 5):
                if offset == 0:
                    continue
                neighbor = channel + offset
                if neighbor in usage:
                    nw = _normalized_weight(usage[neighbor])
                    distance_factor = max(0.0, 1.0 - abs(offset) / 5.0)
                    score -= nw * distance_factor * 30  # 重叠越近扣分越多

        elif band == '5GHz':
            # 5GHz: 20MHz 信道独立不重叠，相邻信道几乎无干扰；
            # 仅在信道绑定（40/80MHz）场景下相邻信道有少量干扰
            for offset in [-4, 4]:
                neighbor = channel + offset
                if neighbor in usage:
                    nw = _normalized_weight(usage[neighbor])
                    score -= nw * 8  # 5GHz 相邻信道干扰很小

        elif band == '6GHz':
            # 6GHz: 信道间隔4，高密度部署时相邻信道仍有干扰
            for offset in [-4, 4]:
                neighbor = channel + offset
                if neighbor in usage:
                    nw = _normalized_weight(usage[neighbor])
                    score -= nw * 5  # 6GHz 功率控制更严格，干扰更小

        return max(0.0, score)
    
    def _get_score_emoji(self, score: float) -> str:
        """✅ Phase 1优化: 根据评分返回emoji和评级"""
        if score >= 80:
            return "🟢 优秀"
        elif score >= 60:
            return "🟡 良好"
        elif score >= 40:
            return "🟠 一般"
        else:
            return "🔴 较差"
    
    def _get_snr(self, signal_dbm: float) -> float:
        """✅ Phase 1优化: 计算信噪比（SNR）"""
        # 典型噪声底: -95dBm (2.4GHz), -92dBm (5GHz), -90dBm (6GHz)
        noise_floor = -95
        snr = signal_dbm - noise_floor
        return max(0, snr)
    
    def _detect_non_wifi_interference(self, channel: int, band: str) -> dict:
        """✅ Phase 2优化: 检测非WiFi干扰源"""
        interference = {
            'source': 'None',
            'impact': 'NONE',
            'suggestion': '',
            'probability': 0
        }
        
        if band != '2.4GHz':
            return interference  # 仅2.4GHz需要检测
        
        usage = self.channel_usage.get(band, {})
        
        # 1. 微波炉检测（2.45GHz，对应信道6-11）
        if channel in [6, 7, 8, 9, 10, 11]:
            # 检查信道6-11的异常高干扰
            microwave_channels = [6, 7, 8, 9, 10, 11]
            total_interference = sum(
                usage.get(ch, {}).get('weight', 0) if isinstance(usage.get(ch, {}), dict) else 0
                for ch in microwave_channels
            )
            
            if total_interference > 3.0:  # 异常高干扰
                interference = {
                    'source': '微波炉干扰',
                    'impact': 'HIGH',
                    'suggestion': '避开信道6-11或使用5GHz频段',
                    'probability': min(100, int(total_interference * 20))
                }
                return interference
        
        # 2. 蓝牙干扰（2.4-2.48GHz，跳频覆盖全部信道）
        if self._detect_bluetooth_activity():
            interference = {
                'source': '蓝牙设备干扰',
                'impact': 'MEDIUM',
                'suggestion': '减少蓝牙设备使用或切换到5GHz',
                'probability': 60
            }
            return interference
        
        # 3. 无线摄像头/无线监控（常用信道1/6/11）
        if channel in [1, 6, 11]:
            ch_data = usage.get(channel, {})
            if isinstance(ch_data, dict):
                count = ch_data.get('count', 0)
                weight = ch_data.get('weight', 0)
                
                # 高占用 + 中等权重 = 可能是摄像头
                if count > 3 and weight > 2.0:
                    interference = {
                        'source': '可能的无线摄像头/监控设备',
                        'impact': 'MEDIUM',
                        'suggestion': '联系管理员确认设备位置',
                        'probability': 50
                    }
                    return interference
        
        # 4. ZigBee设备（通常使用信道11，与WiFi信道11重叠）
        # 仅在信道11 AP 数量异常多（>5个）且平均权重中等时输出提示，
        # 避免无条件对所有信道11用户输出虚假告警
        if channel == 11:
            ch_data = usage.get(11, {})
            if isinstance(ch_data, dict):
                count = ch_data.get('count', 0)
                weight = ch_data.get('weight', 0.0)
                avg_w = (weight / count) if count > 0 else 0
                # 信道11 AP 密度高且平均信号偏弱，提示可能存在 ZigBee 竞争
                if count > 5 and avg_w < 0.4:
                    interference = {
                        'source': '可能的ZigBee智能家居设备',
                        'impact': 'LOW',
                        'suggestion': '如有智能家居系统，建议将ZigBee协调器改为ZigBee信道15/20/25，远离WiFi2.4GHz',
                        'probability': 40
                    }

        return interference
    
    def _detect_bluetooth_activity(self) -> bool:
        """推断当前环境蓝牙干扰可能性（基于 2.4GHz 高密度启发式规则）。

        注意：Windows netsh 扫描结果仅包含 WiFi AP，无法直接检测蓝牙设备。
        此方法通过以下启发式规则推断蓝牙共存干扰概率：
          - 2.4GHz 网络密度高（>10 个 AP）表明密集的无线环境，蓝牙干扰概率上升；
          - 信道1/6/11 同时拥挤，说明可用频谱已严重占用，蓝牙跳频影响更大。
        精度有限，结果仅供参考。
        """
        usage_24 = self.channel_usage.get('2.4GHz', {})
        total_ap_count = sum(
            data.get('count', 0) if isinstance(data, dict) else 0
            for data in usage_24.values()
        )
        # 主信道（1/6/11）同时有 AP 才判定高密度蓝牙干扰风险
        key_channels_occupied = sum(
            1 for ch in [1, 6, 11]
            if (usage_24.get(ch, {}).get('count', 0) if isinstance(usage_24.get(ch, {}), dict) else 0) > 0
        )
        return total_ap_count > 10 and key_channels_occupied >= 3
    
    def _show_quality_alert_config(self):
        """✅ Phase 2优化: 质量告警配置窗口"""
        alert_window = tk.Toplevel(self.parent)
        alert_window.title("🔔 质量告警系统配置")
        alert_window.geometry("700x650")
        
        # 标题
        title_label = ttk.Label(alert_window, 
                               text="质量告警系统 - 自动监控干扰与质量变化",
                               font=('Microsoft YaHei', 12, 'bold'))
        title_label.pack(pady=10)
        
        # 启用开关
        enable_frame = ttk.Frame(alert_window)
        enable_frame.pack(fill='x', padx=20, pady=10)
        
        alert_enabled_var = tk.BooleanVar(value=self.quality_alert_enabled)
        ttk.Checkbutton(enable_frame, text="✅ 启用质量告警",
                       variable=alert_enabled_var).pack(side='left')
        
        # 阈值配置
        threshold_frame = ttk.LabelFrame(alert_window, text="⚙️ 告警阈值配置", padding=10)
        threshold_frame.pack(fill='x', padx=20, pady=10)
        
        # 干扰评分阈值
        ttk.Label(threshold_frame, text="干扰评分低于:").grid(row=0, column=0, sticky='w', pady=5)
        interference_var = tk.IntVar(value=self.alert_thresholds['interference_score'])
        interference_scale = ttk.Scale(threshold_frame, from_=0, to=100, 
                                      variable=interference_var, orient='horizontal', length=300)
        interference_scale.grid(row=0, column=1, padx=10)
        interference_label = ttk.Label(threshold_frame, textvariable=interference_var)
        interference_label.grid(row=0, column=2)
        ttk.Label(threshold_frame, text="分（触发告警）").grid(row=0, column=3, sticky='w')
        
        # 信道拥挤度阈值
        ttk.Label(threshold_frame, text="信道网络数超过:").grid(row=1, column=0, sticky='w', pady=5)
        congestion_var = tk.IntVar(value=self.alert_thresholds['channel_congestion'])
        congestion_scale = ttk.Scale(threshold_frame, from_=1, to=20,
                                    variable=congestion_var, orient='horizontal', length=300)
        congestion_scale.grid(row=1, column=1, padx=10)
        congestion_label = ttk.Label(threshold_frame, textvariable=congestion_var)
        congestion_label.grid(row=1, column=2)
        ttk.Label(threshold_frame, text="个（触发告警）").grid(row=1, column=3, sticky='w')
        
        # 质量下降阈值
        ttk.Label(threshold_frame, text="质量下降超过:").grid(row=2, column=0, sticky='w', pady=5)
        quality_drop_var = tk.IntVar(value=self.alert_thresholds['quality_drop'])
        quality_drop_scale = ttk.Scale(threshold_frame, from_=5, to=50,
                                      variable=quality_drop_var, orient='horizontal', length=300)
        quality_drop_scale.grid(row=2, column=1, padx=10)
        quality_drop_label = ttk.Label(threshold_frame, textvariable=quality_drop_var)
        quality_drop_label.grid(row=2, column=2)
        ttk.Label(threshold_frame, text="分（触发告警）").grid(row=2, column=3, sticky='w')
        
        # 告警历史
        history_frame = ttk.LabelFrame(alert_window, text="📜 告警历史（最近10条）", padding=10)
        history_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        history_text = tk.Text(history_frame, height=10, width=70, font=('Consolas', 9))
        history_text.pack(fill='both', expand=True)
        
        # 显示告警历史
        if self.alert_history:
            for alert in list(self.alert_history)[-10:]:
                history_text.insert('end', f"{alert}\n")
        else:
            history_text.insert('end', "暂无告警记录")
        history_text.config(state='disabled')
        
        # 按钮区域
        button_frame = ttk.Frame(alert_window)
        button_frame.pack(pady=10)
        
        def save_config():
            self.quality_alert_enabled = alert_enabled_var.get()
            self.alert_thresholds['interference_score'] = interference_var.get()
            self.alert_thresholds['channel_congestion'] = congestion_var.get()
            self.alert_thresholds['quality_drop'] = quality_drop_var.get()
            messagebox.showinfo("保存成功", "质量告警配置已保存")
            alert_window.destroy()
        
        def test_alert():
            """测试告警"""
            test_msg = f"""🔔 质量告警测试

干扰评分: 35/100 🔴 较差
触发原因: 干扰评分低于 {interference_var.get()} 分
推荐信道: 6 → 11
建议: 立即切换到推荐信道"""
            messagebox.showwarning("质量告警", test_msg)
            
            # 添加到历史
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.alert_history.append(f"[{timestamp}] 测试告警 - 干扰评分35/100")
        
        ModernButton(button_frame, text="💾 保存配置", 
                    command=save_config, style='success').pack(side='left', padx=5)
        ModernButton(button_frame, text="🔔 测试告警", 
                    command=test_alert, style='warning').pack(side='left', padx=5)
        ModernButton(button_frame, text="❌ 取消", 
                    command=alert_window.destroy).pack(side='left', padx=5)
    
    def _check_quality_alerts(self, channel, band, current_score, network_count):
        """✅ Phase 2优化: 检查质量告警"""
        if not self.quality_alert_enabled:
            return
        
        alerts = []
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 检查干扰评分
        if current_score < self.alert_thresholds['interference_score']:
            alert_msg = f"[{timestamp}] {band} 信道{channel} - 干扰评分{current_score:.1f}/100 低于阈值{self.alert_thresholds['interference_score']}"
            alerts.append(alert_msg)
            self.alert_history.append(alert_msg)
        
        # 检查信道拥挤度
        if network_count > self.alert_thresholds['channel_congestion']:
            alert_msg = f"[{timestamp}] {band} 信道{channel} - 网络数{network_count}个 超过阈值{self.alert_thresholds['channel_congestion']}"
            alerts.append(alert_msg)
            self.alert_history.append(alert_msg)
        
        # 检查质量下降
        baseline_key = f"{band}_{channel}"
        if baseline_key in self.baseline_quality:
            baseline_score = self.baseline_quality[baseline_key]
            quality_drop = baseline_score - current_score
            if quality_drop > self.alert_thresholds['quality_drop']:
                alert_msg = f"[{timestamp}] {band} 信道{channel} - 质量下降{quality_drop:.1f}分（从{baseline_score:.1f}降至{current_score:.1f}）"
                alerts.append(alert_msg)
                self.alert_history.append(alert_msg)
        else:
            # 设置基线
            self.baseline_quality[baseline_key] = current_score
        
        # 显示告警
        if alerts:
            # 获取推荐信道
            region = self.region_var.get()
            if region != "全部地区对比":
                channels = self.CHANNEL_REGIONS.get(region, {}).get(band, [])
                usage = self.channel_usage.get(band, {})
                scores = {ch: self._calculate_interference_score(ch, usage, band) for ch in channels}
                best_channel = max(scores.items(), key=lambda x: x[1])[0] if scores else None
                
                # 构建告警原因列表
                alert_reasons = '\n'.join(['• ' + a.split('] ')[1] for a in alerts])
                
                alert_window_msg = f"""🔔 质量告警

频段: {band}
当前信道: {channel}
当前评分: {current_score:.1f}/100
网络数: {network_count}个

触发原因:
{alert_reasons}

推荐信道: {best_channel} (评分: {scores.get(best_channel, 0):.1f}/100)

建议: 立即切换到推荐信道以改善网络质量"""
                
                messagebox.showwarning("质量告警", alert_window_msg)
    
    def _show_6ghz_optimization(self):
        """✅ Phase 2优化: 6GHz频段专项优化窗口"""
        opt_window = tk.Toplevel(self.parent)
        opt_window.title("🌐 WiFi 6E/7 - 6GHz频段专项优化")
        opt_window.geometry("900x700")
        
        # 标题
        title_frame = ttk.Frame(opt_window)
        title_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(title_frame, 
                 text="6GHz频段专项优化 - WiFi 6E/7",
                 font=('Microsoft YaHei', 14, 'bold')).pack()
        ttk.Label(title_frame,
                 text="高频段特性：高速率 | 低延迟 | 低干扰 | 穿墙弱",
                 font=('Microsoft YaHei', 10),
                 foreground='gray').pack()
        
        # 创建Notebook标签页
        notebook = ttk.Notebook(opt_window)
        notebook.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Tab 1: 覆盖范围预测
        self._create_coverage_tab(notebook)
        
        # Tab 2: 5G+6G协同策略
        self._create_strategy_tab(notebook)
        
        # Tab 3: UNII频段分析
        self._create_unii_tab(notebook)
    
    def _create_coverage_tab(self, notebook):
        """创建覆盖范围预测标签页"""
        coverage_frame = ttk.Frame(notebook)
        notebook.add(coverage_frame, text="📡 覆盖范围预测")
        
        # 输入参数
        param_frame = ttk.LabelFrame(coverage_frame, text="⚙️ 输入参数", padding=10)
        param_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(param_frame, text="AP发射功率(dBm):").grid(row=0, column=0, sticky='w', pady=5)
        tx_power_var = tk.IntVar(value=20)
        ttk.Spinbox(param_frame, from_=10, to=30, textvariable=tx_power_var, width=10).grid(row=0, column=1, pady=5)
        
        ttk.Label(param_frame, text="穿墙数量:").grid(row=1, column=0, sticky='w', pady=5)
        wall_count_var = tk.IntVar(value=2)
        ttk.Spinbox(param_frame, from_=0, to=5, textvariable=wall_count_var, width=10).grid(row=1, column=1, pady=5)
        
        ttk.Label(param_frame, text="环境类型:").grid(row=2, column=0, sticky='w', pady=5)
        env_type_var = tk.StringVar(value="办公室")
        ttk.Combobox(param_frame, textvariable=env_type_var,
                    values=["开放空间", "办公室", "住宅", "工业环境"],
                    width=15, state='readonly').grid(row=2, column=1, pady=5)
        
        # 结果显示
        result_frame = ttk.LabelFrame(coverage_frame, text="📊 预测结果", padding=10)
        result_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        result_text = tk.Text(result_frame, height=15, width=70, font=('Consolas', 10))
        result_text.pack(fill='both', expand=True)
        
        def calculate_coverage():
            """计算6GHz覆盖范围"""
            tx_power = tx_power_var.get()
            wall_count = wall_count_var.get()
            env_type = env_type_var.get()
            
            # 环境损耗系数
            env_loss = {
                "开放空间": 0,
                "办公室": 5,
                "住宅": 8,
                "工业环境": 12
            }.get(env_type, 5)
            
            # Friis公式计算（简化版）
            wall_loss_6g = wall_count * self.ghz6_attenuation_db_per_wall
            total_loss_6g = wall_loss_6g + env_loss
            effective_power_6g = tx_power - total_loss_6g
            
            # 估算覆盖距离
            coverage_6g_excellent = max(0, int((effective_power_6g + 60) * 2))
            coverage_6g_good = max(0, int((effective_power_6g + 70) * 2.5))
            coverage_6g_usable = max(0, int((effective_power_6g + 80) * 3))
            
            # 计算5GHz作为对比
            wall_loss_5g = wall_count * self.ghz5_attenuation_db_per_wall
            total_loss_5g = wall_loss_5g + env_loss * 0.7
            effective_power_5g = tx_power - total_loss_5g
            
            coverage_5g_excellent = max(0, int((effective_power_5g + 60) * 2.5))
            coverage_5g_good = max(0, int((effective_power_5g + 70) * 3))
            coverage_5g_usable = max(0, int((effective_power_5g + 80) * 3.5))
            
            result_text.delete('1.0', 'end')
            result = f"""{'='*60}
  6GHz频段覆盖范围预测（Friis公式）
{'='*60}

📋 输入参数:
  • AP发射功率: {tx_power} dBm
  • 穿墙数量: {wall_count} 面墙
  • 环境类型: {env_type}
  • 环境损耗: {env_loss} dB

📊 6GHz频段覆盖范围:
  🟢 优秀信号: ~{coverage_6g_excellent}米
  🟡 良好信号: ~{coverage_6g_good}米
  🟠 可用信号: ~{coverage_6g_usable}米
  • 穿墙损耗: {wall_loss_6g:.1f} dB
  • 总损耗: {total_loss_6g:.1f} dB

📊 5GHz频段覆盖范围（对比）:
  🟢 优秀信号: ~{coverage_5g_excellent}米
  🟡 良好信号: ~{coverage_5g_good}米
  🟠 可用信号: ~{coverage_5g_usable}米
  • 穿墙损耗: {wall_loss_5g:.1f} dB
  • 总损耗: {total_loss_5g:.1f} dB

📈 对比分析:
  • 5GHz覆盖优势: +{coverage_5g_good - coverage_6g_good}米 ({(coverage_5g_good - coverage_6g_good)*100//coverage_6g_good if coverage_6g_good > 0 else 0}%)
  • 6GHz穿墙衰减: {self.ghz6_attenuation_db_per_wall} dB/墙
  • 5GHz穿墙衰减: {self.ghz5_attenuation_db_per_wall} dB/墙

💡 优化建议:
"""
            if wall_count >= 3:
                result += "  ⚠️ 穿墙过多，6GHz信号衰减严重\n  → 建议: 使用5GHz或增加AP数量\n"
            elif coverage_6g_good < 15:
                result += "  ⚠️ 6GHz覆盖范围有限\n  → 建议: 5G+6G双频组网\n"
            else:
                result += "  ✅ 6GHz适合当前环境\n  → 建议: 高速设备使用6GHz\n"
            
            result_text.insert('1.0', result)
        
        ModernButton(param_frame, text="🔍 计算覆盖",
                    command=calculate_coverage, style='primary').grid(row=3, column=0, columnspan=2, pady=10)
    
    def _create_strategy_tab(self, notebook):
        """创建5G+6G协同策略标签页"""
        strategy_frame = ttk.Frame(notebook)
        notebook.add(strategy_frame, text="🔄 5G+6G协同")
        
        strategy_text = tk.Text(strategy_frame, wrap='word', font=('Microsoft YaHei', 10))
        strategy_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        strategy_content = """╔══════════════════════════════════════════════════╗
║         5G + 6G 双频协同部署策略                  ║
╚══════════════════════════════════════════════════╝

🎯 策略1: 设备类型分流
  • 6GHz频段:
    - WiFi 6E/7笔记本（高性能）
    - 游戏主机、VR设备
    - 企业高速传输终端
    - 优势: 320MHz带宽，低延迟<2ms
  
  • 5GHz频段:
    - WiFi 5/6普通设备
    - 手机、平板
    - 智能电视、NAS
    - 优势: 覆盖范围广，兼容性好

🎯 策略2: 场景优化部署
  • 会议室/办公桌（近距离）:
    - 主用6GHz（高速率，低干扰）
    - 备用5GHz（移动漫游）
  
  • 走廊/远距离:
    - 主用5GHz（穿墙能力强）
    - 6GHz按需启用

🎯 策略3: 负载均衡
  • 智能分流:
    - 高带宽任务 → 6GHz
    - 普通任务 → 5GHz
    - 2.4GHz IoT设备独立
  
  • 动态调整:
    - 监控各频段负载
    - 自动推荐切换

📊 部署参数建议:
  • 6GHz信道: UNII-5/7 (干扰最少)
  • 5GHz信道: 36/149 (避开DFS)
  • 信道宽度: 6GHz 160/320MHz, 5GHz 80MHz
  • AP间距: 6GHz 10-15米, 5GHz 15-25米

⚠️ 注意事项:
  • 6GHz不穿墙，需密集部署
  • 老设备无法使用6GHz
  • 企业需支持MLO（多链路）
  • 定期监控干扰变化

💡 最佳实践:
  1. 小范围高密度区域优先6GHz
  2. 大范围覆盖优先5GHz
  3. 关键业务双频冗余
  4. 定期测试切换性能
"""
        strategy_text.insert('1.0', strategy_content)
        strategy_text.config(state='disabled')
    
    def _create_unii_tab(self, notebook):
        """创建UNII频段分析标签页"""
        unii_frame = ttk.Frame(notebook)
        notebook.add(unii_frame, text="📡 UNII频段")
        
        unii_text = tk.Text(unii_frame, wrap='word', font=('Consolas', 9))
        unii_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        unii_content = """═══════════════════════════════════════════════════════════
  6GHz UNII频段详细分析（WiFi 6E/7）
═══════════════════════════════════════════════════════════

📡 UNII-5频段 (5925-6425 MHz)
  • 信道范围: 1, 5, 9, 13, ..., 93 (共24个信道)
  • 特性: 低干扰，适合室内高密度部署
  • 推荐: ⭐⭐⭐⭐⭐ 首选频段
  • 应用: 企业办公、会议室、高密度场景
  • 信道宽度: 支持20/40/80/160/320MHz

📡 UNII-6频段 (6425-6525 MHz)
  • 信道范围: 97, 101, 105, ..., 117 (共6个信道)
  • 特性: 中等干扰，覆盖范围适中
  • 推荐: ⭐⭐⭐⭐ 备选频段
  • 应用: 混合环境、中密度部署
  • 限制: 部分地区受管制

📡 UNII-7频段 (6525-6875 MHz)
  • 信道范围: 121, 125, 129, ..., 189 (共18个信道)
  • 特性: 极低干扰，高频段特性
  • 推荐: ⭐⭐⭐⭐⭐ 高性能场景
  • 应用: VR/AR、8K流媒体、工业4.0
  • 优势: 支持320MHz超宽信道（WiFi 7）

📡 UNII-8频段 (6875-7125 MHz)
  • 信道范围: 193, 197, 201, ..., 233 (共11个信道)
  • 特性: 最高频段，损耗最大
  • 推荐: ⭐⭐⭐ 特殊场景
  • 应用: 超近距离、极高速率需求
  • 限制: 多数地区未开放或受限

💡 信道选择策略:
  1. 室内高密度: UNII-5 (信道1-93)
  2. 高性能需求: UNII-7 (信道121-189) + 320MHz
  3. 避免边缘: 不推荐UNII-8（兼容性差）
  4. 动态调整: 根据干扰情况切换UNII频段

📊 各频段对比:
  ┌─────────┬────────┬────────┬──────────┐
  │ UNII频段 │ 信道数 │ 干扰度 │ 推荐指数 │
  ├─────────┼────────┼────────┼──────────┤
  │ UNII-5  │   24   │  极低  │  ⭐⭐⭐⭐⭐  │
  │ UNII-6  │    6   │   低   │  ⭐⭐⭐⭐   │
  │ UNII-7  │   18   │  极低  │  ⭐⭐⭐⭐⭐  │
  │ UNII-8  │   11   │   低   │  ⭐⭐⭐    │
  └─────────┴────────┴────────┴──────────┘

⚠️ 使用注意:
  • 不同国家/地区UNII频段开放情况不同
  • 中国: UNII-5/6/7 已开放，UNII-8 待定
  • 美国: 全部UNII频段开放
  • 欧洲: UNII-5/6/7 开放，UNII-8 部分开放
  • 使用前请确认本地法规
"""
        unii_text.insert('1.0', unii_content)
        unii_text.config(state='disabled')
    
    def get_frame(self):
        """获取框架"""
        return self.frame


# ═══════════════════════════════════════════════════════════
#                   Phase 2优化: 异步热力图生成器
# ═══════════════════════════════════════════════════════════

class AsyncHeatmapGenerator:
    """✅ Phase 2优化: 异步热力图生成器（LRU缓存+多线程）"""
    
    def __init__(self, cache_size=10):
        self.cache = {}  # 热力图缓存
        self.cache_order = []  # LRU顺序
        self.cache_size = cache_size
        self.computing = False
        self.compute_thread = None
        import threading
        self._lock = threading.Lock()  # ✅ P1: 保护computing标志
    
    def generate_async(self, channels, usage, band, callback, dfs_channels=None, frame=None):
        """异步生成热力图矩阵
        
        Args:
            frame: Tkinter框架引用，用于线程安全地调度回调到主线程。
                   若提供，非缓存回调将通过 frame.after(0,...) 在主线程执行。
        """
        # 生成缓存键
        cache_key = self._make_cache_key(channels, usage, band)
        
        # 检查缓存（在主线程，直接回调安全）
        if cache_key in self.cache:
            result = self.cache[cache_key]
            callback(result, from_cache=True)
            return
        
        # 缓存未命中，启动异步计算
        with self._lock:
            if self.computing:
                return  # 已有计算在进行
            self.computing = True
        
        import threading
        def compute_task():
            try:
                # 计算干扰矩阵
                if band == '2.4GHz':
                    matrix = self._compute_2ghz_matrix(channels, usage)
                else:  # 5GHz
                    matrix = self._compute_5ghz_matrix(channels, usage, dfs_channels)
                
                # 存入缓存
                self._add_to_cache(cache_key, matrix)
                
                # ✅ 线程安全: 通过 frame.after(0) 将 Tkinter 回调分发到主线程
                if frame is not None:
                    frame.after(0, lambda m=matrix: callback(m, from_cache=False))
                else:
                    callback(matrix, from_cache=False)
                
            except Exception as e:
                print(f"热力图计算错误: {e}")
            finally:
                with self._lock:
                    self.computing = False
        
        self.compute_thread = threading.Thread(target=compute_task, daemon=True)
        self.compute_thread.start()
    
    def _make_cache_key(self, channels, usage, band):
        """生成缓存键"""
        # 使用信道列表和占用数据的哈希值
        usage_hash = hash(str(sorted(
            (k, v.get('weight', 0) if isinstance(v, dict) else v)
            for k, v in usage.items()
        )))
        return (tuple(channels), usage_hash, band)
    
    def _add_to_cache(self, key, value):
        """添加到LRU缓存"""
        if key in self.cache:
            # 更新顺序
            self.cache_order.remove(key)
            self.cache_order.append(key)
        else:
            # 新增缓存
            if len(self.cache) >= self.cache_size:
                # 移除最旧的
                oldest = self.cache_order.pop(0)
                del self.cache[oldest]
            
            self.cache[key] = value
            self.cache_order.append(key)
    
    def _compute_2ghz_matrix(self, channels, usage):
        """计算2.4GHz干扰矩阵（向量化）"""
        n = len(channels)
        matrix = np.zeros((n, n))
        
        # 向量化计算
        for i, ch1 in enumerate(channels):
            for j, ch2 in enumerate(channels):
                if abs(ch1 - ch2) <= 4:  # 重叠范围
                    distance = abs(ch1 - ch2)
                    interference_factor = (5 - distance) / 5
                    
                    ch2_data = usage.get(ch2, {})
                    if isinstance(ch2_data, dict):
                        matrix[i, j] = ch2_data.get('weight', 0) * interference_factor
                    else:
                        matrix[i, j] = (ch2_data * interference_factor) if ch2_data else 0
        
        return matrix
    
    def _compute_5ghz_matrix(self, channels, usage, dfs_channels):
        """计算5GHz干扰矩阵（考虑信道绑定）"""
        n = len(channels)
        matrix = np.zeros((n, n))
        
        # 信道绑定配置
        bonding_40 = [
            ([36, 40], 38), ([44, 48], 46), ([52, 56], 54),
            ([60, 64], 62), ([100, 104], 102), ([108, 112], 110),
            ([116, 120], 118), ([124, 128], 126), ([132, 136], 134),
            ([149, 153], 151), ([157, 161], 159)
        ]
        
        bonding_80 = [
            ([36, 40, 44, 48], 42), ([52, 56, 60, 64], 58),
            ([100, 104, 108, 112], 106), ([116, 120, 124, 128], 122),
            ([149, 153, 157, 161], 155)
        ]
        
        # 计算干扰
        for i, ch1 in enumerate(channels):
            # 找出ch1的绑定组
            bonded_group = [ch1]
            
            # 检查40MHz绑定
            for group, center in bonding_40:
                if ch1 in group:
                    bonded_group.extend(group)
            
            # 检查80MHz绑定
            for group, center in bonding_80:
                if ch1 in group:
                    bonded_group.extend(group)
            
            bonded_group = list(set(bonded_group))
            
            for j, ch2 in enumerate(channels):
                if ch2 in bonded_group:
                    ch2_data = usage.get(ch2, {})
                    if isinstance(ch2_data, dict):
                        matrix[i, j] = ch2_data.get('weight', 0)
                    else:
                        matrix[i, j] = ch2_data if ch2_data else 0
        
        return matrix
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        self.cache_order.clear()
