"""
WiFi信号趋势分析模块
提供24小时信号历史记录、趋势图和统计分析
"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import numpy as np


class SignalTrendAnalyzer:
    """信号趋势分析器"""
    
    def __init__(self, data_file: str = "signal_history.json"):
        self.data_file = data_file
        self.history_data = []  # [{timestamp, ssid, signal_dbm}]
        self.max_days = 7  # 保留7天数据
        self._load_history()
    
    def add_data_point(self, ssid: str, signal_dbm: float):
        """添加数据点"""
        data_point = {
            'timestamp': datetime.now().isoformat(),
            'ssid': ssid,
            'signal_dbm': signal_dbm
        }
        self.history_data.append(data_point)
        
        # 清理旧数据
        self._cleanup_old_data()
        
        # 自动保存（每10个数据点保存一次）
        if len(self.history_data) % 10 == 0:
            self._save_history()
    
    def get_trend_data(self, ssid: str, hours: int = 24) -> Dict:
        """
        获取指定时间范围的趋势数据
        
        Args:
            ssid: WiFi名称
            hours: 时间范围（小时）
            
        Returns:
            包含时间序列和信号数据的字典
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # 过滤数据
        filtered_data = [
            d for d in self.history_data
            if d['ssid'] == ssid and 
            datetime.fromisoformat(d['timestamp']) >= cutoff_time
        ]
        
        if not filtered_data:
            return {
                'timestamps': [],
                'signals': [],
                'stats': {}
            }
        
        # 提取时间和信号数据
        timestamps = [datetime.fromisoformat(d['timestamp']) for d in filtered_data]
        signals = [d['signal_dbm'] for d in filtered_data]
        
        # 计算统计数据
        stats = {
            'max': max(signals),
            'min': min(signals),
            'mean': np.mean(signals),
            'std': np.std(signals),
            'max_time': timestamps[signals.index(max(signals))],
            'min_time': timestamps[signals.index(min(signals))],
            'data_points': len(signals),
            'time_span': (timestamps[-1] - timestamps[0]).total_seconds() / 3600  # 小时
        }
        
        return {
            'timestamps': timestamps,
            'signals': signals,
            'stats': stats
        }
    
    def generate_trend_chart(self, ssid: str, hours: int = 24) -> Figure:
        """
        生成趋势图
        
        Args:
            ssid: WiFi名称
            hours: 时间范围（小时）
            
        Returns:
            matplotlib Figure对象
        """
        trend_data = self.get_trend_data(ssid, hours)
        
        fig = Figure(figsize=(12, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        if not trend_data['timestamps']:
            ax.text(0.5, 0.5, f'暂无{ssid}的历史数据', 
                   ha='center', va='center', fontsize=14)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            return fig
        
        timestamps = trend_data['timestamps']
        signals = trend_data['signals']
        stats = trend_data['stats']
        
        # 绘制趋势线
        ax.plot(timestamps, signals, 'b-', linewidth=2, label='信号强度')
        
        # 标注峰值
        ax.plot(stats['max_time'], stats['max'], 'ro', markersize=10, 
               label=f"峰值: {stats['max']:.1f} dBm")
        ax.annotate(f"{stats['max']:.1f} dBm", 
                   xy=(stats['max_time'], stats['max']),
                   xytext=(10, 10), textcoords='offset points',
                   fontsize=10, color='red',
                   bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.7),
                   arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
        
        # 标注谷值
        ax.plot(stats['min_time'], stats['min'], 'go', markersize=10,
               label=f"谷值: {stats['min']:.1f} dBm")
        ax.annotate(f"{stats['min']:.1f} dBm",
                   xy=(stats['min_time'], stats['min']),
                   xytext=(10, -20), textcoords='offset points',
                   fontsize=10, color='green',
                   bbox=dict(boxstyle='round,pad=0.5', fc='lightgreen', alpha=0.7),
                   arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
        
        # 绘制平均线
        ax.axhline(y=stats['mean'], color='orange', linestyle='--', 
                  linewidth=1.5, label=f"平均值: {stats['mean']:.1f} dBm")
        
        # 填充标准差区域
        ax.fill_between(timestamps, 
                       stats['mean'] - stats['std'],
                       stats['mean'] + stats['std'],
                       alpha=0.2, color='blue', label='标准差范围')
        
        # 信号质量区域标识
        ax.axhspan(-100, -80, alpha=0.1, color='red', label='信号很弱')
        ax.axhspan(-80, -70, alpha=0.1, color='orange', label='信号较弱')
        ax.axhspan(-70, -50, alpha=0.1, color='yellow', label='信号良好')
        ax.axhspan(-50, -30, alpha=0.1, color='green', label='信号优秀')
        
        # 设置标题和标签
        ax.set_title(f'{ssid} - 信号强度趋势 (最近{hours}小时)', 
                    fontsize=14, fontweight='bold', fontproperties='Microsoft YaHei')
        ax.set_xlabel('时间', fontsize=12, fontproperties='Microsoft YaHei')
        ax.set_ylabel('信号强度 (dBm)', fontsize=12, fontproperties='Microsoft YaHei')
        
        # 设置时间轴格式化器
        if hours <= 1:
            # 1小时内：显示 时:分
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=10))
        elif hours <= 6:
            # 6小时内：显示 时:分
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
        elif hours <= 24:
            # 24小时内：显示 月-日 时:分
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=3))
        else:
            # 超过24小时：显示 月-日
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator())
        
        # 网格
        ax.grid(True, linestyle=':', alpha=0.6)
        
        # 图例
        ax.legend(loc='best', fontsize=9, prop={'family': 'Microsoft YaHei'})
        
        # 旋转x轴标签
        fig.autofmt_xdate()
        
        # 紧凑布局
        fig.tight_layout()
        
        return fig
    
    def get_comparison_data(self, ssids: List[str], hours: int = 24) -> Dict:
        """获取多个WiFi的对比数据"""
        comparison = {}
        
        for ssid in ssids:
            trend_data = self.get_trend_data(ssid, hours)
            if trend_data['timestamps']:
                comparison[ssid] = trend_data['stats']
        
        return comparison
    
    def export_to_csv(self, ssid: str, hours: int = 24, filename: Optional[str] = None) -> str:
        """导出为CSV文件"""
        import csv
        
        trend_data = self.get_trend_data(ssid, hours)
        
        if not trend_data['timestamps']:
            raise ValueError(f"没有{ssid}的数据可导出")
        
        if filename is None:
            filename = f"signal_trend_{ssid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['时间', '信号强度(dBm)', 'SSID'])
            
            for ts, sig in zip(trend_data['timestamps'], trend_data['signals']):
                writer.writerow([ts.strftime('%Y-%m-%d %H:%M:%S'), f"{sig:.1f}", ssid])
        
        return filename
    
    def get_available_ssids(self, hours: int = 24) -> List[str]:
        """获取有历史数据的SSID列表"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        ssids = set()
        for d in self.history_data:
            if datetime.fromisoformat(d['timestamp']) >= cutoff_time:
                ssids.add(d['ssid'])
        
        return sorted(list(ssids))
    
    def _load_history(self):
        """加载历史数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.history_data = json.load(f)
            except Exception as e:
                print(f"加载历史数据失败: {e}")
                self.history_data = []
        else:
            self.history_data = []
    
    def _save_history(self):
        """保存历史数据"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.history_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史数据失败: {e}")
    
    def _cleanup_old_data(self):
        """清理超过保留期的数据"""
        cutoff_time = datetime.now() - timedelta(days=self.max_days)
        
        self.history_data = [
            d for d in self.history_data
            if datetime.fromisoformat(d['timestamp']) >= cutoff_time
        ]
    
    def get_hourly_average(self, ssid: str, hours: int = 24) -> Dict:
        """获取每小时平均信号强度"""
        trend_data = self.get_trend_data(ssid, hours)
        
        if not trend_data['timestamps']:
            return {}
        
        # 按小时分组
        hourly_data = {}
        for ts, sig in zip(trend_data['timestamps'], trend_data['signals']):
            hour_key = ts.replace(minute=0, second=0, microsecond=0)
            if hour_key not in hourly_data:
                hourly_data[hour_key] = []
            hourly_data[hour_key].append(sig)
        
        # 计算每小时平均值
        hourly_avg = {
            hour: np.mean(signals)
            for hour, signals in hourly_data.items()
        }
        
        return hourly_avg
    
    def clear_history(self, ssid: Optional[str] = None):
        """清空历史数据"""
        if ssid:
            self.history_data = [d for d in self.history_data if d['ssid'] != ssid]
        else:
            self.history_data = []
        
        self._save_history()
