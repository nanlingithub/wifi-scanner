"""
WiFi扫描缓存管理器
优化性能，避免频繁重复扫描
"""

import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class WiFiScanCache:
    """WiFi扫描结果缓存管理器"""
    
    def __init__(self, cache_duration: int = 300):
        """
        初始化缓存管理器
        
        Args:
            cache_duration: 缓存有效期（秒），默认5分钟
        """
        self.cache_duration = cache_duration
        self._cache: Dict = {}
        self._cache_time: Optional[datetime] = None
        self._hit_count = 0
        self._miss_count = 0
    
    def is_valid(self) -> bool:
        """
        检查缓存是否有效
        
        Returns:
            是否在有效期内
        """
        if self._cache_time is None:
            return False
        
        elapsed = (datetime.now() - self._cache_time).total_seconds()
        return elapsed < self.cache_duration
    
    def get(self) -> Optional[Dict]:
        """
        获取缓存数据
        
        Returns:
            缓存的扫描结果，如果无效返回None
        """
        if self.is_valid():
            self._hit_count += 1
            return self._cache.copy()
        
        self._miss_count += 1
        return None
    
    def set(self, data: Dict) -> None:
        """
        更新缓存数据
        
        Args:
            data: 扫描结果数据
        """
        self._cache = data.copy()
        self._cache_time = datetime.now()
    
    def clear(self) -> None:
        """清除缓存"""
        self._cache = {}
        self._cache_time = None
    
    def get_stats(self) -> Dict:
        """
        获取缓存统计信息
        
        Returns:
            缓存命中率等统计信息
        """
        total = self._hit_count + self._miss_count
        hit_rate = (self._hit_count / total * 100) if total > 0 else 0
        
        return {
            'hits': self._hit_count,
            'misses': self._miss_count,
            'hit_rate': f"{hit_rate:.1f}%",
            'is_valid': self.is_valid(),
            'cache_time': self._cache_time.strftime('%Y-%m-%d %H:%M:%S') if self._cache_time else 'N/A',
            'remaining_seconds': self._get_remaining_seconds()
        }
    
    def get_remaining_time(self) -> float:
        """
        获取缓存剩余有效时间（秒）
        
        Returns:
            剩余秒数
        """
        return float(self._get_remaining_seconds())
    
    def _get_remaining_seconds(self) -> int:
        """获取缓存剩余有效时间"""
        if not self.is_valid():
            return 0
        
        elapsed = (datetime.now() - self._cache_time).total_seconds()
        return max(0, int(self.cache_duration - elapsed))


class NetworkAnalysisCache:
    """网络分析结果缓存"""
    
    def __init__(self):
        self.signal_cache = WiFiScanCache(cache_duration=300)  # 信号分析缓存5分钟
        self.security_cache = WiFiScanCache(cache_duration=600)  # 安全评估缓存10分钟
    
    def get_or_compute(self, cache_type: str, compute_func: callable) -> Dict:
        """
        获取缓存数据，如果缓存无效则调用计算函数
        
        Args:
            cache_type: 缓存类型 ('signal' 或 'security')
            compute_func: 计算函数，无参数
            
        Returns:
            分析结果
        """
        if cache_type == 'signal':
            cached = self.signal_cache.get()
            if cached is not None:
                return cached
            result = compute_func()
            self.signal_cache.set(result)
            return result
        elif cache_type == 'security':
            cached = self.security_cache.get()
            if cached is not None:
                return cached
            result = compute_func()
            self.security_cache.set(result)
            return result
        else:
            # 不支持的缓存类型，直接执行计算
            return compute_func()
    
    def get_signal_analysis(self) -> Optional[Dict]:
        """获取信号分析缓存"""
        return self.signal_cache.get()
    
    def set_signal_analysis(self, data: Dict) -> None:
        """设置信号分析缓存"""
        self.signal_cache.set(data)
    
    def get_security_assessment(self) -> Optional[Dict]:
        """获取安全评估缓存"""
        return self.security_cache.get()
    
    def set_security_assessment(self, data: Dict) -> None:
        """设置安全评估缓存"""
        self.security_cache.set(data)
    
    def clear_all(self) -> None:
        """清除所有缓存"""
        self.signal_cache.clear()
        self.security_cache.clear()
    
    def get_statistics(self) -> Dict:
        """获取所有缓存统计"""
        signal_stats = self.signal_cache.get_stats()
        security_stats = self.security_cache.get_stats()
        
        total_hits = signal_stats['hits'] + security_stats['hits']
        total_misses = signal_stats['misses'] + security_stats['misses']
        total = total_hits + total_misses
        
        return {
            'signal': signal_stats,
            'security': security_stats,
            'overall': {
                'total': total,
                'hits': total_hits,
                'misses': total_misses,
                'hit_rate': f"{(total_hits / total * 100) if total > 0 else 0:.1f}%"
            }
        }
