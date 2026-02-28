#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ChannelAnalysis核心测试
测试WiFi信道分析核心功能，提升覆盖率
"""

import pytest
from unittest.mock import Mock, MagicMock
from collections import deque

# 尝试导入ChannelAnalysisTab
try:
    from wifi_modules.channel_analysis import ChannelAnalysisTab
    HAS_CHANNEL_ANALYSIS = True
except ImportError:
    HAS_CHANNEL_ANALYSIS = False


@pytest.mark.skipif(not HAS_CHANNEL_ANALYSIS, reason="需要ChannelAnalysisTab模块")
@pytest.mark.skip(reason="需要真实Tkinter环境，跳过UI初始化测试")
class TestChannelAnalysisInit:
    """ChannelAnalysisTab初始化测试"""
    
    @pytest.fixture
    def mock_wifi_analyzer(self):
        """创建mock WiFiAnalyzer"""
        analyzer = Mock()
        analyzer.scan_wifi_networks = Mock(return_value=[])
        return analyzer
    
    @pytest.fixture
    def mock_parent(self):
        """创建mock parent frame"""
        parent = Mock()
        return parent
    
    def test_channel_analysis_initialization(self, mock_parent, mock_wifi_analyzer):
        """测试ChannelAnalysisTab基本初始化"""
        tab = ChannelAnalysisTab(mock_parent, mock_wifi_analyzer)
        
        # 验证基础属性
        assert tab.parent == mock_parent
        assert tab.wifi_analyzer == mock_wifi_analyzer
        assert isinstance(tab.channel_usage, dict)
        assert isinstance(tab.last_networks, list)
    
    def test_channel_history_initialization(self, mock_parent, mock_wifi_analyzer):
        """测试信道历史记录初始化"""
        tab = ChannelAnalysisTab(mock_parent, mock_wifi_analyzer)
        
        assert isinstance(tab.channel_history, deque)
        assert tab.channel_history.maxlen == 288  # 24小时历史
    
    def test_bonding_stats_initialization(self, mock_parent, mock_wifi_analyzer):
        """测试信道绑定统计初始化"""
        tab = ChannelAnalysisTab(mock_parent, mock_wifi_analyzer)
        
        assert isinstance(tab.bonding_stats, dict)
        assert '20MHz' in tab.bonding_stats
        assert '40MHz' in tab.bonding_stats
        assert '80MHz' in tab.bonding_stats
        assert '160MHz' in tab.bonding_stats
        assert '320MHz' in tab.bonding_stats
    
    def test_realtime_monitoring_initialization(self, mock_parent, mock_wifi_analyzer):
        """测试实时监控初始化"""
        tab = ChannelAnalysisTab(mock_parent, mock_wifi_analyzer)
        
        assert tab.realtime_monitoring == False
        assert tab.monitor_interval == 10
        assert tab.last_scan_time is None
        assert isinstance(tab.quality_history, deque)


@pytest.mark.skipif(not HAS_CHANNEL_ANALYSIS, reason="需要ChannelAnalysisTab模块")
class TestChannelRegions:
    """信道地区配置测试"""
    
    def test_channel_regions_structure(self):
        """测试信道地区配置结构"""
        regions = ChannelAnalysisTab.CHANNEL_REGIONS
        
        assert isinstance(regions, dict)
        assert len(regions) >= 8  # 至少8个地区
        
        # 验证主要地区
        assert "中国" in regions
        assert "美国" in regions
        assert "欧洲" in regions
        assert "日本" in regions
    
    def test_china_channel_config(self):
        """测试中国信道配置"""
        china = ChannelAnalysisTab.CHANNEL_REGIONS["中国"]
        
        assert "2.4GHz" in china
        assert "5GHz" in china
        assert "6GHz" in china
        assert "protocols" in china
        
        # 验证2.4GHz信道
        assert isinstance(china["2.4GHz"], list)
        assert 1 in china["2.4GHz"]
        assert 13 in china["2.4GHz"]
        
        # 验证支持的协议
        assert "WiFi 6E" in china["protocols"]
        assert "WiFi 7" in china["protocols"]
    
    def test_us_channel_config(self):
        """测试美国信道配置"""
        us = ChannelAnalysisTab.CHANNEL_REGIONS["美国"]
        
        # 验证5GHz信道（美国有更多可用信道）
        assert 36 in us["5GHz"]
        assert 165 in us["5GHz"]
        assert len(us["5GHz"]) > 10
    
    def test_all_regions_have_required_keys(self):
        """测试所有地区都有必需的键"""
        for region_name, config in ChannelAnalysisTab.CHANNEL_REGIONS.items():
            assert "2.4GHz" in config, f"{region_name}缺少2.4GHz配置"
            assert "5GHz" in config, f"{region_name}缺少5GHz配置"
            assert "protocols" in config, f"{region_name}缺少protocols配置"


@pytest.mark.skipif(not HAS_CHANNEL_ANALYSIS, reason="需要ChannelAnalysisTab模块")
class TestDFSChannels:
    """DFS信道测试"""
    
    def test_dfs_channels_range(self):
        """测试DFS信道范围"""
        dfs = ChannelAnalysisTab.DFS_CHANNELS
        
        assert isinstance(dfs, list)
        assert len(dfs) > 0
        
        # DFS信道应该在52-144范围内
        assert min(dfs) >= 52
        assert max(dfs) <= 144
    
    def test_dfs_channel_values(self):
        """测试DFS信道具体值"""
        dfs = ChannelAnalysisTab.DFS_CHANNELS
        
        # 验证一些已知的DFS信道
        assert 52 in dfs
        assert 56 in dfs
        assert 60 in dfs
        assert 64 in dfs
        assert 100 in dfs


@pytest.mark.skipif(not HAS_CHANNEL_ANALYSIS, reason="需要ChannelAnalysisTab模块")
class TestChannelBonding:
    """信道绑定配置测试"""
    
    def test_40mhz_pairs(self):
        """测试40MHz信道对配置"""
        pairs = ChannelAnalysisTab.CHANNEL_40MHZ_PAIRS
        
        assert isinstance(pairs, list)
        assert len(pairs) > 0
        
        # 验证第一个40MHz对
        first_pair = pairs[0]
        assert len(first_pair) == 2
        assert isinstance(first_pair[0], list)  # 信道列表
        assert isinstance(first_pair[1], int)   # 中心信道
    
    def test_80mhz_groups(self):
        """测试80MHz信道组配置"""
        groups = ChannelAnalysisTab.CHANNEL_80MHZ_GROUPS
        
        assert isinstance(groups, list)
        assert len(groups) > 0
        
        # 验证第一个80MHz组
        first_group = groups[0]
        channels, center = first_group
        assert len(channels) == 4  # 80MHz需要4个20MHz信道
        assert isinstance(center, int)
    
    def test_160mhz_groups(self):
        """测试160MHz信道组配置"""
        groups = ChannelAnalysisTab.CHANNEL_160MHZ_GROUPS
        
        assert isinstance(groups, list)
        
        for group in groups:
            channels, center = group
            assert len(channels) == 8  # 160MHz需要8个20MHz信道
    
    def test_320mhz_groups(self):
        """测试320MHz信道组配置（WiFi 7）"""
        groups = ChannelAnalysisTab.CHANNEL_320MHZ_GROUPS
        
        assert isinstance(groups, list)
        
        for group in groups:
            channels, center = group
            assert len(channels) == 16  # 320MHz需要16个20MHz信道


@pytest.mark.skipif(not HAS_CHANNEL_ANALYSIS, reason="需要ChannelAnalysisTab模块")
class TestUNIIBands:
    """6GHz UNII频段测试"""
    
    def test_unii_bands_structure(self):
        """测试UNII频段结构"""
        bands = ChannelAnalysisTab.UNII_BANDS_6GHZ
        
        assert isinstance(bands, dict)
        assert "UNII-5" in bands
        assert "UNII-6" in bands
        assert "UNII-7" in bands
        assert "UNII-8" in bands
    
    def test_unii5_channels(self):
        """测试UNII-5频段信道"""
        unii5 = ChannelAnalysisTab.UNII_BANDS_6GHZ["UNII-5"]
        
        assert isinstance(unii5, list)
        assert len(unii5) > 0
        # 5925-6425 MHz
        assert min(unii5) >= 1
    
    def test_all_unii_bands_have_channels(self):
        """测试所有UNII频段都有信道"""
        bands = ChannelAnalysisTab.UNII_BANDS_6GHZ
        
        for band_name, channels in bands.items():
            assert len(channels) > 0, f"{band_name}没有信道"


@pytest.mark.skipif(not HAS_CHANNEL_ANALYSIS, reason="需要ChannelAnalysisTab模块")
@pytest.mark.skip(reason="需要真实Tkinter环境")
class TestWiFiProtocolInfo:
    """WiFi协议信息测试"""
    
    @pytest.fixture
    def channel_tab(self, mock_parent, mock_wifi_analyzer):
        return ChannelAnalysisTab(mock_parent, mock_wifi_analyzer)
    
    @pytest.fixture
    def mock_parent(self):
        return Mock()
    
    @pytest.fixture
    def mock_wifi_analyzer(self):
        analyzer = Mock()
        analyzer.scan_wifi_networks = Mock(return_value=[])
        return analyzer
    
    def test_wifi_protocol_info_24ghz(self, channel_tab):
        """测试2.4GHz协议信息"""
        info = channel_tab.get_wifi_protocol_info(6, '2.4GHz', 20)
        
        assert isinstance(info, dict)
    
    def test_wifi_protocol_info_5ghz(self, channel_tab):
        """测试5GHz协议信息"""
        info = channel_tab.get_wifi_protocol_info(36, '5GHz', 80)
        
        assert isinstance(info, dict)
    
    def test_wifi_protocol_info_6ghz(self, channel_tab):
        """测试6GHz协议信息（WiFi 6E）"""
        info = channel_tab.get_wifi_protocol_info(37, '6GHz', 160)
        
        assert isinstance(info, dict)


@pytest.mark.skipif(not HAS_CHANNEL_ANALYSIS, reason="需要ChannelAnalysisTab模块")
@pytest.mark.skip(reason="需要真实Tkinter环境")
class TestSignalParsing:
    """信号解析测试"""
    
    @pytest.fixture
    def channel_tab(self, mock_parent, mock_wifi_analyzer):
        return ChannelAnalysisTab(mock_parent, mock_wifi_analyzer)
    
    @pytest.fixture
    def mock_parent(self):
        return Mock()
    
    @pytest.fixture
    def mock_wifi_analyzer(self):
        analyzer = Mock()
        analyzer.scan_wifi_networks = Mock(return_value=[])
        return analyzer
    
    def test_parse_signal_dbm_negative(self, channel_tab):
        """测试解析负值信号强度"""
        # 常见信号格式
        assert channel_tab._parse_signal_dbm("-50") == -50
        assert channel_tab._parse_signal_dbm("-70") == -70
    
    def test_parse_signal_dbm_percentage(self, channel_tab):
        """测试解析百分比信号强度"""
        # 百分比格式（需要转换为dBm）
        result = channel_tab._parse_signal_dbm("85%")
        assert isinstance(result, int)
        assert -100 <= result <= 0
    
    def test_parse_signal_dbm_invalid(self, channel_tab):
        """测试解析无效信号强度"""
        # 无效格式应该返回默认值
        result = channel_tab._parse_signal_dbm("invalid")
        assert isinstance(result, int)
        assert result <= 0


@pytest.mark.skip(reason="需要真实Tkinter环境")
@pytest.mark.skipif(not HAS_CHANNEL_ANALYSIS, reason="需要ChannelAnalysisTab模块")
class TestInterferenceScore:
    """干扰评分测试"""
    
    @pytest.fixture
    def channel_tab(self, mock_parent, mock_wifi_analyzer):
        return ChannelAnalysisTab(mock_parent, mock_wifi_analyzer)
    
    @pytest.fixture
    def mock_parent(self):
        return Mock()
    
    @pytest.fixture
    def mock_wifi_analyzer(self):
        analyzer = Mock()
        analyzer.scan_wifi_networks = Mock(return_value=[])
        return analyzer
    
    def test_interference_score_empty(self, channel_tab):
        """测试空信道的干扰评分"""
        usage = {}
        score = channel_tab._calculate_interference_score(6, usage, '2.4GHz')
        
        assert isinstance(score, float)
        assert score >= 0
    
    def test_interference_score_with_networks(self, channel_tab):
        """测试有网络的信道干扰评分"""
        usage = {
            6: {'count': 3, 'weight': 2.5}
        }
        score = channel_tab._calculate_interference_score(6, usage, '2.4GHz')
        
        assert isinstance(score, float)
        assert score > 0  # 有网络应该有干扰


@pytest.mark.skip(reason="需要真实Tkinter环境")
@pytest.mark.skipif(not HAS_CHANNEL_ANALYSIS, reason="需要ChannelAnalysisTab模块")
class TestBandwidthInference:
    """带宽推断测试"""
    
    @pytest.fixture
    def channel_tab(self, mock_parent, mock_wifi_analyzer):
        return ChannelAnalysisTab(mock_parent, mock_wifi_analyzer)
    
    @pytest.fixture
    def mock_parent(self):
        return Mock()
    
    @pytest.fixture
    def mock_wifi_analyzer(self):
        analyzer = Mock()
        analyzer.scan_wifi_networks = Mock(return_value=[])
        return analyzer
    
    def test_infer_bandwidth_from_protocol(self, channel_tab):
        """测试从协议推断带宽"""
        # WiFi 5 (802.11ac) 通常使用80MHz
        network_ac = {'protocol': '802.11ac', 'channel': 36}
        bandwidth = channel_tab._infer_bandwidth(network_ac)
        
        assert bandwidth in ['20MHz', '40MHz', '80MHz', '160MHz']
    
    def test_infer_bandwidth_from_channel(self, channel_tab):
        """测试从信道推断带宽"""
        # WiFi 4 (802.11n)
        network_n = {'protocol': '802.11n', 'channel': 6}
        bandwidth = channel_tab._infer_bandwidth(network_n)
        
        assert bandwidth in ['20MHz', '40MHz']
    
    def test_infer_bandwidth_default(self, channel_tab):
        """测试默认带宽推断"""
        # 未知协议
        network_unknown = {'channel': 1}
        bandwidth = channel_tab._infer_bandwidth(network_unknown)
        
        assert isinstance(bandwidth, str)
        assert 'MHz' in bandwidth


@pytest.mark.skip(reason="需要真实Tkinter环境")
@pytest.mark.skipif(not HAS_CHANNEL_ANALYSIS, reason="需要ChannelAnalysisTab模块")
class TestBondedGroupDetection:
    """绑定信道组检测测试"""
    
    @pytest.fixture
    def channel_tab(self, mock_parent, mock_wifi_analyzer):
        return ChannelAnalysisTab(mock_parent, mock_wifi_analyzer)
    
    @pytest.fixture
    def mock_parent(self):
        return Mock()
    
    @pytest.fixture
    def mock_wifi_analyzer(self):
        analyzer = Mock()
        analyzer.scan_wifi_networks = Mock(return_value=[])
        return analyzer
    
    def test_get_bonded_group_36(self, channel_tab):
        """测试获取信道36的绑定组"""
        group = channel_tab._get_bonded_group(36)
        
        assert isinstance(group, list)
        assert 36 in group
    
    def test_get_bonded_group_invalid(self, channel_tab):
        """测试无效信道的绑定组"""
        group = channel_tab._get_bonded_group(999)
        
        assert isinstance(group, list)
        # 无效信道应该返回空列表或只包含自己
        assert len(group) <= 1

@pytest.mark.skip(reason="需要真实Tkinter环境")

@pytest.mark.skipif(not HAS_CHANNEL_ANALYSIS, reason="需要ChannelAnalysisTab模块")
class TestChannelRecommendation:
    """信道推荐测试"""
    
    @pytest.fixture
    def channel_tab(self, mock_parent, mock_wifi_analyzer):
        return ChannelAnalysisTab(mock_parent, mock_wifi_analyzer)
    
    @pytest.fixture
    def mock_parent(self):
        return Mock()
    
    @pytest.fixture
    def mock_wifi_analyzer(self):
        analyzer = Mock()
        analyzer.scan_wifi_networks = Mock(return_value=[])
        return analyzer
    
    def test_recommend_24ghz_channels(self, channel_tab):
        """测试2.4GHz信道推荐"""
        recommendations = channel_tab._recommend_non_overlapping_channels('2.4GHz')
        
        assert isinstance(recommendations, list)
        # 2.4GHz常见推荐：1, 6, 11
        if len(recommendations) > 0:
            assert all(ch in range(1, 14) for ch in recommendations)
    
    def test_recommend_5ghz_channels(self, channel_tab):
        """测试5GHz信道推荐"""
        recommendations = channel_tab._recommend_non_overlapping_channels('5GHz')
        
        assert isinstance(recommendations, list)
        # 5GHz有更多可用信道
        if len(recommendations) > 0:
            assert all(ch >= 36 for ch in recommendations)

@pytest.mark.skip(reason="需要真实Tkinter环境")

@pytest.mark.skipif(not HAS_CHANNEL_ANALYSIS, reason="需要ChannelAnalysisTab模块")
class TestChannelBondingDetection:
    """信道绑定检测测试"""
    
    @pytest.fixture
    def channel_tab(self, mock_parent, mock_wifi_analyzer):
        return ChannelAnalysisTab(mock_parent, mock_wifi_analyzer)
    
    @pytest.fixture
    def mock_parent(self):
        return Mock()
    
    @pytest.fixture
    def mock_wifi_analyzer(self):
        analyzer = Mock()
        analyzer.scan_wifi_networks = Mock(return_value=[])
        return analyzer
    
    def test_detect_bonding_empty_networks(self, channel_tab):
        """测试空网络列表的绑定检测"""
        result = channel_tab._detect_channel_bonding([])
        
        assert isinstance(result, dict)
    
    def test_detect_bonding_single_network(self, channel_tab):
        """测试单个网络的绑定检测"""
        networks = [
            {'channel': 36, 'protocol': '802.11ac'}
        ]
        
        result = channel_tab._detect_channel_bonding(networks)
        
        assert isinstance(result, dict)
@pytest.mark.skip(reason="需要真实Tkinter环境")


@pytest.mark.skipif(not HAS_CHANNEL_ANALYSIS, reason="需要ChannelAnalysisTab模块")
class TestChannelCount:
    """信道计数测试"""
    
    @pytest.fixture
    def channel_tab(self, mock_parent, mock_wifi_analyzer):
        tab = ChannelAnalysisTab(mock_parent, mock_wifi_analyzer)
        # 设置一些测试数据
        tab.channel_usage = {
            6: {'count': 5, 'weight': 3.2},
            11: {'count': 3, 'weight': 1.5}
        }
        return tab
    
    @pytest.fixture
    def mock_parent(self):
        return Mock()
    
    @pytest.fixture
    def mock_wifi_analyzer(self):
        analyzer = Mock()
        analyzer.scan_wifi_networks = Mock(return_value=[])
        return analyzer
    
    def test_get_channel_count_existing(self, channel_tab):
        """测试获取存在的信道计数"""
        count = channel_tab._get_channel_count('2.4GHz', 6)
        
        assert isinstance(count, int)
        assert count > 0
    
    def test_get_channel_count_nonexistent(self, channel_tab):
        """测试获取不存在的信道计数"""
        count = channel_tab._get_channel_count('2.4GHz', 1)
        
        assert isinstance(count, int)
        assert count == 0


@pytest.mark.skipif(not HAS_CHANNEL_ANALYSIS, reason="需要ChannelAnalysisTab模块")
class TestWiFiStandards:
    """WiFi标准定义测试"""
    
    def test_wifi_standards_structure(self):
        """测试WiFi标准定义结构"""
        standards = ChannelAnalysisTab.WIFI_STANDARDS
        
        assert isinstance(standards, dict)
        assert "WiFi 4" in standards
        assert "WiFi 5" in standards
        assert "WiFi 6" in standards
        assert "WiFi 6E" in standards
        assert "WiFi 7" in standards
    
    def test_wifi_standards_values(self):
        """测试WiFi标准对应的IEEE标准"""
        standards = ChannelAnalysisTab.WIFI_STANDARDS
        
        assert "802.11n" in standards["WiFi 4"]
        assert "802.11ac" in standards["WiFi 5"]
        assert "802.11ax" in standards["WiFi 6"]
        assert "802.11be" in standards["WiFi 7"]
@pytest.mark.skip(reason="需要真实Tkinter环境")


@pytest.mark.skipif(not HAS_CHANNEL_ANALYSIS, reason="需要ChannelAnalysisTab模块")
class TestEdgeCases:
    """边界情况测试"""
    
    @pytest.fixture
    def channel_tab(self, mock_parent, mock_wifi_analyzer):
        return ChannelAnalysisTab(mock_parent, mock_wifi_analyzer)
    
    @pytest.fixture
    def mock_parent(self):
        return Mock()
    
    @pytest.fixture
    def mock_wifi_analyzer(self):
        analyzer = Mock()
        analyzer.scan_wifi_networks = Mock(return_value=[])
        return analyzer
    
    def test_invalid_channel_number(self, channel_tab):
        """测试无效信道号"""
        # 负数信道
        info = channel_tab.get_wifi_protocol_info(-1, '2.4GHz')
        assert isinstance(info, dict)
        
        # 超大信道号
        info = channel_tab.get_wifi_protocol_info(999, '5GHz')
        assert isinstance(info, dict)
    
    def test_invalid_band(self, channel_tab):
        """测试无效频段"""
        info = channel_tab.get_wifi_protocol_info(6, 'InvalidBand')
        assert isinstance(info, dict)
    
    def test_empty_signal_string(self, channel_tab):
        """测试空信号字符串"""
        result = channel_tab._parse_signal_dbm("")
        assert isinstance(result, int)
    
    def test_none_bandwidth(self, channel_tab):
        """测试None带宽"""
        network = {'channel': 36}
        bandwidth = channel_tab._infer_bandwidth(network)
        assert isinstance(bandwidth, str)
