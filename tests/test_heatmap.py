"""
Heatmap热力图模块单元测试
测试覆盖: 插值算法, 性能优化, 网格计算
"""

import pytest
import sys
import os
import numpy as np
from unittest.mock import Mock, patch

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wifi_modules.heatmap_optimizer import (
    HeatmapOptimizer,
    AdaptiveGridCalculator
)


class TestHeatmapOptimizer:
    """HeatmapOptimizer性能优化器测试"""
    
    @pytest.fixture
    def optimizer(self):
        """创建优化器实例"""
        return HeatmapOptimizer(max_workers=4, chunk_size=50)
    
    @pytest.fixture
    def sample_data(self):
        """创建测试数据"""
        np.random.seed(42)
        x = np.random.uniform(0, 10, 20)
        y = np.random.uniform(0, 10, 20)
        signal = np.random.uniform(0, 100, 20)
        return x, y, signal
    
    # === 缓存功能测试 ===
    
    def test_cache_key_generation(self, optimizer, sample_data):
        """测试缓存键生成"""
        x, y, signal = sample_data
        key1 = optimizer.get_cache_key(x, y, signal, 50, 'rbf')
        key2 = optimizer.get_cache_key(x, y, signal, 50, 'rbf')
        
        # 相同数据应生成相同键
        assert key1 == key2
    
    def test_cache_key_different_data(self, optimizer, sample_data):
        """测试不同数据生成不同缓存键"""
        x, y, signal = sample_data
        key1 = optimizer.get_cache_key(x, y, signal, 50, 'rbf')
        key2 = optimizer.get_cache_key(x, y, signal, 100, 'rbf')
        
        # 不同分辨率应生成不同键
        assert key1 != key2
    
    def test_cache_add_and_get(self, optimizer, sample_data):
        """测试缓存添加和获取"""
        x, y, signal = sample_data
        cache_key = optimizer.get_cache_key(x, y, signal, 50, 'rbf')
        
        # 添加到缓存
        test_result = np.array([[1, 2], [3, 4]])
        optimizer.add_to_cache(cache_key, test_result)
        
        # 从缓存获取
        cached = optimizer.get_from_cache(cache_key)
        assert cached is not None
        np.testing.assert_array_equal(cached, test_result)
    
    def test_cache_size_limit(self, optimizer):
        """测试缓存大小限制（最多20个）"""
        # 添加25个缓存项
        for i in range(25):
            key = f"key_{i}"
            value = np.array([[i]])
            optimizer.add_to_cache(key, value)
        
        # 缓存大小应限制在20
        assert len(optimizer.cache) == 20
    
    def test_cache_stats(self, optimizer, sample_data):
        """测试缓存统计"""
        x, y, signal = sample_data
        cache_key = optimizer.get_cache_key(x, y, signal, 50, 'rbf')
        
        # 初始状态
        stats = optimizer.get_cache_stats()
        assert stats['hits'] == 0
        assert stats['misses'] == 0
        
        # 缓存未命中
        result = optimizer.get_from_cache(cache_key)
        assert result is None
        stats = optimizer.get_cache_stats()
        assert stats['misses'] == 1
        
        # 添加到缓存
        optimizer.add_to_cache(cache_key, np.array([[1]]))
        
        # 缓存命中
        result = optimizer.get_from_cache(cache_key)
        assert result is not None
        stats = optimizer.get_cache_stats()
        assert stats['hits'] == 1
        assert stats['hit_rate'] == 0.5  # 1命中 / (1命中 + 1未命中)
    
    def test_clear_cache(self, optimizer):
        """测试清空缓存"""
        optimizer.add_to_cache('key1', np.array([[1]]))
        optimizer.add_to_cache('key2', np.array([[2]]))
        
        assert len(optimizer.cache) == 2
        
        optimizer.clear_cache()
        
        assert len(optimizer.cache) == 0
        stats = optimizer.get_cache_stats()
        assert stats['hits'] == 0
        assert stats['misses'] == 0
    
    # === 网格分块测试 ===
    
    def test_split_grid_basic(self, optimizer):
        """测试网格分块基本功能"""
        chunks = optimizer._split_grid(100, 100, 50)
        
        # 应该分成4块 (2x2)
        assert len(chunks) == 4
        
        # 验证块的范围
        assert chunks[0] == (0, 50, 0, 50)
        assert chunks[1] == (0, 50, 50, 100)
        assert chunks[2] == (50, 100, 0, 50)
        assert chunks[3] == (50, 100, 50, 100)
    
    def test_split_grid_non_divisible(self, optimizer):
        """测试非整除网格分块"""
        chunks = optimizer._split_grid(120, 80, 50)
        
        # 验证所有块覆盖完整网格
        assert len(chunks) == 6  # 3行 x 2列
    
    def test_split_grid_small(self, optimizer):
        """测试小于块大小的网格"""
        chunks = optimizer._split_grid(30, 30, 50)
        
        # 应该只有1块
        assert len(chunks) == 1
        assert chunks[0] == (0, 30, 0, 30)
    
    # === IDW插值测试 ===
    
    def test_idw_interpolation_basic(self, optimizer):
        """测试IDW插值基本功能"""
        # 简单测试数据：4个点
        x = np.array([0, 1, 0, 1])
        y = np.array([0, 0, 1, 1])
        signal = np.array([100, 80, 60, 40])
        
        # 创建小网格（单个点）
        xi = np.array([[0.5]])
        yi = np.array([[0.5]])
        
        zi = optimizer._interpolate_idw_chunk(x, y, signal, xi, yi, power=2)
        
        # 中心点应该是4个点的加权平均
        assert zi.shape == (1, 1)
        assert 40 <= zi[0, 0] <= 100
    
    def test_idw_exact_point(self, optimizer):
        """测试IDW在数据点处的值"""
        x = np.array([0, 1, 2])
        y = np.array([0, 0, 0])
        signal = np.array([100, 50, 0])
        
        # 在第一个数据点处插值
        xi = np.array([[0]])
        yi = np.array([[0]])
        
        zi = optimizer._interpolate_idw_chunk(x, y, signal, xi, yi)
        
        # 应该等于该点的值
        np.testing.assert_almost_equal(zi[0, 0], 100, decimal=0)
    
    def test_idw_power_effect(self, optimizer):
        """测试IDW权重指数的影响"""
        x = np.array([0, 2])
        y = np.array([0, 0])
        signal = np.array([100, 0])
        
        xi = np.array([[1]])
        yi = np.array([[0]])
        
        # power=1（线性）- 中点距离相等，应为平均值50
        zi1 = optimizer._interpolate_idw_chunk(x, y, signal, xi, yi, power=1)
        
        # power=2（平方）- 中点距离相等，应为平均值50
        zi2 = optimizer._interpolate_idw_chunk(x, y, signal, xi, yi, power=2)
        
        # 在中点位置，不同power值结果应该相同（距离相等）
        # 改为测试不同位置
        xi_off = np.array([[0.5]])
        yi_off = np.array([[0]])
        
        zi1_off = optimizer._interpolate_idw_chunk(x, y, signal, xi_off, yi_off, power=1)
        zi2_off = optimizer._interpolate_idw_chunk(x, y, signal, xi_off, yi_off, power=2)
        
        # 离(0,0)更近时，power越大权重越偏向近点
        assert zi1_off[0, 0] != zi2_off[0, 0]
        assert zi2_off[0, 0] > zi1_off[0, 0]  # power=2应该更接近100


class TestAdaptiveGridCalculator:
    """自适应网格分辨率计算器测试"""
    
    # === 分辨率计算测试 ===
    
    def test_resolution_small_dataset(self):
        """测试小数据集的分辨率"""
        x_res, y_res = AdaptiveGridCalculator.calculate_resolution(
            num_points=5,
            x_range=10,
            y_range=10
        )
        
        # 小于10个点应该使用30x30
        assert x_res == 30
        assert y_res == 30
    
    def test_resolution_medium_dataset(self):
        """测试中等数据集的分辨率"""
        x_res, y_res = AdaptiveGridCalculator.calculate_resolution(
            num_points=30,
            x_range=10,
            y_range=10
        )
        
        # 10-50个点应该使用50x50
        assert x_res == 50
        assert y_res == 50
    
    def test_resolution_large_dataset(self):
        """测试大数据集的分辨率"""
        x_res, y_res = AdaptiveGridCalculator.calculate_resolution(
            num_points=80,
            x_range=10,
            y_range=10
        )
        
        # 50-100个点应该使用80x80
        assert x_res == 80
        assert y_res == 80
    
    def test_resolution_very_large_dataset(self):
        """测试超大数据集的分辨率"""
        x_res, y_res = AdaptiveGridCalculator.calculate_resolution(
            num_points=500,
            x_range=10,
            y_range=10
        )
        
        # 超过100个点，最大150x150
        assert x_res <= 150
        assert y_res <= 150
    
    def test_resolution_aspect_ratio_wide(self):
        """测试宽屏长宽比"""
        x_res, y_res = AdaptiveGridCalculator.calculate_resolution(
            num_points=50,
            x_range=20,  # 宽
            y_range=10   # 窄
        )
        
        # x方向分辨率应该更高
        assert x_res > y_res
    
    def test_resolution_aspect_ratio_tall(self):
        """测试竖屏长宽比"""
        x_res, y_res = AdaptiveGridCalculator.calculate_resolution(
            num_points=50,
            x_range=10,  # 窄
            y_range=20   # 宽
        )
        
        # y方向分辨率应该更高
        assert y_res > x_res
    
    def test_resolution_minimum_value(self):
        """测试分辨率最小值限制"""
        x_res, y_res = AdaptiveGridCalculator.calculate_resolution(
            num_points=1,
            x_range=100,
            y_range=1
        )
        
        # 即使长宽比极端，也应该>=20
        assert x_res >= 20
        assert y_res >= 20
    
    # === 平滑参数计算测试 ===
    
    def test_adaptive_smooth_stable_signal(self):
        """测试稳定信号的平滑参数"""
        signal = np.array([50, 51, 49, 50, 52])  # 标准差<5
        smooth = AdaptiveGridCalculator.calculate_adaptive_smooth(signal)
        
        # 稳定信号不需要平滑
        assert smooth == 0.0
    
    def test_adaptive_smooth_low_variance(self):
        """测试低方差信号"""
        signal = np.array([50, 55, 45, 52, 48])  # 标准差约3-4
        smooth = AdaptiveGridCalculator.calculate_adaptive_smooth(signal)
        
        # 低方差（std≈3.7 < 5）不需要平滑
        assert smooth == 0.0
    
    def test_adaptive_smooth_medium_variance(self):
        """测试中等方差信号"""
        signal = np.array([50, 65, 35, 60, 40])  # 标准差约12
        smooth = AdaptiveGridCalculator.calculate_adaptive_smooth(signal)
        
        # 中等方差使用中等平滑
        assert smooth == 0.3
    
    def test_adaptive_smooth_high_variance(self):
        """测试高方差信号"""
        signal = np.array([0, 100, 20, 80, 10])  # 标准差约40
        smooth = AdaptiveGridCalculator.calculate_adaptive_smooth(signal)
        
        # 高方差使用大平滑参数
        assert smooth == 0.5
    
    def test_adaptive_smooth_empty_array(self):
        """测试空数组"""
        import warnings
        
        signal = np.array([])
        
        # 忽略numpy的警告
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            smooth = AdaptiveGridCalculator.calculate_adaptive_smooth(signal)
        
        # 空数组应该返回0
        assert smooth == 0.0


class TestHeatmapIntegration:
    """热力图集成测试"""
    
    @pytest.fixture
    def optimizer(self):
        return HeatmapOptimizer(max_workers=2, chunk_size=25)
    
    def test_parallel_interpolation_rbf(self, optimizer):
        """测试RBF并行插值"""
        # 创建测试数据
        np.random.seed(42)
        x = np.random.uniform(0, 10, 15)
        y = np.random.uniform(0, 10, 15)
        signal = np.random.uniform(30, 90, 15)
        
        # 创建网格
        xi = np.linspace(0, 10, 40)
        yi = np.linspace(0, 10, 40)
        xi, yi = np.meshgrid(xi, yi)
        
        # 执行插值
        zi = optimizer.parallel_interpolation(
            x, y, signal, xi, yi,
            method='rbf',
            smooth=0.1
        )
        
        # 验证结果
        assert zi.shape == xi.shape
        assert np.all(zi >= 0)
        assert np.all(zi <= 100)
    
    def test_parallel_interpolation_idw(self, optimizer):
        """测试IDW并行插值"""
        x = np.array([0, 10, 0, 10])
        y = np.array([0, 0, 10, 10])
        signal = np.array([100, 80, 60, 40])
        
        xi = np.linspace(0, 10, 30)
        yi = np.linspace(0, 10, 30)
        xi, yi = np.meshgrid(xi, yi)
        
        zi = optimizer.parallel_interpolation(
            x, y, signal, xi, yi,
            method='idw'
        )
        
        assert zi.shape == xi.shape
        assert 40 <= np.min(zi) <= 100
        assert 40 <= np.max(zi) <= 100
    
    def test_parallel_interpolation_caching(self, optimizer):
        """测试插值结果缓存"""
        x = np.array([0, 5, 10])
        y = np.array([0, 5, 10])
        signal = np.array([100, 50, 0])
        
        xi = np.linspace(0, 10, 20)
        yi = np.linspace(0, 10, 20)
        xi, yi = np.meshgrid(xi, yi)
        
        # 第一次计算
        zi1 = optimizer.parallel_interpolation(x, y, signal, xi, yi, method='rbf')
        stats1 = optimizer.get_cache_stats()
        
        # 第二次计算（应该从缓存获取）
        zi2 = optimizer.parallel_interpolation(x, y, signal, xi, yi, method='rbf')
        stats2 = optimizer.get_cache_stats()
        
        # 结果应该相同
        np.testing.assert_array_equal(zi1, zi2)
        
        # 缓存命中应该增加
        assert stats2['hits'] > stats1['hits']
    
    @pytest.mark.performance
    def test_performance_large_dataset(self, optimizer):
        """测试大数据集性能"""
        # 100个数据点
        np.random.seed(42)
        x = np.random.uniform(0, 100, 100)
        y = np.random.uniform(0, 100, 100)
        signal = np.random.uniform(0, 100, 100)
        
        # 100x100网格
        xi = np.linspace(0, 100, 100)
        yi = np.linspace(0, 100, 100)
        xi, yi = np.meshgrid(xi, yi)
        
        import time
        start = time.time()
        
        zi = optimizer.parallel_interpolation(
            x, y, signal, xi, yi,
            method='idw'
        )
        
        elapsed = time.time() - start
        
        # 应该在5秒内完成
        assert elapsed < 5.0
        assert zi.shape == (100, 100)


# 运行示例
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
