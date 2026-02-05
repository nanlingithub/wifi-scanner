"""
信道利用率分析模块
提供WiFi信道拥挤度分析和可视化功能
"""
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import matplotlib
matplotlib.use('TkAgg')
from collections import defaultdict
from typing import Dict, List, Tuple
import numpy as np

class ChannelUtilizationAnalyzer:
    """信道利用率分析器"""
    
    # 2.4GHz频段信道列表
    CHANNELS_24GHZ = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
    # 5GHz频段常用信道
    CHANNELS_5GHZ = [36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112, 
                     116, 120, 124, 128, 132, 136, 140, 144, 149, 153, 157, 161, 165]
    
    def __init__(self):
        """初始化分析器"""
        self.channel_data = defaultdict(list)  # {channel: [network_list]}
        self.band_stats = {'2.4GHz': {}, '5GHz': {}}  # 频段统计
    
    def analyze_channels(self, wifi_networks: List[Dict]) -> Dict:
        """
        分析WiFi网络的信道分布
        
        Args:
            wifi_networks: WiFi网络列表，每个包含 {ssid, channel, signal, bssid}
        
        Returns:
            分析结果字典
        """
        # 清空旧数据
        self.channel_data.clear()
        self.band_stats = {'2.4GHz': {}, '5GHz': {}}
        
        # 按信道分组
        for network in wifi_networks:
            channel = network.get('channel', 0)
            if channel > 0:
                self.channel_data[channel].append(network)
        
        # 统计各频段
        total_24 = 0
        total_5 = 0
        
        for channel, networks in self.channel_data.items():
            count = len(networks)
            if channel in self.CHANNELS_24GHZ:
                self.band_stats['2.4GHz'][channel] = count
                total_24 += count
            elif channel in self.CHANNELS_5GHZ:
                self.band_stats['5GHz'][channel] = count
                total_5 += count
        
        # 生成分析结果
        result = {
            'total_networks': len(wifi_networks),
            'total_24ghz': total_24,
            'total_5ghz': total_5,
            'channels_24ghz': dict(self.band_stats['2.4GHz']),
            'channels_5ghz': dict(self.band_stats['5GHz']),
            'most_congested_24': self._get_most_congested('2.4GHz'),
            'most_congested_5': self._get_most_congested('5GHz'),
            'recommended_24': self._recommend_channel('2.4GHz'),
            'recommended_5': self._recommend_channel('5GHz')
        }
        
        return result
    
    def _get_most_congested(self, band: str) -> Tuple[int, int]:
        """获取最拥挤的信道"""
        if not self.band_stats[band]:
            return (0, 0)
        
        max_channel = max(self.band_stats[band].items(), key=lambda x: x[1])
        return max_channel
    
    def _recommend_channel(self, band: str) -> int:
        """推荐最佳信道"""
        channels = self.CHANNELS_24GHZ if band == '2.4GHz' else self.CHANNELS_5GHZ
        used_channels = self.band_stats[band]
        
        # 找使用最少的信道
        min_count = float('inf')
        best_channel = channels[0]
        
        for channel in channels:
            count = used_channels.get(channel, 0)
            if count < min_count:
                min_count = count
                best_channel = channel
        
        return best_channel
    
    def generate_pie_chart(self, title: str = "WiFi频段分布") -> Figure:
        """
        生成频段分布饼图
        
        Args:
            title: 图表标题
        
        Returns:
            matplotlib Figure对象
        """
        fig = Figure(figsize=(8, 6), facecolor='white')
        ax = fig.add_subplot(111)
        
        # 数据准备
        total_24 = sum(self.band_stats['2.4GHz'].values())
        total_5 = sum(self.band_stats['5GHz'].values())
        
        if total_24 == 0 and total_5 == 0:
            ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', fontsize=14)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            return fig
        
        # 绘制饼图
        labels = ['2.4GHz', '5GHz']
        sizes = [total_24, total_5]
        colors = ['#ff9999', '#66b3ff']
        explode = (0.05, 0.05)
        
        # 过滤掉0值
        filtered_data = [(l, s, c, e) for l, s, c, e in zip(labels, sizes, colors, explode) if s > 0]
        if filtered_data:
            labels, sizes, colors, explode = zip(*filtered_data)
        
        wedges, texts, autotexts = ax.pie(
            sizes, 
            explode=explode, 
            labels=labels, 
            colors=colors,
            autopct='%1.1f%%',
            shadow=True, 
            startangle=90,
            textprops={'fontsize': 10}
        )
        
        # 美化文本
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_weight('bold')
            autotext.set_fontsize(11)
        
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.axis('equal')
        
        return fig
    
    def generate_bar_chart(self, band: str = '2.4GHz', title: str = None) -> Figure:
        """
        生成信道利用率柱状图
        
        Args:
            band: 频段选择 '2.4GHz' 或 '5GHz'
            title: 图表标题
        
        Returns:
            matplotlib Figure对象
        """
        if title is None:
            title = f"{band}频段信道利用率"
        
        fig = Figure(figsize=(12, 6), facecolor='white')
        ax = fig.add_subplot(111)
        
        # 获取信道数据
        channel_stats = self.band_stats[band]
        if not channel_stats:
            ax.text(0.5, 0.5, f'{band}频段暂无数据', ha='center', va='center', fontsize=14)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            return fig
        
        # 准备数据
        channels = sorted(channel_stats.keys())
        counts = [channel_stats[ch] for ch in channels]
        
        # 颜色映射（根据拥挤度）
        max_count = max(counts) if counts else 1
        colors = []
        for count in counts:
            if count == 0:
                colors.append('#90EE90')  # 绿色 - 空闲
            elif count <= max_count * 0.3:
                colors.append('#FFD700')  # 黄色 - 较空闲
            elif count <= max_count * 0.6:
                colors.append('#FFA500')  # 橙色 - 中等
            else:
                colors.append('#FF6347')  # 红色 - 拥挤
        
        # 绘制柱状图
        bars = ax.bar(range(len(channels)), counts, color=colors, alpha=0.8, edgecolor='black', linewidth=1)
        
        # 在柱子上方显示数值
        for i, (bar, count) in enumerate(zip(bars, counts)):
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{int(count)}',
                       ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        # 设置坐标轴
        ax.set_xlabel('信道号', fontsize=12, fontweight='bold')
        ax.set_ylabel('网络数量', fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.set_xticks(range(len(channels)))
        ax.set_xticklabels([str(ch) for ch in channels], rotation=45)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        # 添加图例
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#90EE90', label='空闲 (0)'),
            Patch(facecolor='#FFD700', label=f'较空闲 (1-{int(max_count*0.3)})'),
            Patch(facecolor='#FFA500', label=f'中等 ({int(max_count*0.3)+1}-{int(max_count*0.6)})'),
            Patch(facecolor='#FF6347', label=f'拥挤 ({int(max_count*0.6)+1}+)')
        ]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=9)
        
        fig.tight_layout()
        return fig
    
    def get_channel_details(self, channel: int) -> List[Dict]:
        """
        获取指定信道的详细网络列表
        
        Args:
            channel: 信道号
        
        Returns:
            网络列表
        """
        return self.channel_data.get(channel, [])
    
    def get_summary_text(self) -> str:
        """
        生成文本摘要
        
        Returns:
            摘要文本
        """
        total_24 = sum(self.band_stats['2.4GHz'].values())
        total_5 = sum(self.band_stats['5GHz'].values())
        
        lines = [
            "=" * 50,
            "📊 信道利用率分析报告",
            "=" * 50,
            f"\n总计网络数: {total_24 + total_5}",
            f"  • 2.4GHz: {total_24} 个",
            f"  • 5GHz: {total_5} 个",
            ""
        ]
        
        # 2.4GHz分析
        if self.band_stats['2.4GHz']:
            most_24 = self._get_most_congested('2.4GHz')
            recommend_24 = self._recommend_channel('2.4GHz')
            lines.extend([
                "【2.4GHz频段】",
                f"  最拥挤信道: {most_24[0]} ({most_24[1]} 个网络)",
                f"  推荐信道: {recommend_24}",
                ""
            ])
        
        # 5GHz分析
        if self.band_stats['5GHz']:
            most_5 = self._get_most_congested('5GHz')
            recommend_5 = self._recommend_channel('5GHz')
            lines.extend([
                "【5GHz频段】",
                f"  最拥挤信道: {most_5[0]} ({most_5[1]} 个网络)",
                f"  推荐信道: {recommend_5}",
                ""
            ])
        
        lines.append("=" * 50)
        return "\n".join(lines)
