#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WiFi 6/6E 高级分析器
支持OFDMA、BSS Color、TWT、MU-MIMO等WiFi 6特性分析
v2.0: 使用统一WiFi扫描接口
"""

import re
import platform
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from enum import Enum

# 导入核心WiFi分析器和工具函数
from core.wifi_analyzer import WiFiAnalyzer
from core.utils import channel_to_frequency, frequency_to_channel, percent_to_dbm

# Windows下隐藏cmd窗口
if platform.system().lower() == "windows":
    CREATE_NO_WINDOW = 0x08000000
else:
    CREATE_NO_WINDOW = 0


class WiFi6Standard(Enum):
    """WiFi 6标准枚举"""
    WIFI6_AX = "802.11ax (WiFi 6)"
    WIFI6E_AX = "802.11ax (WiFi 6E)"
    WIFI5_AC = "802.11ac (WiFi 5)"
    WIFI4_N = "802.11n (WiFi 4)"
    LEGACY = "Legacy (a/b/g)"


class BSSColorStatus(Enum):
    """BSS颜色状态"""
    UNIQUE = "唯一 (无冲突)"
    CONFLICT = "冲突"
    NOT_SUPPORTED = "不支持"
    UNKNOWN = "未知"


@dataclass
class OFDMAAnalysis:
    """OFDMA效率分析结果"""
    enabled: bool = False
    ru_allocation: Dict[str, int] = field(default_factory=dict)  # RU分配统计
    efficiency_score: float = 0.0  # 效率评分 0-100
    concurrent_users: int = 0  # 支持的并发用户数
    ul_ofdma_enabled: bool = False  # 上行OFDMA
    dl_ofdma_enabled: bool = False  # 下行OFDMA
    recommendations: List[str] = field(default_factory=list)


@dataclass
class BSSColorAnalysis:
    """BSS颜色分析结果"""
    color_id: Optional[int] = None  # 1-63
    status: BSSColorStatus = BSSColorStatus.UNKNOWN
    conflict_count: int = 0
    conflicting_bssids: List[str] = field(default_factory=list)
    optimal_color: Optional[int] = None
    recommendations: List[str] = field(default_factory=list)


@dataclass
class TWTAnalysis:
    """TWT (目标唤醒时间) 分析结果"""
    supported: bool = False
    individual_twt: bool = False  # 个体TWT
    broadcast_twt: bool = False  # 广播TWT
    flexible_twt: bool = False  # 灵活TWT
    power_save_efficiency: float = 0.0  # 省电效率评分 0-100
    avg_sleep_duration: float = 0.0  # 平均睡眠时长(ms)
    wake_interval: float = 0.0  # 唤醒间隔(ms)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class MUMIMOAnalysis:
    """MU-MIMO分析结果"""
    dl_mu_mimo: bool = False  # 下行MU-MIMO
    ul_mu_mimo: bool = False  # 上行MU-MIMO (WiFi 6新增)
    max_users: int = 0  # 最大并发用户数
    spatial_streams: int = 0  # 空间流数量
    beamforming: bool = False  # 波束成形
    efficiency_score: float = 0.0  # 效率评分 0-100
    recommendations: List[str] = field(default_factory=list)


@dataclass
class WiFi6NetworkInfo:
    """WiFi 6网络信息"""
    ssid: str
    bssid: str
    channel: int
    frequency: int  # MHz
    bandwidth: int  # 20/40/80/160 MHz
    standard: WiFi6Standard
    signal_strength: int  # dBm
    
    # WiFi 6特性
    ofdma_analysis: Optional[OFDMAAnalysis] = None
    bss_color_analysis: Optional[BSSColorAnalysis] = None
    twt_analysis: Optional[TWTAnalysis] = None
    mu_mimo_analysis: Optional[MUMIMOAnalysis] = None
    
    # 性能指标
    max_data_rate: int = 0  # Mbps
    guard_interval: str = "Unknown"  # 0.8us/1.6us/3.2us
    spatial_streams: int = 1
    
    # 扩展信息
    he_capabilities: Dict[str, bool] = field(default_factory=dict)
    encryption: str = "Unknown"
    vendor: str = "Unknown"
    
    def get_overall_score(self) -> float:
        """计算综合评分"""
        scores = []
        
        if self.ofdma_analysis:
            scores.append(self.ofdma_analysis.efficiency_score)
        if self.mu_mimo_analysis:
            scores.append(self.mu_mimo_analysis.efficiency_score)
        if self.twt_analysis:
            scores.append(self.twt_analysis.power_save_efficiency)
        
        # BSS颜色评分
        if self.bss_color_analysis:
            if self.bss_color_analysis.status == BSSColorStatus.UNIQUE:
                scores.append(100.0)
            elif self.bss_color_analysis.status == BSSColorStatus.CONFLICT:
                scores.append(max(0, 100 - self.bss_color_analysis.conflict_count * 20))
        
        return sum(scores) / len(scores) if scores else 0.0


class WiFi6Analyzer:
    """WiFi 6/6E 高级分析器"""
    
    # WiFi 6E频段范围 (6GHz)
    WIFI6E_CHANNELS = list(range(1, 234))  # 6GHz: 5.925-7.125 GHz
    
    # HE (High Efficiency) 能力标志位
    HE_CAPABILITIES = {
        'HE_MAC_CAPS': [
            '+HTC HE Support',
            'TWT Requester',
            'TWT Responder',
            'Fragmentation Support',
            'Multi-BSSID',
            'BSS Color',
            'OM Control',
            'OFDMA RA',
            'A-MSDU in A-MPDU',
            'Multi-TID Aggregation',
        ],
        'HE_PHY_CAPS': [
            'Dual Band',
            'Channel Width Set',
            'Punctured Preamble Rx',
            'Device Class',
            'LDPC Coding',
            'HE SU PPDU 1x HE-LTF',
            'HE SU PPDU 4x HE-LTF',
            'NDP with 4x HE-LTF',
            'STBC Tx',
            'STBC Rx',
            'Doppler Tx',
            'Doppler Rx',
            'Full BW UL MU-MIMO',
            'Partial BW UL MU-MIMO',
            'DCM Max Constellation',
            'Partial BW Extended Range',
            'PPE Threshold Present',
            'Power Boost Factor Support',
            'HE SU PPDU & HE MU PPDU 4x HE-LTF',
            'Max Nc',
            'STBC Tx >80 MHz',
            'STBC Rx >80 MHz',
            'HE ER SU PPDU 4x HE-LTF',
            '20MHz in 40MHz HE PPDU',
            '20MHz in 160/80+80 MHz HE PPDU',
            '80MHz in 160/80+80 MHz HE PPDU',
            'HE ER SU PPDU 1x HE-LTF',
            'Midamble Rx Max NSTS',
            'NDP with 4x HE-LTF',
            'DCM Max NSS',
        ],
        'HE_MCS_NSS': [
            'Rx HE-MCS Map ≤80 MHz',
            'Tx HE-MCS Map ≤80 MHz',
            'Rx HE-MCS Map 160 MHz',
            'Tx HE-MCS Map 160 MHz',
            'Rx HE-MCS Map 80+80 MHz',
            'Tx HE-MCS Map 80+80 MHz',
        ]
    }
    
    def __init__(self):
        """初始化WiFi 6分析器"""
        self.system = platform.system().lower()
        self.wifi6_networks: List[WiFi6NetworkInfo] = []
        self.bss_color_map: Dict[int, List[str]] = {}  # color_id -> [bssid1, bssid2, ...]
        
        # ✅ v2.0: 使用统一WiFi扫描接口
        self.wifi_analyzer = WiFiAnalyzer()
        
    def scan_wifi6_networks(self) -> List[WiFi6NetworkInfo]:
        """扫描WiFi 6/6E网络 - v2.0: 使用统一扫描接口"""
        # ✅ 使用核心扫描API获取所有网络
        all_networks = self.wifi_analyzer.scan_wifi_networks(force_refresh=True)
        
        # 转换为WiFi6NetworkInfo格式
        wifi6_networks = []
        for net in all_networks:
            # 识别WiFi标准
            standard = self._identify_wifi6_standard(net)
            
            # 只处理WiFi 6/6E网络（也可保留WiFi 5/4用于对比）
            wifi6_info = WiFi6NetworkInfo(
                ssid=net.get('ssid', ''),
                bssid=net.get('bssid', ''),
                channel=net.get('channel', 0),
                frequency=channel_to_frequency(net.get('channel', 0)),
                bandwidth=self._estimate_bandwidth(net),
                standard=standard,
                signal_strength=net.get('signal_dbm', -100)
            )
            
            # 分析WiFi 6特性（仅对WiFi 6/6E网络）
            if standard in [WiFi6Standard.WIFI6_AX, WiFi6Standard.WIFI6E_AX]:
                self._analyze_wifi6_features(wifi6_info)
            
            wifi6_networks.append(wifi6_info)
        
        self.wifi6_networks = wifi6_networks
        self._analyze_bss_color_conflicts()
        
        return wifi6_networks
    
    def _identify_wifi6_standard(self, network: Dict) -> WiFi6Standard:
        """识别WiFi标准"""
        wifi_standard = network.get('wifi_standard', 'N/A')
        channel = network.get('channel', 0)
        
        # 确保channel是整数类型
        try:
            channel = int(channel)
        except (ValueError, TypeError):
            channel = 0
        
        # WiFi 6E: 6GHz频段 (信道1-233)
        if channel >= 1 and channel <= 233 and channel not in range(1, 15) and channel not in range(36, 166):
            return WiFi6Standard.WIFI6E_AX
        
        # 根据协议标识
        if '802.11ax' in wifi_standard or 'WiFi 6' in wifi_standard:
            if channel >= 1 and channel <= 233 and channel not in range(1, 15) and channel not in range(36, 166):
                return WiFi6Standard.WIFI6E_AX
            return WiFi6Standard.WIFI6_AX
        elif '802.11ac' in wifi_standard or 'WiFi 5' in wifi_standard:
            return WiFi6Standard.WIFI5_AC
        elif '802.11n' in wifi_standard or 'WiFi 4' in wifi_standard:
            return WiFi6Standard.WIFI4_N
        else:
            return WiFi6Standard.LEGACY
    
    def _estimate_bandwidth(self, network: Dict) -> int:
        """估算带宽"""
        bandwidth = network.get('bandwidth', 0)
        if bandwidth:
            try:
                # 如果是字符串，尝试提取数字
                if isinstance(bandwidth, str):
                    match = re.search(r'(\d+)', bandwidth)
                    if match:
                        return int(match.group(1))
                return int(bandwidth)
            except:
                pass
        
        # 根据频段和标准估算
        channel = network.get('channel', 0)
        wifi_standard = network.get('wifi_standard', '')
        
        # WiFi 6 默认至少80MHz
        if '802.11ax' in wifi_standard:
            if channel >= 36:  # 5GHz/6GHz
                return 80
            else:  # 2.4GHz
                return 40
        # WiFi 5 默认80MHz
        elif '802.11ac' in wifi_standard:
            return 80
        # WiFi 4 默认40MHz
        elif '802.11n' in wifi_standard:
            return 40
        
        return 20  # 默认20MHz
    
    # ❌ v2.0: 频率/信道转换方法已迁移到core.utils
    # 使用: from core.utils import channel_to_frequency, frequency_to_channel
    
    # ❌ v2.0: 删除平台特定的扫描方法，已由统一接口替代
    # _scan_windows(), _scan_linux(), _scan_macos() 方法已移除
    
    def _analyze_wifi6_features_old(self) -> None:
        """❌ 旧版：通过平台特定命令分析WiFi 6特性（已废弃）
        
        v2.0注释：
        原_scan_windows(), _scan_linux(), _scan_macos()方法（约200行）已被删除。
        现在使用core.wifi_analyzer.WiFiAnalyzer().scan_wifi_networks()统一接口，
        大幅简化代码并提高跨平台兼容性。
        """
        pass
    
    def _analyze_wifi6_features(self, network: WiFi6NetworkInfo):
        """分析WiFi 6特性"""
        # OFDMA分析
        network.ofdma_analysis = self._analyze_ofdma(network)
        
        # BSS颜色分析
        network.bss_color_analysis = self._analyze_bss_color(network)
        
        # TWT分析
        network.twt_analysis = self._analyze_twt(network)
        
        # MU-MIMO分析
        network.mu_mimo_analysis = self._analyze_mu_mimo(network)
        
        # HE能力
        network.he_capabilities = self._detect_he_capabilities(network)
    
    def _analyze_ofdma(self, network: WiFi6NetworkInfo) -> OFDMAAnalysis:
        """分析OFDMA特性"""
        analysis = OFDMAAnalysis()
        
        # 模拟OFDMA检测 (实际需要从驱动获取)
        # 这里基于信道带宽和标准进行估算
        if network.standard == WiFi6Standard.WIFI6_AX:
            analysis.enabled = True
            analysis.dl_ofdma_enabled = True
            analysis.ul_ofdma_enabled = True  # WiFi 6支持上行OFDMA
            
            # 根据带宽计算RU分配
            bandwidth = network.bandwidth if network.bandwidth > 0 else 80
            
            if bandwidth == 20:
                analysis.ru_allocation = {'26-tone': 9, '52-tone': 4, '106-tone': 2, '242-tone': 1}
                analysis.concurrent_users = 9
            elif bandwidth == 40:
                analysis.ru_allocation = {'26-tone': 18, '52-tone': 8, '106-tone': 4, '484-tone': 1}
                analysis.concurrent_users = 18
            elif bandwidth == 80:
                analysis.ru_allocation = {'26-tone': 37, '52-tone': 16, '106-tone': 8, '996-tone': 1}
                analysis.concurrent_users = 37
            elif bandwidth >= 160:
                analysis.ru_allocation = {'26-tone': 74, '52-tone': 32, '106-tone': 16, '2x996-tone': 1}
                analysis.concurrent_users = 74
            
            # 计算效率评分
            signal_quality = (network.signal_strength + 100) / 70 * 100  # -30dBm=100, -100dBm=0
            bandwidth_factor = min(bandwidth / 160, 1.0)
            analysis.efficiency_score = min(signal_quality * bandwidth_factor, 100)
            
            # 建议
            if analysis.efficiency_score < 60:
                analysis.recommendations.append("信号强度偏弱，建议靠近AP或增加AP数量")
            if bandwidth < 80:
                analysis.recommendations.append(f"当前带宽{bandwidth}MHz，建议使用80MHz或160MHz以提升OFDMA效率")
            if analysis.concurrent_users > 20:
                analysis.recommendations.append(f"支持{analysis.concurrent_users}个并发用户，适合高密度环境")
        else:
            analysis.enabled = False
            analysis.recommendations.append("该AP不支持OFDMA，建议升级到WiFi 6")
        
        return analysis
    
    def _analyze_bss_color(self, network: WiFi6NetworkInfo) -> BSSColorAnalysis:
        """分析BSS颜色"""
        analysis = BSSColorAnalysis()
        
        if network.standard == WiFi6Standard.WIFI6_AX:
            # 模拟BSS颜色检测 (实际需要从beacon帧中解析)
            # 这里随机分配一个颜色ID进行演示
            import random
            analysis.color_id = random.randint(1, 63)
            
            # 记录到颜色映射表
            if analysis.color_id not in self.bss_color_map:
                self.bss_color_map[analysis.color_id] = []
            self.bss_color_map[analysis.color_id].append(network.bssid)
            
            # 检测冲突 (简化版，实际需要检查同信道)
            if len(self.bss_color_map[analysis.color_id]) > 1:
                analysis.status = BSSColorStatus.CONFLICT
                analysis.conflict_count = len(self.bss_color_map[analysis.color_id]) - 1
                analysis.conflicting_bssids = [
                    bssid for bssid in self.bss_color_map[analysis.color_id] 
                    if bssid != network.bssid
                ]
                
                # 推荐最优颜色
                used_colors = set(self.bss_color_map.keys())
                available_colors = set(range(1, 64)) - used_colors
                if available_colors:
                    analysis.optimal_color = min(available_colors)
                    analysis.recommendations.append(
                        f"检测到BSS颜色冲突，建议更改为颜色{analysis.optimal_color}"
                    )
                else:
                    # 选择使用最少的颜色
                    analysis.optimal_color = min(
                        self.bss_color_map.keys(), 
                        key=lambda k: len(self.bss_color_map[k])
                    )
                    analysis.recommendations.append(
                        f"所有颜色都在使用，建议更改为使用最少的颜色{analysis.optimal_color}"
                    )
            else:
                analysis.status = BSSColorStatus.UNIQUE
                analysis.recommendations.append(f"BSS颜色{analysis.color_id}唯一，无冲突")
        else:
            analysis.status = BSSColorStatus.NOT_SUPPORTED
            analysis.recommendations.append("该AP不支持BSS颜色，建议升级到WiFi 6")
        
        return analysis
    
    def _analyze_twt(self, network: WiFi6NetworkInfo) -> TWTAnalysis:
        """分析TWT (Target Wake Time)"""
        analysis = TWTAnalysis()
        
        if network.standard == WiFi6Standard.WIFI6_AX:
            analysis.supported = True
            analysis.individual_twt = True
            analysis.broadcast_twt = True
            analysis.flexible_twt = True
            
            # 模拟TWT参数 (实际需要从AP获取)
            analysis.wake_interval = 100.0  # 100ms
            analysis.avg_sleep_duration = 900.0  # 900ms
            
            # 计算省电效率
            total_time = analysis.wake_interval + analysis.avg_sleep_duration
            sleep_ratio = analysis.avg_sleep_duration / total_time if total_time > 0 else 0
            analysis.power_save_efficiency = sleep_ratio * 100
            
            # 建议
            if analysis.power_save_efficiency > 80:
                analysis.recommendations.append(f"TWT省电效率{analysis.power_save_efficiency:.1f}%，优秀")
            elif analysis.power_save_efficiency > 60:
                analysis.recommendations.append(f"TWT省电效率{analysis.power_save_efficiency:.1f}%，良好")
            else:
                analysis.recommendations.append(
                    f"TWT省电效率{analysis.power_save_efficiency:.1f}%，建议调整唤醒间隔"
                )
            
            analysis.recommendations.append(
                f"支持个体/广播/灵活TWT，适合IoT设备节能"
            )
        else:
            analysis.supported = False
            analysis.recommendations.append("该AP不支持TWT，IoT设备省电效果有限")
        
        return analysis
    
    def _analyze_mu_mimo(self, network: WiFi6NetworkInfo) -> MUMIMOAnalysis:
        """分析MU-MIMO"""
        analysis = MUMIMOAnalysis()
        
        if network.standard == WiFi6Standard.WIFI6_AX:
            analysis.dl_mu_mimo = True  # WiFi 6支持下行
            analysis.ul_mu_mimo = True  # WiFi 6新增上行MU-MIMO
            analysis.beamforming = True
            
            # 根据频段估算空间流
            if network.frequency >= 5000:
                analysis.spatial_streams = 8  # 5GHz/6GHz通常支持8流
                analysis.max_users = 8
            else:
                analysis.spatial_streams = 4  # 2.4GHz通常支持4流
                analysis.max_users = 4
            
            # 计算效率评分
            signal_quality = (network.signal_strength + 100) / 70 * 100
            stream_factor = analysis.spatial_streams / 8
            analysis.efficiency_score = min(signal_quality * stream_factor, 100)
            
            # 建议
            analysis.recommendations.append(
                f"支持{analysis.spatial_streams}流 DL/UL MU-MIMO，最多{analysis.max_users}个并发用户"
            )
            if analysis.efficiency_score > 80:
                analysis.recommendations.append("MU-MIMO效率优秀，适合多用户场景")
            elif analysis.efficiency_score > 60:
                analysis.recommendations.append("MU-MIMO效率良好")
            else:
                analysis.recommendations.append("信号较弱，可能影响MU-MIMO性能")
        else:
            if network.standard == WiFi6Standard.WIFI5_AC:
                analysis.dl_mu_mimo = True  # WiFi 5支持下行
                analysis.ul_mu_mimo = False
                analysis.max_users = 4
                analysis.recommendations.append("WiFi 5仅支持下行MU-MIMO，建议升级到WiFi 6")
            else:
                analysis.dl_mu_mimo = False
                analysis.ul_mu_mimo = False
                analysis.recommendations.append("不支持MU-MIMO，建议升级到WiFi 6")
        
        return analysis
    
    def _detect_he_capabilities(self, network: WiFi6NetworkInfo) -> Dict[str, bool]:
        """检测HE能力"""
        capabilities = {}
        
        # 模拟HE能力检测 (实际需要解析beacon/probe response帧)
        if network.standard == WiFi6Standard.WIFI6_AX:
            # MAC层能力
            capabilities.update({
                '+HTC HE Support': True,
                'TWT Requester': True,
                'TWT Responder': True,
                'BSS Color': True,
                'OFDMA RA': True,
                'Multi-BSSID': True,
            })
            
            # PHY层能力
            capabilities.update({
                'Dual Band': network.frequency >= 5000,
                'LDPC Coding': True,
                'STBC Tx': True,
                'STBC Rx': True,
                'Full BW UL MU-MIMO': True,
                'Partial BW UL MU-MIMO': True,
                '20MHz in 40MHz HE PPDU': True,
                '80MHz in 160/80+80 MHz HE PPDU': network.bandwidth >= 160,
            })
        
        return capabilities
    
    def _analyze_bss_color_conflicts(self):
        """分析所有网络的BSS颜色冲突"""
        # 重新检查冲突
        for network in self.wifi6_networks:
            if network.bss_color_analysis and network.bss_color_analysis.color_id:
                color_id = network.bss_color_analysis.color_id
                if color_id in self.bss_color_map:
                    conflict_count = len(self.bss_color_map[color_id]) - 1
                    if conflict_count > 0:
                        network.bss_color_analysis.status = BSSColorStatus.CONFLICT
                        network.bss_color_analysis.conflict_count = conflict_count
                        network.bss_color_analysis.conflicting_bssids = [
                            bssid for bssid in self.bss_color_map[color_id]
                            if bssid != network.bssid
                        ]
    
    def get_wifi6_summary(self) -> Dict:
        """获取WiFi 6网络摘要"""
        total_networks = len(self.wifi6_networks)
        wifi6_count = sum(
            1 for n in self.wifi6_networks 
            if n.standard in [WiFi6Standard.WIFI6_AX, WiFi6Standard.WIFI6E_AX]
        )
        wifi6e_count = sum(
            1 for n in self.wifi6_networks 
            if n.standard == WiFi6Standard.WIFI6E_AX
        )
        
        ofdma_enabled = sum(
            1 for n in self.wifi6_networks 
            if n.ofdma_analysis and n.ofdma_analysis.enabled
        )
        
        mu_mimo_enabled = sum(
            1 for n in self.wifi6_networks 
            if n.mu_mimo_analysis and (n.mu_mimo_analysis.dl_mu_mimo or n.mu_mimo_analysis.ul_mu_mimo)
        )
        
        twt_supported = sum(
            1 for n in self.wifi6_networks 
            if n.twt_analysis and n.twt_analysis.supported
        )
        
        bss_color_conflicts = sum(
            1 for n in self.wifi6_networks 
            if n.bss_color_analysis and n.bss_color_analysis.status == BSSColorStatus.CONFLICT
        )
        
        avg_score = sum(n.get_overall_score() for n in self.wifi6_networks) / total_networks if total_networks > 0 else 0
        
        return {
            'total_networks': total_networks,
            'wifi6_count': wifi6_count,
            'wifi6e_count': wifi6e_count,
            'wifi6_ratio': wifi6_count / total_networks if total_networks > 0 else 0,
            'ofdma_enabled': ofdma_enabled,
            'mu_mimo_enabled': mu_mimo_enabled,
            'twt_supported': twt_supported,
            'bss_color_conflicts': bss_color_conflicts,
            'average_score': avg_score,
            'scan_time': datetime.now().isoformat()
        }


# ❌ v2.0: 以下静态方法已废弃，已迁移到core.utils模块
# 请使用:
#   from core.utils import percent_to_dbm, channel_to_frequency, frequency_to_channel
# 这些函数现在是全局工具函数，无需通过类调用


# 测试代码
if __name__ == "__main__":
    analyzer = WiFi6Analyzer()
    print("正在扫描WiFi 6/6E网络...")
    
    networks = analyzer.scan_wifi6_networks()
    
    print(f"\n发现 {len(networks)} 个网络")
    print("=" * 80)
    
    for i, network in enumerate(networks, 1):
        print(f"\n[{i}] {network.ssid} ({network.bssid})")
        print(f"    标准: {network.standard.value}")
        print(f"    信道: {network.channel} ({network.frequency} MHz)")
        print(f"    信号: {network.signal_strength} dBm")
        print(f"    综合评分: {network.get_overall_score():.1f}/100")
        
        if network.ofdma_analysis and network.ofdma_analysis.enabled:
            print(f"\n    [OFDMA]")
            print(f"      效率评分: {network.ofdma_analysis.efficiency_score:.1f}/100")
            print(f"      并发用户: {network.ofdma_analysis.concurrent_users}")
            print(f"      上行/下行: {network.ofdma_analysis.ul_ofdma_enabled}/{network.ofdma_analysis.dl_ofdma_enabled}")
        
        if network.bss_color_analysis and network.bss_color_analysis.color_id:
            print(f"\n    [BSS颜色]")
            print(f"      颜色ID: {network.bss_color_analysis.color_id}")
            print(f"      状态: {network.bss_color_analysis.status.value}")
            if network.bss_color_analysis.conflict_count > 0:
                print(f"      冲突数: {network.bss_color_analysis.conflict_count}")
        
        if network.twt_analysis and network.twt_analysis.supported:
            print(f"\n    [TWT]")
            print(f"      省电效率: {network.twt_analysis.power_save_efficiency:.1f}%")
            print(f"      唤醒间隔: {network.twt_analysis.wake_interval} ms")
        
        if network.mu_mimo_analysis and (network.mu_mimo_analysis.dl_mu_mimo or network.mu_mimo_analysis.ul_mu_mimo):
            print(f"\n    [MU-MIMO]")
            print(f"      空间流: {network.mu_mimo_analysis.spatial_streams}")
            print(f"      DL/UL: {network.mu_mimo_analysis.dl_mu_mimo}/{network.mu_mimo_analysis.ul_mu_mimo}")
            print(f"      效率评分: {network.mu_mimo_analysis.efficiency_score:.1f}/100")
    
    print("\n" + "=" * 80)
    summary = analyzer.get_wifi6_summary()
    print(f"\n网络摘要:")
    print(f"  总网络数: {summary['total_networks']}")
    print(f"  WiFi 6网络: {summary['wifi6_count']} ({summary['wifi6_ratio']*100:.1f}%)")
    print(f"  WiFi 6E网络: {summary['wifi6e_count']}")
    print(f"  OFDMA启用: {summary['ofdma_enabled']}")
    print(f"  MU-MIMO启用: {summary['mu_mimo_enabled']}")
    print(f"  TWT支持: {summary['twt_supported']}")
    print(f"  BSS颜色冲突: {summary['bss_color_conflicts']}")
    print(f"  平均评分: {summary['average_score']:.1f}/100")
