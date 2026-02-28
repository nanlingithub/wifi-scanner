"""
信号趋势分析模块测试
测试wifi_modules.analytics.signal_trend.SignalTrendAnalyzer
"""
import pytest
import json
import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import numpy as np

from wifi_modules.analytics.signal_trend import SignalTrendAnalyzer


@pytest.fixture
def temp_data_file():
    """创建临时数据文件"""
    fd, path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def analyzer(temp_data_file):
    """创建分析器实例"""
    return SignalTrendAnalyzer(data_file=temp_data_file)


@pytest.fixture
def analyzer_with_data(temp_data_file):
    """创建带有测试数据的分析器"""
    analyzer = SignalTrendAnalyzer(data_file=temp_data_file)
    
    # 添加24小时数据
    base_time = datetime.now()
    for i in range(48):  # 48个数据点，每半小时一个
        timestamp = base_time - timedelta(hours=24 - i*0.5)
        # 模拟信号波动 -70±10 dBm
        signal = -70 + 10 * np.sin(i / 8)
        analyzer.history_data.append({
            'timestamp': timestamp.isoformat(),
            'ssid': 'TestWiFi',
            'signal_dbm': signal
        })
    
    # 添加第二个WiFi的数据
    for i in range(24):
        timestamp = base_time - timedelta(hours=12 - i*0.5)
        signal = -60 + 5 * np.cos(i / 6)
        analyzer.history_data.append({
            'timestamp': timestamp.isoformat(),
            'ssid': 'TestWiFi2',
            'signal_dbm': signal
        })
    
    return analyzer


class TestSignalTrendAnalyzerInit:
    """测试初始化"""
    
    def test_init_default(self, temp_data_file):
        """测试默认初始化"""
        analyzer = SignalTrendAnalyzer(data_file=temp_data_file)
        
        assert analyzer.data_file == temp_data_file
        assert analyzer.history_data == []
        assert analyzer.max_days == 7
    
    def test_init_loads_existing_data(self, temp_data_file):
        """测试加载已存在的数据"""
        test_data = [
            {
                'timestamp': datetime.now().isoformat(),
                'ssid': 'TestAP',
                'signal_dbm': -65.0
            }
        ]
        
        with open(temp_data_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        analyzer = SignalTrendAnalyzer(data_file=temp_data_file)
        
        assert len(analyzer.history_data) == 1
        assert analyzer.history_data[0]['ssid'] == 'TestAP'
        assert analyzer.history_data[0]['signal_dbm'] == -65.0
    
    def test_init_with_corrupted_file(self, temp_data_file):
        """测试处理损坏的数据文件"""
        with open(temp_data_file, 'w') as f:
            f.write("invalid json data{{{")
        
        analyzer = SignalTrendAnalyzer(data_file=temp_data_file)
        
        # 应该回退到空列表
        assert analyzer.history_data == []


class TestAddDataPoint:
    """测试添加数据点"""
    
    def test_add_single_data_point(self, analyzer):
        """测试添加单个数据点"""
        analyzer.add_data_point('MyWiFi', -55.0)
        
        assert len(analyzer.history_data) == 1
        assert analyzer.history_data[0]['ssid'] == 'MyWiFi'
        assert analyzer.history_data[0]['signal_dbm'] == -55.0
        assert 'timestamp' in analyzer.history_data[0]
    
    def test_add_multiple_data_points(self, analyzer):
        """测试添加多个数据点"""
        for i in range(5):
            analyzer.add_data_point('WiFi', -60.0 - i)
        
        assert len(analyzer.history_data) == 5
        assert analyzer.history_data[0]['signal_dbm'] == -60.0
        assert analyzer.history_data[4]['signal_dbm'] == -64.0
    
    def test_auto_save_on_tenth_point(self, analyzer, temp_data_file):
        """测试每10个数据点自动保存"""
        for i in range(10):
            analyzer.add_data_point('WiFi', -65.0)
        
        # 应该已经保存
        assert os.path.exists(temp_data_file)
        
        with open(temp_data_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert len(saved_data) == 10
    
    def test_cleanup_old_data_on_add(self, analyzer):
        """测试添加时清理旧数据"""
        # 添加超过max_days的旧数据
        old_time = datetime.now() - timedelta(days=8)
        analyzer.history_data.append({
            'timestamp': old_time.isoformat(),
            'ssid': 'OldWiFi',
            'signal_dbm': -70.0
        })
        
        # 添加新数据点
        analyzer.add_data_point('NewWiFi', -60.0)
        
        # 旧数据应该被清理
        assert len(analyzer.history_data) == 1
        assert analyzer.history_data[0]['ssid'] == 'NewWiFi'


class TestGetTrendData:
    """测试获取趋势数据"""
    
    def test_get_trend_data_basic(self, analyzer_with_data):
        """测试基本趋势数据获取"""
        result = analyzer_with_data.get_trend_data('TestWiFi', hours=24)
        
        assert 'timestamps' in result
        assert 'signals' in result
        assert 'stats' in result
        assert len(result['timestamps']) > 0
        assert len(result['signals']) > 0
    
    def test_get_trend_data_empty(self, analyzer):
        """测试无数据时返回空结果"""
        result = analyzer.get_trend_data('NonExistent', hours=24)
        
        assert result['timestamps'] == []
        assert result['signals'] == []
        assert result['stats'] == {}
    
    def test_get_trend_data_time_filter(self, analyzer_with_data):
        """测试时间过滤"""
        result_24h = analyzer_with_data.get_trend_data('TestWiFi', hours=24)
        result_12h = analyzer_with_data.get_trend_data('TestWiFi', hours=12)
        
        # 12小时数据应该少于24小时
        assert len(result_12h['signals']) < len(result_24h['signals'])
    
    def test_trend_data_stats_calculation(self, analyzer_with_data):
        """测试统计数据计算"""
        result = analyzer_with_data.get_trend_data('TestWiFi', hours=24)
        stats = result['stats']
        
        assert 'max' in stats
        assert 'min' in stats
        assert 'mean' in stats
        assert 'std' in stats
        assert 'max_time' in stats
        assert 'min_time' in stats
        assert 'data_points' in stats
        assert 'time_span' in stats
        
        # 验证最大值和最小值
        assert stats['max'] == max(result['signals'])
        assert stats['min'] == min(result['signals'])
        assert stats['data_points'] == len(result['signals'])
    
    def test_trend_data_multiple_ssids(self, analyzer_with_data):
        """测试多个SSID数据不干扰"""
        result1 = analyzer_with_data.get_trend_data('TestWiFi', hours=24)
        result2 = analyzer_with_data.get_trend_data('TestWiFi2', hours=24)
        
        # 两个WiFi的数据应该独立
        assert len(result1['signals']) != len(result2['signals'])


class TestGenerateTrendChart:
    """测试生成趋势图"""
    
    def test_generate_chart_with_data(self, analyzer_with_data):
        """测试生成图表"""
        fig = analyzer_with_data.generate_trend_chart('TestWiFi', hours=24)
        
        assert fig is not None
        assert hasattr(fig, 'get_axes')
        axes = fig.get_axes()
        assert len(axes) > 0
    
    def test_generate_chart_no_data(self, analyzer):
        """测试无数据时生成空图表"""
        fig = analyzer.generate_trend_chart('NonExistent', hours=24)
        
        assert fig is not None
        # 应该显示"暂无数据"文本
        axes = fig.get_axes()
        assert len(axes) > 0
    
    def test_generate_chart_different_time_ranges(self, analyzer_with_data):
        """测试不同时间范围的图表"""
        fig_1h = analyzer_with_data.generate_trend_chart('TestWiFi', hours=1)
        fig_6h = analyzer_with_data.generate_trend_chart('TestWiFi', hours=6)
        fig_24h = analyzer_with_data.generate_trend_chart('TestWiFi', hours=24)
        fig_48h = analyzer_with_data.generate_trend_chart('TestWiFi', hours=48)
        
        # 所有图表都应该成功生成
        assert all([fig_1h, fig_6h, fig_24h, fig_48h])


class TestGetComparisonData:
    """测试获取对比数据"""
    
    def test_get_comparison_single_ssid(self, analyzer_with_data):
        """测试单个SSID对比"""
        result = analyzer_with_data.get_comparison_data(['TestWiFi'], hours=24)
        
        assert 'TestWiFi' in result
        assert 'max' in result['TestWiFi']
        assert 'min' in result['TestWiFi']
        assert 'mean' in result['TestWiFi']
    
    def test_get_comparison_multiple_ssids(self, analyzer_with_data):
        """测试多个SSID对比"""
        result = analyzer_with_data.get_comparison_data(
            ['TestWiFi', 'TestWiFi2'], 
            hours=24
        )
        
        assert 'TestWiFi' in result
        assert 'TestWiFi2' in result
        assert len(result) == 2
    
    def test_get_comparison_with_nonexistent(self, analyzer_with_data):
        """测试包含不存在的SSID"""
        result = analyzer_with_data.get_comparison_data(
            ['TestWiFi', 'NonExistent'], 
            hours=24
        )
        
        # 只应该包含存在的SSID
        assert 'TestWiFi' in result
        assert 'NonExistent' not in result


class TestExportToCSV:
    """测试CSV导出"""
    
    def test_export_to_csv_basic(self, analyzer_with_data, temp_data_file):
        """测试基本CSV导出"""
        output_dir = os.path.dirname(temp_data_file)
        filename = os.path.join(output_dir, 'test_export.csv')
        
        try:
            result_file = analyzer_with_data.export_to_csv(
                'TestWiFi', 
                hours=24, 
                filename=filename
            )
            
            assert os.path.exists(result_file)
            
            # 验证CSV内容
            with open(result_file, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
            
            # 应该有标题行和数据行
            assert len(lines) > 1
            assert '时间' in lines[0]
            assert '信号强度' in lines[0]
        finally:
            if os.path.exists(filename):
                os.remove(filename)
    
    def test_export_to_csv_auto_filename(self, analyzer_with_data):
        """测试自动生成文件名"""
        try:
            result_file = analyzer_with_data.export_to_csv('TestWiFi', hours=24)
            
            assert os.path.exists(result_file)
            assert result_file.startswith('signal_trend_TestWiFi_')
            assert result_file.endswith('.csv')
        finally:
            if os.path.exists(result_file):
                os.remove(result_file)
    
    def test_export_to_csv_no_data(self, analyzer):
        """测试无数据时导出失败"""
        with pytest.raises(ValueError) as exc_info:
            analyzer.export_to_csv('NonExistent', hours=24)
        
        assert '没有' in str(exc_info.value)
        assert 'NonExistent' in str(exc_info.value)


class TestGetAvailableSSIDs:
    """测试获取可用SSID列表"""
    
    def test_get_available_ssids(self, analyzer_with_data):
        """测试获取SSID列表"""
        ssids = analyzer_with_data.get_available_ssids(hours=24)
        
        assert 'TestWiFi' in ssids
        assert 'TestWiFi2' in ssids
        assert len(ssids) == 2
    
    def test_get_available_ssids_empty(self, analyzer):
        """测试空数据时返回空列表"""
        ssids = analyzer.get_available_ssids(hours=24)
        
        assert ssids == []
    
    def test_get_available_ssids_time_filter(self, analyzer_with_data):
        """测试时间过滤影响SSID列表"""
        # TestWiFi2只有12小时的数据
        ssids_24h = analyzer_with_data.get_available_ssids(hours=24)
        ssids_6h = analyzer_with_data.get_available_ssids(hours=6)
        
        # 24小时应该包含两个WiFi
        assert len(ssids_24h) == 2
        
        # 6小时可能只包含TestWiFi2
        assert 'TestWiFi2' in ssids_6h


class TestDataPersistence:
    """测试数据持久化"""
    
    def test_save_and_load(self, temp_data_file):
        """测试保存和加载数据"""
        # 创建分析器并添加数据
        analyzer1 = SignalTrendAnalyzer(data_file=temp_data_file)
        analyzer1.add_data_point('WiFi1', -65.0)
        analyzer1.add_data_point('WiFi2', -70.0)
        analyzer1._save_history()
        
        # 创建新分析器加载数据
        analyzer2 = SignalTrendAnalyzer(data_file=temp_data_file)
        
        assert len(analyzer2.history_data) == 2
        assert analyzer2.history_data[0]['ssid'] == 'WiFi1'
        assert analyzer2.history_data[1]['ssid'] == 'WiFi2'
    
    def test_save_handles_exceptions(self, analyzer):
        """测试保存异常处理"""
        # 设置无效路径
        analyzer.data_file = '/invalid/path/file.json'
        
        # 应该不会抛出异常
        analyzer._save_history()


class TestCleanupOldData:
    """测试清理旧数据"""
    
    def test_cleanup_removes_old_data(self, analyzer):
        """测试清理超期数据"""
        # 添加旧数据
        old_time = datetime.now() - timedelta(days=8)
        analyzer.history_data.append({
            'timestamp': old_time.isoformat(),
            'ssid': 'OldWiFi',
            'signal_dbm': -70.0
        })
        
        # 添加新数据
        new_time = datetime.now()
        analyzer.history_data.append({
            'timestamp': new_time.isoformat(),
            'ssid': 'NewWiFi',
            'signal_dbm': -60.0
        })
        
        analyzer._cleanup_old_data()
        
        # 只应该保留新数据
        assert len(analyzer.history_data) == 1
        assert analyzer.history_data[0]['ssid'] == 'NewWiFi'
    
    def test_cleanup_keeps_recent_data(self, analyzer):
        """测试保留最近的数据"""
        # 添加6天前的数据
        recent_time = datetime.now() - timedelta(days=6)
        analyzer.history_data.append({
            'timestamp': recent_time.isoformat(),
            'ssid': 'RecentWiFi',
            'signal_dbm': -65.0
        })
        
        analyzer._cleanup_old_data()
        
        # 应该保留
        assert len(analyzer.history_data) == 1
        assert analyzer.history_data[0]['ssid'] == 'RecentWiFi'


class TestGetHourlyAverage:
    """测试每小时平均值"""
    
    def test_get_hourly_average(self, analyzer_with_data):
        """测试计算每小时平均值"""
        result = analyzer_with_data.get_hourly_average('TestWiFi', hours=24)
        
        # 应该有多个小时的数据
        assert len(result) > 0
        
        # 每个值都应该是数字
        for hour, avg in result.items():
            assert isinstance(hour, datetime)
            assert isinstance(avg, (int, float))
    
    def test_get_hourly_average_empty(self, analyzer):
        """测试无数据时返回空字典"""
        result = analyzer.get_hourly_average('NonExistent', hours=24)
        
        assert result == {}
    
    def test_hourly_average_grouping(self, analyzer):
        """测试小时分组正确性"""
        base_time = datetime.now().replace(minute=0, second=0, microsecond=0)
        
        # 同一小时添加3个数据点（确保在同一小时内）
        for i in range(3):
            timestamp = base_time.replace(minute=i*15)  # 0, 15, 30分钟
            analyzer.history_data.append({
                'timestamp': timestamp.isoformat(),
                'ssid': 'TestWiFi',
                'signal_dbm': -60.0 - i
            })
        
        result = analyzer.get_hourly_average('TestWiFi', hours=2)
        
        # 应该至少有一个小时的数据
        assert len(result) >= 1
        
        # 找到包含所有数据点的那个小时
        hour_with_data = base_time
        if hour_with_data in result:
            avg_value = result[hour_with_data]
            # 平均值应该是 (-60 + -61 + -62) / 3 = -61
            assert abs(avg_value - (-61.0)) < 0.01


class TestClearHistory:
    """测试清空历史数据"""
    
    def test_clear_specific_ssid(self, analyzer_with_data):
        """测试清空特定SSID数据"""
        initial_count = len(analyzer_with_data.history_data)
        
        analyzer_with_data.clear_history(ssid='TestWiFi')
        
        # TestWiFi数据应该被删除
        assert len(analyzer_with_data.history_data) < initial_count
        
        # TestWiFi2数据应该保留
        remaining_ssids = [d['ssid'] for d in analyzer_with_data.history_data]
        assert 'TestWiFi' not in remaining_ssids
        assert 'TestWiFi2' in remaining_ssids
    
    def test_clear_all_history(self, analyzer_with_data):
        """测试清空所有数据"""
        analyzer_with_data.clear_history()
        
        assert len(analyzer_with_data.history_data) == 0
    
    def test_clear_saves_changes(self, analyzer_with_data, temp_data_file):
        """测试清空后保存更改"""
        analyzer_with_data.clear_history()
        
        # 重新加载验证
        analyzer_new = SignalTrendAnalyzer(data_file=temp_data_file)
        assert len(analyzer_new.history_data) == 0


class TestEdgeCases:
    """测试边界情况"""
    
    def test_extreme_signal_values(self, analyzer):
        """测试极端信号值"""
        analyzer.add_data_point('WiFi', -100.0)  # 很弱
        analyzer.add_data_point('WiFi', -30.0)   # 很强
        
        result = analyzer.get_trend_data('WiFi', hours=1)
        
        assert result['stats']['min'] == -100.0
        assert result['stats']['max'] == -30.0
    
    def test_unicode_ssid(self, analyzer):
        """测试Unicode SSID"""
        analyzer.add_data_point('中文WiFi', -65.0)
        analyzer.add_data_point('日本語WiFi', -70.0)
        
        ssids = analyzer.get_available_ssids(hours=1)
        
        assert '中文WiFi' in ssids
        assert '日本語WiFi' in ssids
    
    def test_large_dataset(self, analyzer):
        """测试大数据集"""
        base_time = datetime.now()
        
        # 添加1000个数据点
        for i in range(1000):
            timestamp = base_time - timedelta(minutes=i)
            analyzer.history_data.append({
                'timestamp': timestamp.isoformat(),
                'ssid': 'TestWiFi',
                'signal_dbm': -70.0 + (i % 20)
            })
        
        result = analyzer.get_trend_data('TestWiFi', hours=24)
        
        # 应该能正常处理
        assert len(result['signals']) > 0
        assert 'stats' in result
    
    def test_single_data_point(self, analyzer):
        """测试单个数据点"""
        analyzer.add_data_point('WiFi', -65.0)
        
        result = analyzer.get_trend_data('WiFi', hours=1)
        
        assert len(result['signals']) == 1
        assert result['stats']['max'] == result['stats']['min']
        assert result['stats']['std'] == 0.0
    
    def test_zero_hours_parameter(self, analyzer_with_data):
        """测试hours=0参数"""
        result = analyzer_with_data.get_trend_data('TestWiFi', hours=0)
        
        # 应该返回空或极少数据
        assert isinstance(result, dict)
    
    def test_negative_signal_values(self, analyzer):
        """测试负信号值（正常范围）"""
        # WiFi信号通常是负值
        for val in [-30, -50, -70, -90]:
            analyzer.add_data_point('WiFi', val)
        
        result = analyzer.get_trend_data('WiFi', hours=1)
        
        assert all(s < 0 for s in result['signals'])
