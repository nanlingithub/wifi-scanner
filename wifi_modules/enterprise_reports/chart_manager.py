"""
图表资源管理器 v2.0
解决matplotlib内存泄漏问题
"""

import io
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from typing import List, Optional
from reportlab.lib.utils import ImageReader


class ChartManager:
    """✅ 图表资源管理器"""
    
    def __init__(self):
        """初始化图表管理器"""
        self.charts: List[Figure] = []  # 追踪所有图表
        self.buffers: List[io.BytesIO] = []  # 追踪所有缓冲区
    
    def create_pie_chart(self, labels: List[str], sizes: List[float], 
                         title: str, colors: Optional[List[str]] = None) -> ImageReader:
        """
        创建饼图（自动管理资源）
        
        Args:
            labels: 标签列表
            sizes: 数值列表
            title: 图表标题
            colors: 颜色列表（可选）
            
        Returns:
            ImageReader: ReportLab图片对象
        """
        fig, ax = plt.subplots(figsize=(6, 4))
        self.charts.append(fig)  # ✅ 追踪图表
        
        # 绘制饼图
        wedges, texts, autotexts = ax.pie(
            sizes, 
            labels=labels, 
            autopct='%1.1f%%',
            colors=colors,
            startangle=90
        )
        
        # 设置标题
        ax.set_title(title, fontsize=12, fontweight='bold', pad=20)
        
        # 美化文本
        for text in texts:
            text.set_fontsize(9)
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(8)
        
        # 保存到内存
        img_buffer = io.BytesIO()
        self.buffers.append(img_buffer)  # ✅ 追踪缓冲区
        
        fig.savefig(img_buffer, format='PNG', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        
        return ImageReader(img_buffer)
    
    def create_bar_chart(self, categories: List[str], values: List[float],
                         title: str, xlabel: str = '', ylabel: str = '',
                         color: str = '#3498db') -> ImageReader:
        """
        创建柱状图
        
        Args:
            categories: 类别列表
            values: 数值列表
            title: 图表标题
            xlabel: X轴标签
            ylabel: Y轴标签
            color: 柱状颜色
            
        Returns:
            ImageReader: ReportLab图片对象
        """
        fig, ax = plt.subplots(figsize=(8, 4))
        self.charts.append(fig)
        
        # 绘制柱状图
        bars = ax.bar(categories, values, color=color, alpha=0.7)
        
        # 设置标题和标签
        ax.set_title(title, fontsize=12, fontweight='bold', pad=15)
        ax.set_xlabel(xlabel, fontsize=10)
        ax.set_ylabel(ylabel, fontsize=10)
        
        # 在柱子上显示数值
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}',
                   ha='center', va='bottom', fontsize=8)
        
        # 网格线
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)
        
        # 旋转X轴标签（如果类别名称较长）
        plt.xticks(rotation=45, ha='right')
        
        # 保存到内存
        img_buffer = io.BytesIO()
        self.buffers.append(img_buffer)
        
        fig.savefig(img_buffer, format='PNG', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        
        return ImageReader(img_buffer)
    
    def create_line_chart(self, x_data: List, y_data: List[List[float]],
                          labels: List[str], title: str,
                          xlabel: str = '', ylabel: str = '') -> ImageReader:
        """
        创建折线图
        
        Args:
            x_data: X轴数据
            y_data: Y轴数据列表（支持多条线）
            labels: 线条标签
            title: 图表标题
            xlabel: X轴标签
            ylabel: Y轴标签
            
        Returns:
            ImageReader: ReportLab图片对象
        """
        fig, ax = plt.subplots(figsize=(8, 4))
        self.charts.append(fig)
        
        # 绘制多条折线
        colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6']
        for idx, (y, label) in enumerate(zip(y_data, labels)):
            ax.plot(x_data, y, marker='o', label=label, 
                   color=colors[idx % len(colors)], linewidth=2)
        
        # 设置标题和标签
        ax.set_title(title, fontsize=12, fontweight='bold', pad=15)
        ax.set_xlabel(xlabel, fontsize=10)
        ax.set_ylabel(ylabel, fontsize=10)
        
        # 图例
        ax.legend(loc='best', fontsize=9)
        
        # 网格线
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # 保存到内存
        img_buffer = io.BytesIO()
        self.buffers.append(img_buffer)
        
        fig.savefig(img_buffer, format='PNG', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        
        return ImageReader(img_buffer)
    
    def cleanup(self):
        """✅ 清理所有图表和缓冲区"""
        # 关闭所有图表
        for fig in self.charts:
            plt.close(fig)
        self.charts.clear()
        
        # 关闭所有缓冲区
        for buffer in self.buffers:
            buffer.close()
        self.buffers.clear()
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出：自动清理"""
        self.cleanup()
        return False
    
    def __del__(self):
        """析构函数：确保资源释放"""
        self.cleanup()


# 使用示例
if __name__ == '__main__':
    # 方式1: 使用with语句（推荐）
    with ChartManager() as cm:
        pie_img = cm.create_pie_chart(
            labels=['优秀', '良好', '一般', '差'],
            sizes=[30, 40, 20, 10],
            title='信号质量分布'
        )
        # 图表会在退出with块时自动清理
    
    # 方式2: 手动清理
    cm = ChartManager()
    try:
        bar_img = cm.create_bar_chart(
            categories=['2.4G', '5G'],
            values=[25, 63],
            title='频段使用统计',
            ylabel='网络数量'
        )
    finally:
        cm.cleanup()  # 确保清理
    
    print("✓ 图表管理器测试完成")
