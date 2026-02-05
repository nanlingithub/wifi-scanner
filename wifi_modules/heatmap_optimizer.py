"""
热力图性能优化模块
实现多线程插值、缓存机制和渐进式渲染
"""

import numpy as np
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from scipy.interpolate import Rbf
try:
    from pykrige.ok import OrdinaryKriging
    KRIGING_AVAILABLE = True
except ImportError:
    KRIGING_AVAILABLE = False


class HeatmapOptimizer:
    """热力图性能优化器
    
    功能:
    - 多线程并行插值计算
    - 网格分块处理
    - 结果缓存
    - 渐进式渲染支持
    """
    
    def __init__(self, max_workers=4, chunk_size=50):
        """初始化优化器
        
        Args:
            max_workers: 最大线程数
            chunk_size: 每块网格大小
        """
        self.max_workers = max_workers
        self.chunk_size = chunk_size
        self.cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
    
    def get_cache_key(self, x, y, signal, resolution, method):
        """生成缓存键
        
        Args:
            x, y, signal: 数据点
            resolution: 网格分辨率
            method: 插值方法
        
        Returns:
            缓存键字符串
        """
        # 使用数据点哈希 + 参数组合
        data_hash = hash((
            tuple(x),
            tuple(y),
            tuple(signal),
            resolution,
            method
        ))
        return str(data_hash)
    
    def get_from_cache(self, cache_key):
        """从缓存获取结果
        
        Args:
            cache_key: 缓存键
        
        Returns:
            缓存的结果或None
        """
        if cache_key in self.cache:
            self.cache_hits += 1
            return self.cache[cache_key]
        
        self.cache_misses += 1
        return None
    
    def add_to_cache(self, cache_key, result):
        """添加到缓存
        
        Args:
            cache_key: 缓存键
            result: 计算结果
        """
        # 限制缓存大小（最多保留20个结果）
        if len(self.cache) >= 20:
            # 删除最旧的缓存项
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        self.cache[cache_key] = result
    
    def parallel_interpolation(
        self, 
        x, 
        y, 
        signal, 
        xi, 
        yi, 
        method='rbf',
        smooth=0.0,
        progress_callback=None
    ):
        """多线程并行插值计算
        
        Args:
            x, y: 测量点坐标数组
            signal: 信号强度数组
            xi, yi: 网格坐标数组
            method: 插值方法 ('rbf', 'kriging', 'idw')
            smooth: 平滑参数
            progress_callback: 进度回调函数 (completed, total)
        
        Returns:
            插值后的网格数据
        """
        # 检查缓存
        cache_key = self.get_cache_key(
            x, y, signal, 
            xi.shape[0], 
            method
        )
        
        cached_result = self.get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result
        
        # 网格分块
        rows, cols = xi.shape
        chunks = self._split_grid(rows, cols, self.chunk_size)
        
        # 根据方法选择插值函数
        if method == 'kriging' and KRIGING_AVAILABLE:
            interpolator = self._create_kriging_interpolator(x, y, signal)
        elif method == 'rbf':
            interpolator = self._create_rbf_interpolator(x, y, signal, smooth)
        else:  # idw
            interpolator = lambda xi_chunk, yi_chunk: self._interpolate_idw_chunk(
                x, y, signal, xi_chunk, yi_chunk
            )
        
        # 多线程处理
        zi = np.zeros_like(xi)
        total_chunks = len(chunks)
        completed = 0
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_chunk = {}
            for chunk_idx, (row_start, row_end, col_start, col_end) in enumerate(chunks):
                xi_chunk = xi[row_start:row_end, col_start:col_end]
                yi_chunk = yi[row_start:row_end, col_start:col_end]
                
                future = executor.submit(
                    self._process_chunk,
                    interpolator,
                    xi_chunk,
                    yi_chunk,
                    method
                )
                future_to_chunk[future] = (chunk_idx, row_start, row_end, col_start, col_end)
            
            # 收集结果
            for future in as_completed(future_to_chunk):
                chunk_info = future_to_chunk[future]
                chunk_idx, row_start, row_end, col_start, col_end = chunk_info
                
                try:
                    zi_chunk = future.result()
                    zi[row_start:row_end, col_start:col_end] = zi_chunk
                    
                    # 更新进度
                    completed += 1
                    if progress_callback:
                        progress_callback(completed, total_chunks)
                
                except Exception as e:
                    print(f"块 {chunk_idx} 处理失败: {e}")
                    # 使用默认值填充
                    zi[row_start:row_end, col_start:col_end] = 0
        
        # 钳制到[0, 100]范围
        zi = np.clip(zi, 0, 100)
        
        # 添加到缓存
        self.add_to_cache(cache_key, zi)
        
        return zi
    
    def _split_grid(self, rows, cols, chunk_size):
        """将网格分块
        
        Args:
            rows, cols: 网格尺寸
            chunk_size: 块大小
        
        Returns:
            分块列表 [(row_start, row_end, col_start, col_end), ...]
        """
        chunks = []
        
        for row_start in range(0, rows, chunk_size):
            row_end = min(row_start + chunk_size, rows)
            
            for col_start in range(0, cols, chunk_size):
                col_end = min(col_start + chunk_size, cols)
                
                chunks.append((row_start, row_end, col_start, col_end))
        
        return chunks
    
    def _create_rbf_interpolator(self, x, y, signal, smooth):
        """创建RBF插值器
        
        Args:
            x, y, signal: 数据点
            smooth: 平滑参数
        
        Returns:
            RBF插值函数
        """
        rbf = Rbf(x, y, signal, function='multiquadric', smooth=smooth)
        return lambda xi_chunk, yi_chunk: rbf(xi_chunk, yi_chunk)
    
    def _create_kriging_interpolator(self, x, y, signal):
        """创建Kriging插值器
        
        Args:
            x, y, signal: 数据点
        
        Returns:
            Kriging插值函数
        """
        try:
            OK = OrdinaryKriging(x, y, signal, variogram_model='exponential')
            
            def kriging_func(xi_chunk, yi_chunk):
                # 展平网格
                xi_flat = xi_chunk.ravel()
                yi_flat = yi_chunk.ravel()
                
                # Kriging插值
                zi_flat, _ = OK.execute('points', xi_flat, yi_flat)
                
                # 重塑为原始形状
                return zi_flat.reshape(xi_chunk.shape)
            
            return kriging_func
        
        except Exception as e:
            print(f"Kriging初始化失败，回退到RBF: {e}")
            return self._create_rbf_interpolator(x, y, signal, 0.0)
    
    def _interpolate_idw_chunk(self, x, y, signal, xi_chunk, yi_chunk, power=2):
        """反距离加权插值（块处理）
        
        Args:
            x, y, signal: 原始数据点
            xi_chunk, yi_chunk: 目标网格块
            power: 距离权重指数
        
        Returns:
            插值后的网格块
        """
        zi_chunk = np.zeros_like(xi_chunk)
        
        for i in range(xi_chunk.shape[0]):
            for j in range(xi_chunk.shape[1]):
                distances = np.sqrt(
                    (x - xi_chunk[i,j])**2 + 
                    (y - yi_chunk[i,j])**2
                )
                
                # 避免除零
                distances[distances < 1e-10] = 1e-10
                
                weights = 1.0 / (distances ** power)
                zi_chunk[i,j] = np.sum(weights * signal) / np.sum(weights)
        
        return zi_chunk
    
    def _process_chunk(self, interpolator, xi_chunk, yi_chunk, method):
        """处理单个网格块
        
        Args:
            interpolator: 插值函数
            xi_chunk, yi_chunk: 网格块坐标
            method: 插值方法
        
        Returns:
            插值后的网格块
        """
        return interpolator(xi_chunk, yi_chunk)
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0
    
    def get_cache_stats(self):
        """获取缓存统计
        
        Returns:
            字典包含hits, misses, hit_rate
        """
        total = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total if total > 0 else 0
        
        return {
            'hits': self.cache_hits,
            'misses': self.cache_misses,
            'hit_rate': hit_rate,
            'cache_size': len(self.cache)
        }


class AdaptiveGridCalculator:
    """自适应网格分辨率计算器
    
    根据数据点数量和分布自动确定最佳网格分辨率
    """
    
    @staticmethod
    def calculate_resolution(num_points, x_range, y_range, target_density=5):
        """计算自适应网格分辨率
        
        Args:
            num_points: 数据点数量
            x_range: X轴范围
            y_range: Y轴范围
            target_density: 目标点密度（每单位面积的点数）
        
        Returns:
            网格分辨率（行数、列数）
        """
        # 计算面积
        area = x_range * y_range
        
        # 基于数据点密度计算分辨率
        if num_points < 10:
            base_resolution = 30
        elif num_points < 50:
            base_resolution = 50
        elif num_points < 100:
            base_resolution = 80
        else:
            base_resolution = min(150, int(np.sqrt(num_points) * 10))
        
        # 考虑长宽比
        aspect_ratio = x_range / y_range if y_range > 0 else 1
        
        if aspect_ratio > 1.5:
            # 横向布局
            x_resolution = base_resolution
            y_resolution = int(base_resolution / aspect_ratio)
        elif aspect_ratio < 0.67:
            # 纵向布局
            y_resolution = base_resolution
            x_resolution = int(base_resolution * aspect_ratio)
        else:
            # 近似正方形
            x_resolution = y_resolution = base_resolution
        
        return max(20, x_resolution), max(20, y_resolution)
    
    @staticmethod
    def calculate_adaptive_smooth(signal_values):
        """计算自适应平滑参数
        
        Args:
            signal_values: 信号强度数组
        
        Returns:
            平滑参数
        """
        # 处理空数组
        if len(signal_values) == 0:
            return 0.0
        
        # 计算信号方差
        signal_std = np.std(signal_values)
        
        # 处理NaN情况
        if np.isnan(signal_std):
            return 0.0
        
        # 方差大时使用更大的平滑参数
        if signal_std < 5:
            return 0.0  # 信号稳定，不需要平滑
        elif signal_std < 10:
            return 0.1
        elif signal_std < 20:
            return 0.3
        else:
            return 0.5  # 信号波动大，增加平滑
