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
    DFS_CHANNELS = list(range(52, 145, 4))
    
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
        """显示分析结果"""
        self.result_text.delete('1.0', 'end')
        
        result = "=== 信道占用分析 ===\n\n"
        
        for band in ['2.4GHz', '5GHz', '6GHz']:
            usage = self.channel_usage.get(band, {})
            if not usage:
                continue
            
            result += f"{band}频段:\n"
            result += f"  占用信道: {len(usage)} 个\n"
            
            if usage:
                # 安全提取count值进行比较
                most_used = max(usage.items(), key=lambda x: self._get_channel_count(band, x[0]))
                count = self._get_channel_count(band, most_used[0])
                result += f"  最拥挤: 信道{most_used[0]} ({count}个网络)\n"
                
                # 找出空闲信道
                region = self.region_var.get()
                if region != "全部地区对比":
                    available = self.CHANNEL_REGIONS.get(region, {}).get(band, [])
                    free_channels = [ch for ch in available if ch not in usage]
                    if free_channels:
                        result += f"  空闲信道: {', '.join(map(str, free_channels[:5]))}"
                        if len(free_channels) > 5:
                            result += f" 等{len(free_channels)}个"
                        result += "\n"
            
            result += "\n"
        
        self.result_text.insert('1.0', result)
    
    def _recommend_channel(self):
        """智能推荐信道"""
        if not self.channel_usage:
            messagebox.showwarning("提示", "请先点击'分析信道'")
            return
        
        region = self.region_var.get()
        if region == "全部地区对比":
            messagebox.showinfo("提示", "请选择具体地区进行推荐")
            return
        
        recommendations = []
        
        for band in ['2.4GHz', '5GHz']:
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
                recommendations.append(f"{band}频段推荐:\n")
                for ch, score in top_channels:
                    quality = "优秀" if score >= 80 else "良好" if score >= 60 else "一般"
                    recommendations.append(f"  信道{ch} (评分:{score:.0f}, {quality})\n")
                recommendations.append("\n")
        
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
                    'signal': int(net.get('signal', '-100').replace(' dBm', '')) if 'dBm' in str(net.get('signal', '')) else -100,
                    'bssid': net.get('mac', 'Unknown')
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
    
    def _calculate_interference_score(self, ch: int, usage: dict, band: str) -> float:
        """✅ P0: 计算信道干扰评分（IEEE 802.11标准）"""
        score = 100
        
        # 自身占用惩罚（使用加权值）
        if ch in usage:
            ch_data = usage[ch]
            if isinstance(ch_data, dict):
                score -= ch_data['weight'] * 30  # 权重惩罚
            else:
                score -= ch_data * 25  # 兼容旧格式
        
        if band == '2.4GHz':
            # 2.4GHz: 22MHz带宽，±4信道重叠
            for offset in range(-4, 5):
                adj_ch = ch + offset
                if 1 <= adj_ch <= 13 and adj_ch != ch and adj_ch in usage:
                    # 距离越近干扰越强（反比衰减）
                    interference_factor = (5 - abs(offset)) / 5
                    
                    adj_data = usage[adj_ch]
                    if isinstance(adj_data, dict):
                        score -= adj_data['weight'] * 15 * interference_factor
                    else:
                        score -= adj_data * 15 * interference_factor
        
        elif band == '5GHz':
            # 5GHz: 考虑信道绑定干扰
            bonded_group = self._get_bonded_group(ch)
            for bonded_ch in bonded_group:
                if bonded_ch != ch and bonded_ch in usage:
                    bonded_data = usage[bonded_ch]
                    if isinstance(bonded_data, dict):
                        score -= bonded_data['weight'] * 20
                    else:
                        score -= bonded_data * 20
        
        return max(0, score)
    
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
        """✅ P2: 显示干扰热力图"""
        if not self.channel_usage:
            messagebox.showwarning("提示", "请先点击'分析信道'扫描网络")
            return
        
        # 创建热力图窗口
        heatmap_window = tk.Toplevel(self.parent)
        heatmap_window.title("🔥 信道干扰热力图")
        heatmap_window.geometry("1000x800")
        
        # 创建图表
        fig = Figure(figsize=(10, 8))
        
        # 2.4GHz热力图
        ax1 = fig.add_subplot(2, 1, 1)
        self._draw_heatmap_2ghz(ax1)
        
        # 5GHz热力图
        ax2 = fig.add_subplot(2, 1, 2)
        self._draw_heatmap_5ghz(ax2)
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, heatmap_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        
        toolbar = NavigationToolbar2Tk(canvas, heatmap_window)
        toolbar.update()
    
    def _draw_heatmap_2ghz(self, ax):
        """绘制2.4GHz干扰热力图"""
        channels = list(range(1, 14))
        usage = self.channel_usage.get('2.4GHz', {})
        
        # 计算干扰矩阵
        interference_matrix = np.zeros((len(channels), len(channels)))
        
        for i, ch1 in enumerate(channels):
            for j, ch2 in enumerate(channels):
                if abs(ch1 - ch2) <= 4:  # 重叠范围
                    distance = abs(ch1 - ch2)
                    interference_factor = (5 - distance) / 5
                    
                    ch2_data = usage.get(ch2, {})
                    if isinstance(ch2_data, dict):
                        interference_matrix[i, j] = ch2_data.get('weight', 0) * interference_factor
                    else:
                        interference_matrix[i, j] = ch2_data * interference_factor if ch2_data else 0
        
        # 绘制热力图
        im = ax.imshow(interference_matrix, cmap='RdYlGn_r', aspect='auto', interpolation='bilinear')
        
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
    
    def _draw_heatmap_5ghz(self, ax):
        """绘制5GHz干扰热力图"""
        channels = [36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112, 
                   116, 120, 124, 128, 132, 136, 140, 149, 153, 157, 161, 165]
        usage = self.channel_usage.get('5GHz', {})
        
        # 计算干扰矩阵
        interference_matrix = np.zeros((len(channels), len(channels)))
        
        for i, ch1 in enumerate(channels):
            bonded_group = self._get_bonded_group(ch1)
            for j, ch2 in enumerate(channels):
                if ch2 in bonded_group:
                    ch2_data = usage.get(ch2, {})
                    if isinstance(ch2_data, dict):
                        interference_matrix[i, j] = ch2_data.get('weight', 0)
                    else:
                        interference_matrix[i, j] = ch2_data if ch2_data else 0
        
        # 绘制热力图
        im = ax.imshow(interference_matrix, cmap='RdYlGn_r', aspect='auto', interpolation='nearest')
        
        ax.set_xticks(range(len(channels)))
        ax.set_xticklabels(channels, rotation=45, fontsize=8)
        ax.set_yticks(range(len(channels)))
        ax.set_yticklabels(channels, fontsize=8)
        ax.set_xlabel('信道')
        ax.set_ylabel('受影响信道')
        ax.set_title('5GHz信道干扰热力图（考虑信道绑定）', fontweight='bold')
        
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
    
    def get_frame(self):
        """获取框架"""
        return self.frame
