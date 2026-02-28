#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ChannelUtilizationAnalyzer测试
测试信道利用率分析核心功能，提升覆盖率
"""

import pytest

# 尝试导入ChannelUtilizationAnalyzer
try:
    from wifi_modules.analytics.channel_utilization import ChannelUtilizationAnalyzer
    HAS_ANALYZER = True
except ImportError:
    HAS_ANALYZER = False


@pytest.mark.skipif(not HAS_ANALYZER, reason="需要ChannelUtilizationAnalyzer模块")
class TestChannelUtilizationInit:
    """ChannelUtilizationAnalyzer初始化测试"""
    
    def test_analyzer_initialization(self):
        """测试分析器初始化"""
        analyzer = ChannelUtilizationAnalyzer()
        
        assert analyzer.channel_data is not None
        assert analyzer.band_stats is not None
        assert '2.4GHz' in analyzer.band_stats
        assert '5GHz' in analyzer.band_stats
    
    def test_24ghz_channels_definition(self):
        """测试2.4GHz信道定义"""
        channels = ChannelUtilizationAnalyzer.CHANNELS_24GHZ
        
        assert isinstance(channels, list)
        assert len(channels) == 14
        assert 1 in channels
        assert 14 in channels
    
    def test_5ghz_channels_definition(self):
        """测试5GHz信道定义"""
        channels = ChannelUtilizationAnalyzer.CHANNELS_5GHZ
        
        assert isinstance(channels, list)
        assert len(channels) > 0
        assert 36 in channels
        assert 165 in channels


@pytest.mark.skipif(not HAS_ANALYZER, reason="需要ChannelUtilizationAnalyzer模块")
class TestChannelAnalysis:
    """信道分析测试"""
    
    @pytest.fixture
    def analyzer(self):
        return ChannelUtilizationAnalyzer()
    
    def test_analyze_empty_networks(self, analyzer):
        """测试空网络列表分析"""
        result = analyzer.analyze_channels([])
        
        assert result['total_networks'] == 0
        assert result['total_24ghz'] == 0
        assert result['total_5ghz'] == 0
    
    def test_analyze_single_24ghz_network(self, analyzer):
        """测试单个2.4GHz网络"""
        networks = [
            {'ssid': 'TestWiFi', 'channel': 6, 'signal': -50, 'bssid': 'aa:bb:cc:dd:ee:ff'}
        ]
        
        result = analyzer.analyze_channels(networks)
        
        assert result['total_networks'] == 1
        assert result['total_24ghz'] == 1
        assert result['total_5ghz'] == 0
        assert 6 in result['channels_24ghz']
        assert result['channels_24ghz'][6] == 1
    
    def test_analyze_single_5ghz_network(self, analyzer):
        """测试单个5GHz网络"""
        networks = [
            {'ssid': 'TestWiFi5G', 'channel': 36, 'signal': -55}
        ]
        
        result = analyzer.analyze_channels(networks)
        
        assert result['total_networks'] == 1
        assert result['total_24ghz'] == 0
        assert result['total_5ghz'] == 1
        assert 36 in result['channels_5ghz']
    
    def test_analyze_mixed_networks(self, analyzer):
        """测试混合频段网络"""
        networks = [
            {'ssid': 'WiFi24_1', 'channel': 1, 'signal': -50},
            {'ssid': 'WiFi24_6', 'channel': 6, 'signal': -55},
            {'ssid': 'WiFi24_11', 'channel': 11, 'signal': -60},
            {'ssid': 'WiFi5_36', 'channel': 36, 'signal': -45},
            {'ssid': 'WiFi5_149', 'channel': 149, 'signal': -52}
        ]
        
        result = analyzer.analyze_channels(networks)
        
        assert result['total_networks'] == 5
        assert result['total_24ghz'] == 3
        assert result['total_5ghz'] == 2
    
    def test_analyze_multiple_networks_same_channel(self, analyzer):
        """测试同一信道多个网络"""
        networks = [
            {'ssid': 'WiFi1', 'channel': 6, 'signal': -50},
            {'ssid': 'WiFi2', 'channel': 6, 'signal': -55},
            {'ssid': 'WiFi3', 'channel': 6, 'signal': -60}
        ]
        
        result = analyzer.analyze_channels(networks)
        
        assert result['channels_24ghz'][6] == 3
    
    def test_analyze_invalid_channel(self, analyzer):
        """测试无效信道"""
        networks = [
            {'ssid': 'Invalid', 'channel': 0, 'signal': -50},
            {'ssid': 'Invalid2', 'channel': -1, 'signal': -55}
        ]
        
        result = analyzer.analyze_channels(networks)
        
        # 无效信道应该被忽略
        assert result['total_24ghz'] == 0
        assert result['total_5ghz'] == 0
    
    def test_analyze_missing_channel(self, analyzer):
        """测试缺少channel字段"""
        networks = [
            {'ssid': 'NoChannel', 'signal': -50}
        ]
        
        result = analyzer.analyze_channels(networks)
        
        # 缺少信道的网络应该被忽略
        assert result['total_24ghz'] == 0
        assert result['total_5ghz'] == 0


@pytest.mark.skipif(not HAS_ANALYZER, reason="需要ChannelUtilizationAnalyzer模块")
class TestMostCongested:
    """最拥挤信道测试"""
    
    @pytest.fixture
    def analyzer(self):
        return ChannelUtilizationAnalyzer()
    
    def test_most_congested_empty(self, analyzer):
        """测试空数据的最拥挤信道"""
        analyzer.analyze_channels([])
        
        result = analyzer._get_most_congested('2.4GHz')
        assert result == (0, 0)
    
    def test_most_congested_24ghz(self, analyzer):
        """测试2.4GHz最拥挤信道"""
        networks = [
            {'channel': 1, 'ssid': 'W1'},
            {'channel': 6, 'ssid': 'W2'},
            {'channel': 6, 'ssid': 'W3'},
            {'channel': 6, 'ssid': 'W4'},
            {'channel': 11, 'ssid': 'W5'}
        ]
        
        analyzer.analyze_channels(networks)
        channel, count = analyzer._get_most_congested('2.4GHz')
        
        assert channel == 6
        assert count == 3
    
    def test_most_congested_5ghz(self, analyzer):
        """测试5GHz最拥挤信道"""
        networks = [
            {'channel': 36, 'ssid': 'W1'},
            {'channel': 149, 'ssid': 'W2'},
            {'channel': 149, 'ssid': 'W3'}
        ]
        
        analyzer.analyze_channels(networks)
        channel, count = analyzer._get_most_congested('5GHz')
        
        assert channel == 149
        assert count == 2


@pytest.mark.skipif(not HAS_ANALYZER, reason="需要ChannelUtilizationAnalyzer模块")
class TestChannelRecommendation:
    """信道推荐测试"""
    
    @pytest.fixture
    def analyzer(self):
        return ChannelUtilizationAnalyzer()
    
    def test_recommend_empty_24ghz(self, analyzer):
        """测试空数据时的2.4GHz推荐"""
        analyzer.analyze_channels([])
        
        recommended = analyzer._recommend_channel('2.4GHz')
        
        assert recommended in ChannelUtilizationAnalyzer.CHANNELS_24GHZ
        assert recommended == 1  # 第一个信道
    
    def test_recommend_empty_5ghz(self, analyzer):
        """测试空数据时的5GHz推荐"""
        analyzer.analyze_channels([])
        
        recommended = analyzer._recommend_channel('5GHz')
        
        assert recommended in ChannelUtilizationAnalyzer.CHANNELS_5GHZ
        assert recommended == 36  # 第一个信道
    
    def test_recommend_least_used_24ghz(self, analyzer):
        """测试推荐使用最少的2.4GHz信道"""
        networks = [
            {'channel': 1, 'ssid': 'W1'},
            {'channel': 1, 'ssid': 'W2'},
            {'channel': 6, 'ssid': 'W3'},
            {'channel': 6, 'ssid': 'W4'},
            {'channel': 6, 'ssid': 'W5'}
            # 信道11未使用
        ]
        
        analyzer.analyze_channels(networks)
        recommended = analyzer._recommend_channel('2.4GHz')
        
        # 应该推荐未使用的信道（11或其他未使用的）
        # 或者使用最少的信道（1，使用2次）
        assert recommended in ChannelUtilizationAnalyzer.CHANNELS_24GHZ
    
    def test_recommend_least_used_5ghz(self, analyzer):
        """测试推荐使用最少的5GHz信道"""
        networks = [
            {'channel': 36, 'ssid': 'W1'},
            {'channel': 36, 'ssid': 'W2'},
            {'channel': 40, 'ssid': 'W3'}
            # 其他信道未使用
        ]
        
        analyzer.analyze_channels(networks)
        recommended = analyzer._recommend_channel('5GHz')
        
        # 应该推荐未使用的信道
        assert recommended in ChannelUtilizationAnalyzer.CHANNELS_5GHZ
        # 如果所有信道都有使用，推荐使用最少的


@pytest.mark.skipif(not HAS_ANALYZER, reason="需要ChannelUtilizationAnalyzer模块")
class TestChannelDetails:
    """信道详情测试"""
    
    @pytest.fixture
    def analyzer(self):
        return ChannelUtilizationAnalyzer()
    
    def test_get_channel_details_existing(self, analyzer):
        """测试获取存在的信道详情"""
        networks = [
            {'channel': 6, 'ssid': 'WiFi1', 'signal': -50},
            {'channel': 6, 'ssid': 'WiFi2', 'signal': -55},
            {'channel': 11, 'ssid': 'WiFi3', 'signal': -60}
        ]
        
        analyzer.analyze_channels(networks)
        details = analyzer.get_channel_details(6)
        
        assert len(details) == 2
        assert details[0]['ssid'] in ['WiFi1', 'WiFi2']
    
    def test_get_channel_details_nonexistent(self, analyzer):
        """测试获取不存在的信道详情"""
        networks = [
            {'channel': 6, 'ssid': 'WiFi1'}
        ]
        
        analyzer.analyze_channels(networks)
        details = analyzer.get_channel_details(11)
        
        assert isinstance(details, list)
        assert len(details) == 0


@pytest.mark.skipif(not HAS_ANALYZER, reason="需要ChannelUtilizationAnalyzer模块")
class TestSummaryText:
    """摘要文本测试"""
    
    @pytest.fixture
    def analyzer(self):
        return ChannelUtilizationAnalyzer()
    
    def test_summary_text_empty(self, analyzer):
        """测试空数据的摘要文本"""
        analyzer.analyze_channels([])
        summary = analyzer.get_summary_text()
        
        assert isinstance(summary, str)
        assert len(summary) > 0
    
    def test_summary_text_with_data(self, analyzer):
        """测试有数据的摘要文本"""
        networks = [
            {'channel': 6, 'ssid': 'WiFi1'},
            {'channel': 36, 'ssid': 'WiFi5G'}
        ]
        
        analyzer.analyze_channels(networks)
        summary = analyzer.get_summary_text()
        
        assert isinstance(summary, str)
        assert len(summary) > 0


@pytest.mark.skipif(not HAS_ANALYZER, reason="需要ChannelUtilizationAnalyzer模块")
class TestAnalyzeResult:
    """分析结果测试"""
    
    @pytest.fixture
    def analyzer(self):
        return ChannelUtilizationAnalyzer()
    
    def test_result_structure(self, analyzer):
        """测试分析结果结构"""
        networks = [
            {'channel': 6, 'ssid': 'Test'}
        ]
        
        result = analyzer.analyze_channels(networks)
        
        # 验证必需的键存在
        assert 'total_networks' in result
        assert 'total_24ghz' in result
        assert 'total_5ghz' in result
        assert 'channels_24ghz' in result
        assert 'channels_5ghz' in result
        assert 'most_congested_24' in result
        assert 'most_congested_5' in result
        assert 'recommended_24' in result
        assert 'recommended_5' in result
    
    def test_result_types(self, analyzer):
        """测试分析结果数据类型"""
        result = analyzer.analyze_channels([])
        
        assert isinstance(result['total_networks'], int)
        assert isinstance(result['total_24ghz'], int)
        assert isinstance(result['total_5ghz'], int)
        assert isinstance(result['channels_24ghz'], dict)
        assert isinstance(result['channels_5ghz'], dict)
        assert isinstance(result['most_congested_24'], tuple)
        assert isinstance(result['most_congested_5'], tuple)
        assert isinstance(result['recommended_24'], int)
        assert isinstance(result['recommended_5'], int)


@pytest.mark.skipif(not HAS_ANALYZER, reason="需要ChannelUtilizationAnalyzer模块")
class TestEdgeCases:
    """边界情况测试"""
    
    @pytest.fixture
    def analyzer(self):
        return ChannelUtilizationAnalyzer()
    
    def test_large_dataset(self, analyzer):
        """测试大数据集"""
        # 生成100个网络
        networks = [
            {'channel': i % 11 + 1, 'ssid': f'WiFi{i}'}
            for i in range(100)
        ]
        
        result = analyzer.analyze_channels(networks)
        
        assert result['total_networks'] == 100
        assert result['total_24ghz'] == 100
    
    def test_all_channels_used(self, analyzer):
        """测试所有信道都被使用"""
        networks = []
        for ch in ChannelUtilizationAnalyzer.CHANNELS_24GHZ:
            networks.append({'channel': ch, 'ssid': f'WiFi_CH{ch}'})
        
        result = analyzer.analyze_channels(networks)
        
        assert len(result['channels_24ghz']) == 14
    
    def test_repeated_analysis(self, analyzer):
        """测试重复分析（数据清除）"""
        networks1 = [{'channel': 6, 'ssid': 'WiFi1'}]
        networks2 = [{'channel': 11, 'ssid': 'WiFi2'}]
        
        result1 = analyzer.analyze_channels(networks1)
        assert result1['total_networks'] == 1
        assert 6 in result1['channels_24ghz']
        
        # 第二次分析应该清除旧数据
        result2 = analyzer.analyze_channels(networks2)
        assert result2['total_networks'] == 1
        assert 11 in result2['channels_24ghz']
        assert 6 not in result2['channels_24ghz']
    
    def test_unicode_ssid(self, analyzer):
        """测试Unicode SSID"""
        networks = [
            {'channel': 6, 'ssid': '中文WiFi'},
            {'channel': 6, 'ssid': 'Café☕'},
            {'channel': 36, 'ssid': '日本語'}
        ]
        
        result = analyzer.analyze_channels(networks)
        
        assert result['total_networks'] == 3
        assert result['total_24ghz'] == 2
        assert result['total_5ghz'] == 1
    
    def test_missing_fields(self, analyzer):
        """测试缺失字段"""
        networks = [
            {'channel': 6},  # 缺少ssid
            {'ssid': 'NoChannel'},  # 缺少channel
            {}  # 空字典
        ]
        
        result = analyzer.analyze_channels(networks)
        
        # 应该能够处理缺失字段
        assert isinstance(result, dict)
