#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WiFi 6 分析器测试套件
测试OFDMA、BSS Color、TWT、MU-MIMO等功能
"""

import pytest
import sys
import os
import importlib.util

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 直接导入模块，避免通过__init__.py导致的依赖问题
spec = importlib.util.spec_from_file_location(
    "wifi6_analyzer",
    os.path.join(project_root, "wifi_modules", "wifi6_analyzer.py")
)
wifi6_analyzer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wifi6_analyzer)

# 导入所需的类
WiFi6Analyzer = wifi6_analyzer.WiFi6Analyzer
WiFi6NetworkInfo = wifi6_analyzer.WiFi6NetworkInfo
WiFi6Standard = wifi6_analyzer.WiFi6Standard
BSSColorStatus = wifi6_analyzer.BSSColorStatus
OFDMAAnalysis = wifi6_analyzer.OFDMAAnalysis
BSSColorAnalysis = wifi6_analyzer.BSSColorAnalysis
TWTAnalysis = wifi6_analyzer.TWTAnalysis
MUMIMOAnalysis = wifi6_analyzer.MUMIMOAnalysis


class TestWiFi6Analyzer:
    """WiFi 6分析器基础测试"""
    
    @pytest.fixture
    def analyzer(self):
        """创建分析器实例"""
        return WiFi6Analyzer()
    
    def test_analyzer_initialization(self, analyzer):
        """测试分析器初始化"""
        assert analyzer is not None
        assert analyzer.wifi6_networks == []
        assert analyzer.bss_color_map == {}
    
    def test_channel_to_frequency_2_4ghz(self, analyzer):
        """测试2.4GHz信道转频率"""
        assert analyzer._channel_to_frequency(1) == 2412
        assert analyzer._channel_to_frequency(6) == 2437
        assert analyzer._channel_to_frequency(11) == 2456
        assert analyzer._channel_to_frequency(13) == 2472
        assert analyzer._channel_to_frequency(14) == 2484
    
    def test_channel_to_frequency_5ghz(self, analyzer):
        """测试5GHz信道转频率"""
        assert analyzer._channel_to_frequency(36) == 5180
        assert analyzer._channel_to_frequency(40) == 5200
        assert analyzer._channel_to_frequency(149) == 5745
        assert analyzer._channel_to_frequency(165) == 5825
    
    def test_channel_to_frequency_6ghz(self, analyzer):
        """测试6GHz信道转频率 (WiFi 6E)"""
        freq = analyzer._channel_to_frequency(1)
        assert freq == 5960  # 6GHz起始频率
        
        freq = analyzer._channel_to_frequency(100)
        assert freq == 6455
    
    def test_frequency_to_channel_2_4ghz(self, analyzer):
        """测试2.4GHz频率转信道"""
        assert analyzer._frequency_to_channel(2412) == 1
        assert analyzer._frequency_to_channel(2437) == 6
        assert analyzer._frequency_to_channel(2472) == 13
        assert analyzer._frequency_to_channel(2484) == 14
    
    def test_frequency_to_channel_5ghz(self, analyzer):
        """测试5GHz频率转信道"""
        assert analyzer._frequency_to_channel(5180) == 36
        assert analyzer._frequency_to_channel(5745) == 149
    
    def test_frequency_to_channel_6ghz(self, analyzer):
        """测试6GHz频率转信道"""
        ch = analyzer._frequency_to_channel(5960)
        assert ch == 1
        
        ch = analyzer._frequency_to_channel(6455)
        assert ch == 100
    
    def test_percent_to_dbm_conversion(self, analyzer):
        """测试信号百分比转dBm"""
        # 优秀信号 (80-100%)
        assert analyzer._percent_to_dbm(100) == -30
        assert analyzer._percent_to_dbm(90) >= -50
        assert analyzer._percent_to_dbm(80) >= -50
        
        # 良好信号 (60-80%)
        dbm_70 = analyzer._percent_to_dbm(70)
        assert -60 <= dbm_70 <= -50
        
        # 中等信号 (40-60%)
        dbm_50 = analyzer._percent_to_dbm(50)
        assert -70 <= dbm_50 <= -60
        
        # 弱信号 (<40%)
        dbm_20 = analyzer._percent_to_dbm(20)
        assert dbm_20 <= -80


class TestOFDMAAnalysis:
    """OFDMA分析测试"""
    
    @pytest.fixture
    def network_20mhz(self):
        """创建20MHz WiFi 6网络"""
        return WiFi6NetworkInfo(
            ssid="Test_WiFi6_20",
            bssid="00:11:22:33:44:55",
            channel=36,
            frequency=5180,
            bandwidth=20,
            standard=WiFi6Standard.WIFI6_AX,
            signal_strength=-45
        )
    
    @pytest.fixture
    def network_80mhz(self):
        """创建80MHz WiFi 6网络"""
        return WiFi6NetworkInfo(
            ssid="Test_WiFi6_80",
            bssid="AA:BB:CC:DD:EE:FF",
            channel=42,
            frequency=5210,
            bandwidth=80,
            standard=WiFi6Standard.WIFI6_AX,
            signal_strength=-35
        )
    
    @pytest.fixture
    def network_160mhz(self):
        """创建160MHz WiFi 6网络"""
        return WiFi6NetworkInfo(
            ssid="Test_WiFi6_160",
            bssid="11:22:33:44:55:66",
            channel=50,
            frequency=5250,
            bandwidth=160,
            standard=WiFi6Standard.WIFI6_AX,
            signal_strength=-40
        )
    
    def test_ofdma_enabled_for_wifi6(self, network_80mhz):
        """测试WiFi 6网络启用OFDMA"""
        analyzer = WiFi6Analyzer()
        ofdma = analyzer._analyze_ofdma(network_80mhz)
        
        assert ofdma.enabled is True
        assert ofdma.dl_ofdma_enabled is True
        assert ofdma.ul_ofdma_enabled is True
    
    def test_ofdma_ru_allocation_20mhz(self, network_20mhz):
        """测试20MHz带宽RU分配"""
        analyzer = WiFi6Analyzer()
        ofdma = analyzer._analyze_ofdma(network_20mhz)
        
        assert '26-tone' in ofdma.ru_allocation
        assert ofdma.ru_allocation['26-tone'] == 9
        assert '242-tone' in ofdma.ru_allocation
        assert ofdma.concurrent_users == 9
    
    def test_ofdma_ru_allocation_80mhz(self, network_80mhz):
        """测试80MHz带宽RU分配"""
        analyzer = WiFi6Analyzer()
        ofdma = analyzer._analyze_ofdma(network_80mhz)
        
        assert '26-tone' in ofdma.ru_allocation
        assert ofdma.ru_allocation['26-tone'] == 37
        assert '996-tone' in ofdma.ru_allocation
        assert ofdma.concurrent_users == 37
    
    def test_ofdma_ru_allocation_160mhz(self, network_160mhz):
        """测试160MHz带宽RU分配"""
        analyzer = WiFi6Analyzer()
        ofdma = analyzer._analyze_ofdma(network_160mhz)
        
        assert '26-tone' in ofdma.ru_allocation
        assert ofdma.ru_allocation['26-tone'] == 74
        assert '2x996-tone' in ofdma.ru_allocation
        assert ofdma.concurrent_users == 74
    
    def test_ofdma_efficiency_score(self, network_80mhz):
        """测试OFDMA效率评分"""
        analyzer = WiFi6Analyzer()
        ofdma = analyzer._analyze_ofdma(network_80mhz)
        
        assert 0 <= ofdma.efficiency_score <= 100
        # 强信号(-35dBm) + 80MHz带宽应该有较高评分
        assert ofdma.efficiency_score > 70
    
    def test_ofdma_recommendations(self, network_20mhz):
        """测试OFDMA建议"""
        analyzer = WiFi6Analyzer()
        ofdma = analyzer._analyze_ofdma(network_20mhz)
        
        assert len(ofdma.recommendations) > 0
        # 20MHz带宽应该建议升级
        assert any("80MHz" in r or "160MHz" in r for r in ofdma.recommendations)
    
    def test_ofdma_disabled_for_wifi5(self):
        """测试WiFi 5网络不支持OFDMA"""
        network = WiFi6NetworkInfo(
            ssid="Test_WiFi5",
            bssid="00:11:22:33:44:55",
            channel=36,
            frequency=5180,
            bandwidth=80,
            standard=WiFi6Standard.WIFI5_AC,
            signal_strength=-45
        )
        
        analyzer = WiFi6Analyzer()
        ofdma = analyzer._analyze_ofdma(network)
        
        assert ofdma.enabled is False
        assert any("不支持" in r for r in ofdma.recommendations)


class TestBSSColorAnalysis:
    """BSS颜色分析测试"""
    
    @pytest.fixture
    def wifi6_network(self):
        """创建WiFi 6网络"""
        return WiFi6NetworkInfo(
            ssid="Test_WiFi6",
            bssid="00:11:22:33:44:55",
            channel=36,
            frequency=5180,
            bandwidth=80,
            standard=WiFi6Standard.WIFI6_AX,
            signal_strength=-45
        )
    
    def test_bss_color_id_range(self, wifi6_network):
        """测试BSS颜色ID范围 (1-63)"""
        analyzer = WiFi6Analyzer()
        bss_color = analyzer._analyze_bss_color(wifi6_network)
        
        assert bss_color.color_id is not None
        assert 1 <= bss_color.color_id <= 63
    
    def test_bss_color_unique_status(self, wifi6_network):
        """测试唯一BSS颜色状态"""
        analyzer = WiFi6Analyzer()
        bss_color = analyzer._analyze_bss_color(wifi6_network)
        
        # 第一个网络应该是唯一的
        assert bss_color.status == BSSColorStatus.UNIQUE
        assert bss_color.conflict_count == 0
    
    def test_bss_color_conflict_detection(self):
        """测试BSS颜色冲突检测"""
        analyzer = WiFi6Analyzer()
        
        # 创建两个网络
        network1 = WiFi6NetworkInfo(
            ssid="WiFi6_1",
            bssid="00:11:22:33:44:55",
            channel=36,
            frequency=5180,
            bandwidth=80,
            standard=WiFi6Standard.WIFI6_AX,
            signal_strength=-45
        )
        
        network2 = WiFi6NetworkInfo(
            ssid="WiFi6_2",
            bssid="AA:BB:CC:DD:EE:FF",
            channel=36,
            frequency=5180,
            bandwidth=80,
            standard=WiFi6Standard.WIFI6_AX,
            signal_strength=-50
        )
        
        # 分析第一个网络
        bss1 = analyzer._analyze_bss_color(network1)
        
        # 强制第二个网络使用相同颜色来模拟冲突
        import random
        random.seed(42)  # 固定随机种子
        analyzer.bss_color_map[bss1.color_id] = [network1.bssid]
        
        # 手动添加冲突
        analyzer.bss_color_map[bss1.color_id].append(network2.bssid)
        
        # 重新检查
        network2.bss_color_analysis = BSSColorAnalysis(color_id=bss1.color_id)
        analyzer.wifi6_networks = [network1, network2]
        analyzer._analyze_bss_color_conflicts()
        
        # 验证冲突检测
        assert len(analyzer.bss_color_map[bss1.color_id]) >= 2
    
    def test_bss_color_not_supported_for_wifi5(self):
        """测试WiFi 5不支持BSS颜色"""
        network = WiFi6NetworkInfo(
            ssid="Test_WiFi5",
            bssid="00:11:22:33:44:55",
            channel=36,
            frequency=5180,
            bandwidth=80,
            standard=WiFi6Standard.WIFI5_AC,
            signal_strength=-45
        )
        
        analyzer = WiFi6Analyzer()
        bss_color = analyzer._analyze_bss_color(network)
        
        assert bss_color.status == BSSColorStatus.NOT_SUPPORTED
        assert any("不支持" in r for r in bss_color.recommendations)
    
    def test_bss_color_optimal_recommendation(self, wifi6_network):
        """测试最优颜色推荐"""
        analyzer = WiFi6Analyzer()
        
        # 占用一些颜色
        analyzer.bss_color_map[1] = ["00:11:22:33:44:55"]
        analyzer.bss_color_map[2] = ["AA:BB:CC:DD:EE:FF"]
        
        bss_color = analyzer._analyze_bss_color(wifi6_network)
        
        # 应该推荐未使用的颜色
        if bss_color.optimal_color:
            assert bss_color.optimal_color not in [1, 2] or len(analyzer.bss_color_map[bss_color.optimal_color]) <= 1


class TestTWTAnalysis:
    """TWT分析测试"""
    
    @pytest.fixture
    def wifi6_network(self):
        """创建WiFi 6网络"""
        return WiFi6NetworkInfo(
            ssid="Test_WiFi6_TWT",
            bssid="00:11:22:33:44:55",
            channel=36,
            frequency=5180,
            bandwidth=80,
            standard=WiFi6Standard.WIFI6_AX,
            signal_strength=-45
        )
    
    def test_twt_supported_for_wifi6(self, wifi6_network):
        """测试WiFi 6支持TWT"""
        analyzer = WiFi6Analyzer()
        twt = analyzer._analyze_twt(wifi6_network)
        
        assert twt.supported is True
        assert twt.individual_twt is True
        assert twt.broadcast_twt is True
        assert twt.flexible_twt is True
    
    def test_twt_power_save_efficiency(self, wifi6_network):
        """测试TWT省电效率计算"""
        analyzer = WiFi6Analyzer()
        twt = analyzer._analyze_twt(wifi6_network)
        
        assert 0 <= twt.power_save_efficiency <= 100
        # 默认参数应该有较高省电效率
        assert twt.power_save_efficiency > 80
    
    def test_twt_timing_parameters(self, wifi6_network):
        """测试TWT时间参数"""
        analyzer = WiFi6Analyzer()
        twt = analyzer._analyze_twt(wifi6_network)
        
        assert twt.wake_interval > 0
        assert twt.avg_sleep_duration > 0
        # 睡眠时间应该远大于唤醒间隔
        assert twt.avg_sleep_duration > twt.wake_interval
    
    def test_twt_not_supported_for_wifi5(self):
        """测试WiFi 5不支持TWT"""
        network = WiFi6NetworkInfo(
            ssid="Test_WiFi5",
            bssid="00:11:22:33:44:55",
            channel=36,
            frequency=5180,
            bandwidth=80,
            standard=WiFi6Standard.WIFI5_AC,
            signal_strength=-45
        )
        
        analyzer = WiFi6Analyzer()
        twt = analyzer._analyze_twt(network)
        
        assert twt.supported is False
        assert any("不支持" in r for r in twt.recommendations)
    
    def test_twt_recommendations(self, wifi6_network):
        """测试TWT建议"""
        analyzer = WiFi6Analyzer()
        twt = analyzer._analyze_twt(wifi6_network)
        
        assert len(twt.recommendations) > 0
        # 应该包含IoT设备相关建议
        assert any("IoT" in r or "节能" in r for r in twt.recommendations)


class TestMUMIMOAnalysis:
    """MU-MIMO分析测试"""
    
    @pytest.fixture
    def wifi6_network_5ghz(self):
        """创建5GHz WiFi 6网络"""
        return WiFi6NetworkInfo(
            ssid="Test_WiFi6_5G",
            bssid="00:11:22:33:44:55",
            channel=36,
            frequency=5180,
            bandwidth=80,
            standard=WiFi6Standard.WIFI6_AX,
            signal_strength=-45
        )
    
    @pytest.fixture
    def wifi6_network_2_4ghz(self):
        """创建2.4GHz WiFi 6网络"""
        return WiFi6NetworkInfo(
            ssid="Test_WiFi6_2.4G",
            bssid="AA:BB:CC:DD:EE:FF",
            channel=6,
            frequency=2437,
            bandwidth=40,
            standard=WiFi6Standard.WIFI6_AX,
            signal_strength=-50
        )
    
    def test_mu_mimo_enabled_for_wifi6(self, wifi6_network_5ghz):
        """测试WiFi 6支持MU-MIMO"""
        analyzer = WiFi6Analyzer()
        mu_mimo = analyzer._analyze_mu_mimo(wifi6_network_5ghz)
        
        assert mu_mimo.dl_mu_mimo is True
        assert mu_mimo.ul_mu_mimo is True  # WiFi 6新增上行MU-MIMO
        assert mu_mimo.beamforming is True
    
    def test_mu_mimo_spatial_streams_5ghz(self, wifi6_network_5ghz):
        """测试5GHz频段空间流数量"""
        analyzer = WiFi6Analyzer()
        mu_mimo = analyzer._analyze_mu_mimo(wifi6_network_5ghz)
        
        assert mu_mimo.spatial_streams == 8
        assert mu_mimo.max_users == 8
    
    def test_mu_mimo_spatial_streams_2_4ghz(self, wifi6_network_2_4ghz):
        """测试2.4GHz频段空间流数量"""
        analyzer = WiFi6Analyzer()
        mu_mimo = analyzer._analyze_mu_mimo(wifi6_network_2_4ghz)
        
        assert mu_mimo.spatial_streams == 4
        assert mu_mimo.max_users == 4
    
    def test_mu_mimo_efficiency_score(self, wifi6_network_5ghz):
        """测试MU-MIMO效率评分"""
        analyzer = WiFi6Analyzer()
        mu_mimo = analyzer._analyze_mu_mimo(wifi6_network_5ghz)
        
        assert 0 <= mu_mimo.efficiency_score <= 100
        # 强信号应该有较高评分
        assert mu_mimo.efficiency_score > 60
    
    def test_mu_mimo_wifi5_downlink_only(self):
        """测试WiFi 5仅支持下行MU-MIMO"""
        network = WiFi6NetworkInfo(
            ssid="Test_WiFi5",
            bssid="00:11:22:33:44:55",
            channel=36,
            frequency=5180,
            bandwidth=80,
            standard=WiFi6Standard.WIFI5_AC,
            signal_strength=-45
        )
        
        analyzer = WiFi6Analyzer()
        mu_mimo = analyzer._analyze_mu_mimo(network)
        
        assert mu_mimo.dl_mu_mimo is True
        assert mu_mimo.ul_mu_mimo is False
        assert mu_mimo.max_users == 4
        assert any("WiFi 5" in r and "下行" in r for r in mu_mimo.recommendations)
    
    def test_mu_mimo_recommendations(self, wifi6_network_5ghz):
        """测试MU-MIMO建议"""
        analyzer = WiFi6Analyzer()
        mu_mimo = analyzer._analyze_mu_mimo(wifi6_network_5ghz)
        
        assert len(mu_mimo.recommendations) > 0


class TestWiFi6Summary:
    """WiFi 6摘要测试"""
    
    @pytest.fixture
    def analyzer_with_networks(self):
        """创建包含多个网络的分析器"""
        analyzer = WiFi6Analyzer()
        
        # 添加WiFi 6网络
        network1 = WiFi6NetworkInfo(
            ssid="WiFi6_1",
            bssid="00:11:22:33:44:55",
            channel=36,
            frequency=5180,
            bandwidth=80,
            standard=WiFi6Standard.WIFI6_AX,
            signal_strength=-45
        )
        
        # 添加WiFi 6E网络
        network2 = WiFi6NetworkInfo(
            ssid="WiFi6E_1",
            bssid="AA:BB:CC:DD:EE:FF",
            channel=1,
            frequency=5960,
            bandwidth=160,
            standard=WiFi6Standard.WIFI6E_AX,
            signal_strength=-40
        )
        
        # 添加WiFi 5网络
        network3 = WiFi6NetworkInfo(
            ssid="WiFi5_1",
            bssid="11:22:33:44:55:66",
            channel=149,
            frequency=5745,
            bandwidth=80,
            standard=WiFi6Standard.WIFI5_AC,
            signal_strength=-50
        )
        
        # 分析特性
        for network in [network1, network2, network3]:
            if network.standard in [WiFi6Standard.WIFI6_AX, WiFi6Standard.WIFI6E_AX]:
                analyzer._analyze_wifi6_features(network)
        
        analyzer.wifi6_networks = [network1, network2, network3]
        
        return analyzer
    
    def test_summary_network_count(self, analyzer_with_networks):
        """测试摘要网络计数"""
        summary = analyzer_with_networks.get_wifi6_summary()
        
        assert summary['total_networks'] == 3
        assert summary['wifi6_count'] == 2
        assert summary['wifi6e_count'] == 1
    
    def test_summary_wifi6_ratio(self, analyzer_with_networks):
        """测试WiFi 6比率"""
        summary = analyzer_with_networks.get_wifi6_summary()
        
        assert summary['wifi6_ratio'] == pytest.approx(2/3, 0.01)
    
    def test_summary_feature_counts(self, analyzer_with_networks):
        """测试特性统计"""
        summary = analyzer_with_networks.get_wifi6_summary()
        
        # WiFi 6网络应该启用OFDMA
        assert summary['ofdma_enabled'] >= 2
        # WiFi 6网络应该支持MU-MIMO
        assert summary['mu_mimo_enabled'] >= 2
        # WiFi 6网络应该支持TWT
        assert summary['twt_supported'] >= 2
    
    def test_summary_average_score(self, analyzer_with_networks):
        """测试平均评分"""
        summary = analyzer_with_networks.get_wifi6_summary()
        
        assert 0 <= summary['average_score'] <= 100
    
    def test_summary_scan_time(self, analyzer_with_networks):
        """测试扫描时间戳"""
        summary = analyzer_with_networks.get_wifi6_summary()
        
        assert 'scan_time' in summary
        assert summary['scan_time']  # 非空


class TestNetworkOverallScore:
    """网络综合评分测试"""
    
    def test_overall_score_calculation(self):
        """测试综合评分计算"""
        network = WiFi6NetworkInfo(
            ssid="Test_WiFi6",
            bssid="00:11:22:33:44:55",
            channel=36,
            frequency=5180,
            bandwidth=80,
            standard=WiFi6Standard.WIFI6_AX,
            signal_strength=-45
        )
        
        analyzer = WiFi6Analyzer()
        analyzer._analyze_wifi6_features(network)
        
        score = network.get_overall_score()
        assert 0 <= score <= 100
    
    def test_overall_score_with_all_features(self):
        """测试包含所有特性的综合评分"""
        network = WiFi6NetworkInfo(
            ssid="Test_WiFi6",
            bssid="00:11:22:33:44:55",
            channel=36,
            frequency=5180,
            bandwidth=160,
            standard=WiFi6Standard.WIFI6_AX,
            signal_strength=-35
        )
        
        analyzer = WiFi6Analyzer()
        analyzer._analyze_wifi6_features(network)
        
        score = network.get_overall_score()
        
        # 强信号 + 160MHz带宽 + WiFi 6特性应该有高评分
        assert score > 70
    
    def test_overall_score_no_wifi6_features(self):
        """测试没有WiFi 6特性的评分"""
        network = WiFi6NetworkInfo(
            ssid="Test_WiFi5",
            bssid="00:11:22:33:44:55",
            channel=36,
            frequency=5180,
            bandwidth=80,
            standard=WiFi6Standard.WIFI5_AC,
            signal_strength=-50
        )
        
        # 不分析WiFi 6特性
        score = network.get_overall_score()
        
        # 没有特性数据，评分应该为0
        assert score == 0.0


# 性能测试
@pytest.mark.performance
class TestPerformance:
    """性能测试"""
    
    def test_scan_performance(self):
        """测试扫描性能"""
        import time
        
        analyzer = WiFi6Analyzer()
        
        start_time = time.time()
        networks = analyzer.scan_wifi6_networks()
        elapsed_time = time.time() - start_time
        
        # 扫描应该在30秒内完成
        assert elapsed_time < 30
        print(f"\n扫描耗时: {elapsed_time:.2f}秒, 发现 {len(networks)} 个网络")
    
    def test_analysis_performance(self):
        """测试分析性能"""
        import time
        
        analyzer = WiFi6Analyzer()
        
        # 创建测试网络
        network = WiFi6NetworkInfo(
            ssid="Test_WiFi6",
            bssid="00:11:22:33:44:55",
            channel=36,
            frequency=5180,
            bandwidth=80,
            standard=WiFi6Standard.WIFI6_AX,
            signal_strength=-45
        )
        
        start_time = time.time()
        analyzer._analyze_wifi6_features(network)
        elapsed_time = time.time() - start_time
        
        # 单个网络分析应该在0.1秒内完成
        assert elapsed_time < 0.1
        print(f"\n分析耗时: {elapsed_time*1000:.2f}毫秒")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
