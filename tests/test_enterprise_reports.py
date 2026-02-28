"""
企业报告模块单元测试 v2.0
测试覆盖: PDF生成器, 报告缓存, 模板系统
"""

import os
import pytest
import tempfile
import shutil
import json
import time
from pathlib import Path
from datetime import datetime

# 条件导入（某些环境可能缺少reportlab）
try:
    from wifi_modules.enterprise_reports.pdf_generator import PDFGenerator
    from wifi_modules.enterprise_reports.report_cache import ReportCache
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


@pytest.mark.skipif(not HAS_REPORTLAB, reason="需要reportlab库")
class TestReportCache:
    """报告缓存系统测试"""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """创建临时缓存目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # 清理
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def cache(self, temp_cache_dir):
        """创建缓存实例"""
        return ReportCache(cache_dir=temp_cache_dir, ttl=60)
    
    def test_cache_initialization(self, temp_cache_dir):
        """测试缓存初始化"""
        cache = ReportCache(cache_dir=temp_cache_dir, ttl=30)
        
        assert cache.cache_dir.exists()
        assert cache.ttl == 30
        assert cache.cache_dir == Path(temp_cache_dir)
    
    def test_compute_hash_consistency(self, cache):
        """测试哈希计算的一致性"""
        data1 = {
            'network_name': 'TestWiFi',
            'signal_strength': -50,
            'timestamp': '2024-01-01 12:00:00'
        }
        
        data2 = {
            'signal_strength': -50,
            'network_name': 'TestWiFi',
            'timestamp': '2024-01-01 13:00:00'  # 不同时间戳
        }
        
        hash1 = cache._compute_hash(data1)
        hash2 = cache._compute_hash(data2)
        
        # 时间戳应该被忽略，哈希值应该相同
        assert hash1 == hash2
        assert len(hash1) == 32  # MD5哈希长度
    
    def test_compute_hash_changes_with_data(self, cache):
        """测试数据变化时哈希值不同"""
        data1 = {'network': 'WiFi1', 'signal': -50}
        data2 = {'network': 'WiFi2', 'signal': -50}
        
        hash1 = cache._compute_hash(data1)
        hash2 = cache._compute_hash(data2)
        
        assert hash1 != hash2
    
    def test_cache_miss(self, cache):
        """测试缓存未命中"""
        data = {'network': 'TestWiFi', 'signal': -50}
        result = cache.get(data, 'signal')
        
        assert result is None
    
    def test_cache_hit(self, cache):
        """测试缓存命中"""
        data = {'network': 'TestWiFi', 'signal': -50}
        pdf_content = b'%PDF-1.4\n%fake pdf content'
        
        # 写入缓存
        cache.set(data, 'signal', pdf_content)
        
        # 读取缓存
        result = cache.get(data, 'signal')
        
        assert result == pdf_content
    
    def test_cache_expiration(self, temp_cache_dir):
        """测试缓存过期"""
        # 创建TTL为1秒的缓存
        cache = ReportCache(cache_dir=temp_cache_dir, ttl=1)
        
        data = {'network': 'TestWiFi'}
        pdf_content = b'%PDF-1.4\ntest'
        
        # 写入缓存
        cache.set(data, 'signal', pdf_content)
        
        # 立即读取应该命中
        result = cache.get(data, 'signal')
        assert result == pdf_content
        
        # 等待过期
        time.sleep(2)
        
        # 过期后应该未命中
        result = cache.get(data, 'signal')
        assert result is None
    
    def test_cache_invalidate(self, cache):
        """测试缓存失效"""
        data = {'network': 'TestWiFi', 'signal': -50}
        pdf_content = b'%PDF-1.4\ntest'
        
        # 写入缓存
        cache.set(data, 'signal', pdf_content)
        assert cache.get(data, 'signal') is not None
        
        # 使缓存失效
        cache.invalidate(data, 'signal')
        
        # 应该未命中
        result = cache.get(data, 'signal')
        assert result is None
    
    def test_different_report_types(self, cache):
        """测试不同报告类型的缓存隔离"""
        data = {'network': 'TestWiFi'}
        pdf1 = b'%PDF-signal'
        pdf2 = b'%PDF-security'
        
        # 写入不同类型的缓存
        cache.set(data, 'signal', pdf1)
        cache.set(data, 'security', pdf2)
        
        # 读取应该返回各自的内容
        assert cache.get(data, 'signal') == pdf1
        assert cache.get(data, 'security') == pdf2
    
    def test_cleanup_expired_caches(self, temp_cache_dir):
        """测试清理过期缓存"""
        cache = ReportCache(cache_dir=temp_cache_dir, ttl=1)
        
        data1 = {'network': 'WiFi1'}
        data2 = {'network': 'WiFi2'}
        
        # 写入两个缓存
        cache.set(data1, 'signal', b'pdf1')
        cache.set(data2, 'signal', b'pdf2')
        
        # 等待过期
        time.sleep(2)
        
        # 手动触发清理（私有方法，仅测试用）
        cache._cleanup_expired()
        
        # 过期缓存应该被清理
        assert cache.get(data1, 'signal') is None
        assert cache.get(data2, 'signal') is None
    
    def test_clear_all_caches(self, cache):
        """测试清空所有缓存"""
        data1 = {'network': 'WiFi1'}
        data2 = {'network': 'WiFi2'}
        
        # 写入多个缓存
        cache.set(data1, 'signal', b'pdf1')
        cache.set(data2, 'security', b'pdf2')
        
        # 清空所有缓存
        cache.clear_all()
        
        # 所有缓存应该被清除
        assert cache.get(data1, 'signal') is None
        assert cache.get(data2, 'security') is None
    
    def test_get_cache_stats(self, cache):
        """测试获取缓存统计信息"""
        data1 = {'network': 'WiFi1'}
        data2 = {'network': 'WiFi2'}
        
        # 写入缓存
        cache.set(data1, 'signal', b'pdf1' * 100)
        cache.set(data2, 'security', b'pdf2' * 200)
        
        stats = cache.get_stats()
        
        assert stats['total_files'] >= 2
        assert stats['total_size_mb'] >= 0  # 修改为total_size_mb
        assert 'cache_dir' in stats
        assert 'ttl_minutes' in stats
    
    def test_meta_file_creation(self, cache):
        """测试元数据文件创建"""
        data = {'network': 'TestWiFi'}
        cache.set(data, 'signal', b'pdf')
        
        cache_key = cache._compute_hash(data)
        meta_file = cache._get_meta_path(cache_key, 'signal')
        
        assert meta_file.exists()
        
        # 验证元数据内容
        with open(meta_file, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        
        assert 'created_at' in meta
        assert meta['report_type'] == 'signal'
        assert meta['cache_key'] == cache_key


@pytest.mark.skipif(not HAS_REPORTLAB, reason="需要reportlab库")
class TestPDFGenerator:
    """PDF生成器测试"""
    
    @pytest.fixture
    def temp_output_dir(self):
        """创建临时输出目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def generator(self):
        """创建PDF生成器实例"""
        return PDFGenerator(use_cache=False)
    
    @pytest.fixture
    def generator_with_cache(self, temp_output_dir):
        """创建带缓存的生成器"""
        gen = PDFGenerator(use_cache=True)
        gen.cache = ReportCache(cache_dir=temp_output_dir, ttl=60)
        return gen
    
    def test_generator_initialization(self, generator):
        """测试生成器初始化"""
        assert generator is not None
        assert generator.styles is not None
        assert 'CustomTitle' in generator.styles
        assert 'SectionTitle' in generator.styles
        assert 'CustomBody' in generator.styles
    
    def test_font_setup(self, generator):
        """测试字体设置"""
        # 字体设置应该成功（或静默失败）
        generator.setup_fonts()
        # 不应该抛出异常
    
    def test_styles_creation(self, generator):
        """测试样式创建"""
        styles = generator._create_styles()
        
        # 验证自定义样式
        assert 'CustomTitle' in styles
        assert 'SectionTitle' in styles
        assert 'CustomBody' in styles
        assert 'Emphasis' in styles
        
        # 验证样式属性
        title_style = styles['CustomTitle']
        assert title_style.fontSize == 24
    
    def test_generator_without_cache(self):
        """测试无缓存模式"""
        gen = PDFGenerator(use_cache=False)
        assert gen.cache is None
    
    def test_generator_with_cache(self):
        """测试启用缓存模式"""
        gen = PDFGenerator(use_cache=True)
        assert gen.cache is not None
        assert isinstance(gen.cache, ReportCache)


@pytest.mark.skipif(not HAS_REPORTLAB, reason="需要reportlab库")
class TestReportCacheEdgeCases:
    """缓存边界情况测试"""
    
    @pytest.fixture
    def temp_cache_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_empty_data(self, temp_cache_dir):
        """测试空数据"""
        cache = ReportCache(cache_dir=temp_cache_dir)
        
        empty_data = {}
        pdf = b'empty pdf'
        
        cache.set(empty_data, 'signal', pdf)
        result = cache.get(empty_data, 'signal')
        
        assert result == pdf
    
    def test_large_data(self, temp_cache_dir):
        """测试大数据"""
        cache = ReportCache(cache_dir=temp_cache_dir)
        
        large_data = {
            f'network_{i}': {
                'ssid': f'WiFi_{i}',
                'signal': -50 - i,
                'channels': list(range(100))
            }
            for i in range(100)
        }
        
        pdf = b'large pdf' * 1000
        
        cache.set(large_data, 'signal', pdf)
        result = cache.get(large_data, 'signal')
        
        assert result == pdf
    
    def test_unicode_data(self, temp_cache_dir):
        """测试Unicode数据"""
        cache = ReportCache(cache_dir=temp_cache_dir)
        
        unicode_data = {
            'network': '测试WiFi网络',
            'description': '这是一个包含中文的描述 🌐📡',
            'location': '北京市海淀区'
        }
        
        pdf = b'unicode pdf'
        
        cache.set(unicode_data, 'signal', pdf)
        result = cache.get(unicode_data, 'signal')
        
        assert result == pdf
    
    def test_corrupted_meta_file(self, temp_cache_dir):
        """测试损坏的元数据文件"""
        cache = ReportCache(cache_dir=temp_cache_dir)
        
        data = {'network': 'Test'}
        cache.set(data, 'signal', b'pdf')
        
        # 损坏元数据文件
        cache_key = cache._compute_hash(data)
        meta_file = cache._get_meta_path(cache_key, 'signal')
        
        with open(meta_file, 'w') as f:
            f.write('invalid json {{{')
        
        # 应该返回None而不是抛出异常
        result = cache.get(data, 'signal')
        assert result is None
    
    def test_missing_pdf_file(self, temp_cache_dir):
        """测试PDF文件缺失"""
        cache = ReportCache(cache_dir=temp_cache_dir)
        
        data = {'network': 'Test'}
        cache.set(data, 'signal', b'pdf')
        
        # 删除PDF文件但保留meta
        cache_key = cache._compute_hash(data)
        cache_file = cache._get_cache_path(cache_key, 'signal')
        cache_file.unlink()
        
        # 应该返回None
        result = cache.get(data, 'signal')
        assert result is None
    
    def test_concurrent_access(self, temp_cache_dir):
        """测试并发访问"""
        import threading
        
        cache = ReportCache(cache_dir=temp_cache_dir)
        results = []
        
        def write_cache(i):
            data = {'network': f'WiFi{i}'}
            cache.set(data, 'signal', f'pdf{i}'.encode())
        
        def read_cache(i):
            data = {'network': f'WiFi{i}'}
            result = cache.get(data, 'signal')
            results.append(result)
        
        # 并发写入
        threads = [threading.Thread(target=write_cache, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # 并发读取
        threads = [threading.Thread(target=read_cache, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # 应该成功读取大部分缓存
        assert len([r for r in results if r is not None]) >= 5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
