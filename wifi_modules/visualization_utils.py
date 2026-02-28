#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WiFi可视化工具统一模块
整合热力图、频谱图、雷达图等通用可视化功能
减少代码重复，提高可维护性
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, ListedColormap, BoundaryNorm
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# 尝试导入高级插值库
try:
    from scipy.interpolate import Rbf, griddata
    from pykrige.ok import OrdinaryKriging
    KRIGING_AVAILABLE = True
except ImportError:
    from scipy.interpolate import griddata
    KRIGING_AVAILABLE = False


class HeatmapVisualizer:
    """热力图可视化器 - 统一热力图生成逻辑"""
    
    # 信号质量分级
    QUALITY_BOUNDS = [0, 20, 40, 60, 80, 100]
    QUALITY_COLORS = ['#e74c3c', '#e67e22', '#f39c12', '#3498db', '#2ecc71']
    QUALITY_LABELS = ['极弱', '弱', '一般', '良好', '优秀']
    
    def __init__(self, interpolation='rbf', resolution='auto', smooth='auto'):
        """
        初始化热力图可视化器
        
        Args:
            interpolation: 插值方法 ('rbf', 'kriging', 'idw', 'nearest')
            resolution: 网格分辨率 ('auto', 'low', 'medium', 'high', 或具体数值)
            smooth: 平滑参数 ('auto' 或具体数值)
        """
        self.interpolation = interpolation
        self.resolution = resolution
        self.smooth = smooth
    
    def plot_heatmap(self, x, y, values, ax=None, 
                     colormap='quality', show_points=True,
                     xlabel='X坐标 (米)', ylabel='Y坐标 (米)',
                     title='WiFi信号强度热力图',
                     aps=None, obstacles=None):
        """
        绘制热力图
        
        Args:
            x: X坐标数组
            y: Y坐标数组
            values: 信号值数组 (0-100)
            ax: matplotlib轴对象，None则创建新图
            colormap: 颜色映射 ('quality'质量分级, 'continuous'连续渐变)
            show_points: 是否显示测量点
            xlabel, ylabel, title: 图表标签
            aps: AP位置列表 [{'x': x, 'y': y, 'name': 'AP1'}, ...]
            obstacles: 障碍物列表 [{'type': 'wall', 'start': (x1,y1), 'end': (x2,y2)}, ...]
        
        Returns:
            ax: matplotlib轴对象
        """
        # 创建图表
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 8))
        
        # 数据验证
        if len(x) < 3:
            raise ValueError("至少需要3个数据点才能生成热力图")
        
        x = np.array(x)
        y = np.array(y)
        values = np.array(values)
        
        # 网格插值
        xi, yi, zi = self._interpolate(x, y, values)
        
        # 绘制热力图
        if colormap == 'quality':
            # 质量分级颜色映射
            cmap = ListedColormap(self.QUALITY_COLORS)
            norm = BoundaryNorm(self.QUALITY_BOUNDS, cmap.N)
            contour = ax.contourf(xi, yi, zi, levels=self.QUALITY_BOUNDS, 
                                 cmap=cmap, norm=norm, alpha=0.8)
            cbar = plt.colorbar(contour, ax=ax, ticks=[10, 30, 50, 70, 90])
            cbar.ax.set_yticklabels(self.QUALITY_LABELS)
            cbar.set_label('信号质量')
        else:
            # 连续渐变颜色映射
            colors = ['#e74c3c', '#e67e22', '#f39c12', '#3498db', '#2ecc71']
            cmap = LinearSegmentedColormap.from_list('signal', colors, N=100)
            contour = ax.contourf(xi, yi, zi, levels=20, cmap=cmap, alpha=0.8)
            cbar = plt.colorbar(contour, ax=ax)
            cbar.set_label('信号强度 (%)')
        
        # 标记测量点
        if show_points:
            ax.scatter(x, y, c='black', s=30, marker='x', label='测量点', zorder=5)
        
        # 标记AP位置
        if aps:
            for ap in aps:
                ax.plot(ap['x'], ap['y'], marker='*', markersize=25, 
                       color='red', markeredgecolor='white', markeredgewidth=2, zorder=6)
                ax.annotate(ap.get('name', 'AP'), 
                           xy=(ap['x'], ap['y']), xytext=(5, 5), 
                           textcoords='offset points', fontsize=9, fontweight='bold',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='red', alpha=0.7),
                           zorder=7)
        
        # 绘制障碍物
        if obstacles:
            for obs in obstacles:
                if obs['type'] == 'wall':
                    start, end = obs['start'], obs['end']
                    ax.plot([start[0], end[0]], [start[1], end[1]], 
                           'k-', linewidth=3, label='墙体' if obs == obstacles[0] else '', zorder=4)
        
        # 设置标签
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        if show_points or aps or obstacles:
            ax.legend(loc='best')
        
        ax.grid(True, alpha=0.3)
        
        return ax
    
    def _interpolate(self, x, y, values):
        """执行插值计算"""
        # 确定范围
        x_min, x_max = x.min(), x.max()
        y_min, y_max = y.min(), y.max()
        
        # 扩展小范围
        if x_max - x_min < 0.1:
            x_center = (x_max + x_min) / 2
            x_min, x_max = x_center - 0.5, x_center + 0.5
        if y_max - y_min < 0.1:
            y_center = (y_max + y_min) / 2
            y_min, y_max = y_center - 0.5, y_center + 0.5
        
        # 确定分辨率
        resolution = self._get_resolution(len(x))
        
        # 创建网格
        xi = np.linspace(x_min, x_max, resolution)
        yi = np.linspace(y_min, y_max, resolution)
        xi, yi = np.meshgrid(xi, yi)
        
        # 执行插值
        if self.interpolation == 'kriging' and KRIGING_AVAILABLE:
            try:
                OK = OrdinaryKriging(x, y, values, variogram_model='exponential')
                zi, ss = OK.execute('grid', xi[0], yi[:, 0])
                zi = zi.T
            except Exception as e:
                print(f"Kriging插值失败，使用RBF: {e}")
                zi = self._rbf_interpolate(x, y, values, xi, yi)
        elif self.interpolation == 'rbf':
            zi = self._rbf_interpolate(x, y, values, xi, yi)
        elif self.interpolation == 'idw':
            zi = self._idw_interpolate(x, y, values, xi, yi)
        else:  # nearest
            points = np.column_stack((x, y))
            zi = griddata(points, values, (xi, yi), method='nearest')
        
        # 钳制到 [0, 100]
        zi = np.clip(zi, 0, 100)
        
        return xi, yi, zi
    
    def _rbf_interpolate(self, x, y, values, xi, yi):
        """RBF插值"""
        smooth = self._get_smooth(values)
        rbf = Rbf(x, y, values, function='multiquadric', smooth=smooth)
        return rbf(xi, yi)
    
    def _idw_interpolate(self, x, y, values, xi, yi, power=2):
        """反距离加权(IDW)插值 - 快速预览模式"""
        zi = np.zeros_like(xi)
        for i in range(xi.shape[0]):
            for j in range(xi.shape[1]):
                distances = np.sqrt((x - xi[i, j])**2 + (y - yi[i, j])**2)
                distances[distances < 1e-10] = 1e-10  # 避免除零
                weights = 1.0 / distances**power
                zi[i, j] = np.sum(weights * values) / np.sum(weights)
        return zi
    
    def _get_resolution(self, num_points):
        """自适应网格分辨率"""
        if isinstance(self.resolution, int):
            return self.resolution
        elif self.resolution == 'auto':
            if num_points < 10:
                return 50
            elif num_points < 30:
                return 100
            else:
                return 200
        elif self.resolution == 'low':
            return 50
        elif self.resolution == 'medium':
            return 100
        elif self.resolution == 'high':
            return 200
        else:
            return 100
    
    def _get_smooth(self, values):
        """自适应平滑参数"""
        if isinstance(self.smooth, (int, float)):
            return self.smooth
        elif self.smooth == 'auto':
            # 根据信号变异性调整
            std = np.std(values)
            if std < 10:
                return 0.1
            elif std < 20:
                return 0.5
            else:
                return 1.0
        else:
            return 0.5


class SpectrumVisualizer:
    """频谱图可视化器 - 统一频谱分析图"""
    
    def __init__(self, style='modern'):
        """
        初始化频谱可视化器
        
        Args:
            style: 样式 ('modern'现代风格, 'classic'经典风格)
        """
        self.style = style
    
    def plot_spectrum(self, frequencies, powers, ssids=None, ax=None,
                     band='2.4GHz', title='WiFi频谱分析',
                     show_legend=True, top_n=10):
        """
        绘制频谱图
        
        Args:
            frequencies: 频率数组 (MHz)
            powers: 功率/RSSI数组 (dBm)
            ssids: SSID列表（可选）
            ax: matplotlib轴对象
            band: 频段标识
            title: 图表标题
            show_legend: 是否显示图例
            top_n: 显示前N个最强信号的SSID
        
        Returns:
            ax: matplotlib轴对象
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(12, 6))
        
        frequencies = np.array(frequencies)
        powers = np.array(powers)
        
        if self.style == 'modern':
            # 现代风格：黑底绿线
            ax.set_facecolor('black')
            line_color = '#00ff00'
            grid_color = '#333333'
        else:
            # 经典风格：白底蓝线
            ax.set_facecolor('white')
            line_color = '#3498db'
            grid_color = '#cccccc'
        
        # 绘制频谱线
        ax.plot(frequencies, powers, color=line_color, linewidth=2, label='信号强度')
        ax.fill_between(frequencies, powers, -100, alpha=0.3, color=line_color)
        
        # 标记Top N信号的SSID
        if ssids and show_legend and len(ssids) == len(powers):
            # 找出最强的N个信号
            top_indices = np.argsort(powers)[-top_n:][::-1]
            for idx in top_indices:
                ax.annotate(ssids[idx], 
                           xy=(frequencies[idx], powers[idx]),
                           xytext=(0, 10), textcoords='offset points',
                           fontsize=8, ha='center',
                           bbox=dict(boxstyle='round,pad=0.3', 
                                   facecolor='yellow', alpha=0.7),
                           arrowprops=dict(arrowstyle='->', color='red'))
        
        # 设置标签和网格
        ax.set_xlabel('频率 (MHz)', fontsize=12, 
                     color='white' if self.style == 'modern' else 'black')
        ax.set_ylabel('信号强度 (dBm)', fontsize=12,
                     color='white' if self.style == 'modern' else 'black')
        ax.set_title(title, fontsize=14, fontweight='bold',
                    color='white' if self.style == 'modern' else 'black')
        
        ax.grid(True, alpha=0.3, color=grid_color)
        ax.tick_params(colors='white' if self.style == 'modern' else 'black')
        
        # 设置Y轴范围
        ax.set_ylim(-100, 0)
        
        if show_legend:
            ax.legend(loc='upper right')
        
        return ax


class RadarVisualizer:
    """雷达图可视化器 - 统一雷达/罗盘图"""
    
    def __init__(self, sectors=12):
        """
        初始化雷达可视化器
        
        Args:
            sectors: 扇区数量 (8, 12, 16)
        """
        self.sectors = sectors
    
    def plot_radar(self, values, labels=None, ax=None,
                   title='信号强度雷达图',
                   fill=True, color='#3498db'):
        """
        绘制雷达图
        
        Args:
            values: 各方向的值 (0-100)
            labels: 各方向的标签
            ax: matplotlib轴对象 (polar投影)
            title: 图表标题
            fill: 是否填充
            color: 填充颜色
        
        Returns:
            ax: matplotlib轴对象
        """
        if ax is None:
            fig = plt.figure(figsize=(8, 8))
            ax = fig.add_subplot(111, projection='polar')
        
        values = np.array(values)
        
        # 确保数据闭合
        if len(values) != self.sectors:
            raise ValueError(f"值的数量必须为 {self.sectors}")
        
        # 角度
        angles = np.linspace(0, 2*np.pi, self.sectors, endpoint=False)
        values = np.concatenate((values, [values[0]]))  # 闭合
        angles = np.concatenate((angles, [angles[0]]))  # 闭合
        
        # 绘制雷达图
        ax.plot(angles, values, 'o-', linewidth=2, color=color, label='信号强度')
        if fill:
            ax.fill(angles, values, alpha=0.25, color=color)
        
        # 设置标签
        if labels is None:
            # 默认方向标签
            labels = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 
                     'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW',
                     'W', 'WNW', 'NW', 'NNW'][:self.sectors]
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, fontsize=10)
        
        # 设置径向范围
        ax.set_ylim(0, 100)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(['20%', '40%', '60%', '80%', '100%'])
        
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.grid(True)
        
        return ax


# 导出接口
__all__ = [
    'HeatmapVisualizer',
    'SpectrumVisualizer',
    'RadarVisualizer'
]
