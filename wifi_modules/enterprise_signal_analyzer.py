"""
企业级WiFi信号分析模块
提供专业的信号质量评估、覆盖分析、干扰检测等功能
用于生成企业级网络信号分析报告
版本: 1.7 - 集成配置加载器和日志系统
"""

import subprocess
import re
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import statistics

# 新增：导入配置加载器和日志系统
from wifi_modules.config_loader import ConfigLoader
from wifi_modules.logger import get_logger

class EnterpriseSignalAnalyzer:
    """企业级WiFi信号分析器"""
    
    def __init__(self):
        self.CREATE_NO_WINDOW = 0x08000000
        self.scan_history = []
        
        # 新增：初始化配置加载器和日志系统
        self.config = ConfigLoader()
        self.logger = get_logger('EnterpriseSignalAnalyzer')
        self.logger.info("企业级信号分析器初始化")
        
    def perform_comprehensive_scan(self, duration_seconds: int = 30) -> Dict:
        """
        执行综合扫描
        
        Args:
            duration_seconds: 扫描持续时间（秒）
            
        Returns:
            综合扫描结果字典
        """
        self.logger.info(f"开始企业级综合扫描（{duration_seconds}秒）")
        
        results = {
            'scan_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'duration': duration_seconds,
            'networks': [],
            'signal_quality': {},
            'coverage_analysis': {},
            'interference_analysis': {},
            'channel_analysis': {},
            'recommendations': []
        }
        
        # 执行多次扫描以获取更准确的数据
        scan_count = max(3, duration_seconds // 10)
        all_scans = []
        
        for i in range(scan_count):
            scan_data = self._execute_scan()
            if scan_data:
                all_scans.append(scan_data)
                time.sleep(duration_seconds / scan_count)
        
        # 聚合扫描数据
        if all_scans:
            results['networks'] = self._aggregate_network_data(all_scans)
            results['signal_quality'] = self._analyze_signal_quality(results['networks'])
            results['coverage_analysis'] = self._analyze_coverage(results['networks'])
            results['interference_analysis'] = self._analyze_interference(results['networks'])
            results['channel_analysis'] = self._analyze_channels(results['networks'])
            results['recommendations'] = self._generate_recommendations(results)
        
        return results
    
    def _execute_scan(self) -> List[Dict]:
        """执行单次WiFi扫描"""
        try:
            cmd = "netsh wlan show networks mode=bssid"
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=self.CREATE_NO_WINDOW,
                encoding='gbk',
                errors='ignore'
            )
            
            if result.returncode == 0:
                return self._parse_scan_results(result.stdout)
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"netsh命令执行失败: {e.cmd}, 返回码: {e.returncode}")
        except Exception as e:
            self.logger.exception(f"扫描错误: {e}")
        
        return []
    
    def _parse_scan_results(self, output: str) -> List[Dict]:
        """解析扫描结果"""
        networks = []
        current_network = {}
        
        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            
            if line.startswith('SSID'):
                if current_network and 'ssid' in current_network:
                    networks.append(current_network)
                match = re.search(r'SSID\s+\d+\s*:\s*(.+)', line)
                current_network = {
                    'ssid': match.group(1).strip() if match else '隐藏网络',
                    'bssids': []
                }
            
            elif 'BSSID' in line and ':' in line:
                bssid_match = re.search(r'BSSID\s+\d+\s*:\s*([0-9a-fA-F:]+)', line)
                if bssid_match and current_network:
                    current_bssid = {'bssid': bssid_match.group(1)}
                    current_network['bssids'].append(current_bssid)
            
            elif '信号' in line and '%' in line:
                signal_match = re.search(r'(\d+)%', line)
                if signal_match and current_network and current_network['bssids']:
                    current_network['bssids'][-1]['signal'] = int(signal_match.group(1))
            
            elif '频道' in line or 'Channel' in line:
                channel_match = re.search(r'(\d+)', line)
                if channel_match and current_network and current_network['bssids']:
                    current_network['bssids'][-1]['channel'] = int(channel_match.group(1))
            
            elif '身份验证' in line or 'Authentication' in line:
                if current_network:
                    current_network['authentication'] = line.split(':')[-1].strip()
            
            elif '加密' in line or 'Encryption' in line:
                if current_network:
                    current_network['encryption'] = line.split(':')[-1].strip()
        
        if current_network and 'ssid' in current_network:
            networks.append(current_network)
        
        return networks
    
    def _aggregate_network_data(self, scans: List[List[Dict]]) -> List[Dict]:
        """聚合多次扫描的网络数据"""
        network_map = {}
        
        for scan in scans:
            for network in scan:
                ssid = network.get('ssid', '未知')
                
                if ssid not in network_map:
                    network_map[ssid] = {
                        'ssid': ssid,
                        'authentication': network.get('authentication', '未知'),
                        'encryption': network.get('encryption', '未知'),
                        'bssids': {},
                        'signal_samples': []
                    }
                
                for bssid_data in network.get('bssids', []):
                    bssid = bssid_data.get('bssid')
                    if bssid:
                        if bssid not in network_map[ssid]['bssids']:
                            network_map[ssid]['bssids'][bssid] = {
                                'bssid': bssid,
                                'channel': bssid_data.get('channel', 0),
                                'signals': []
                            }
                        
                        signal = bssid_data.get('signal', 0)
                        if signal > 0:
                            network_map[ssid]['bssids'][bssid]['signals'].append(signal)
                            network_map[ssid]['signal_samples'].append(signal)
        
        # 计算统计数据
        networks = []
        for ssid, data in network_map.items():
            bssid_list = []
            for bssid, bssid_data in data['bssids'].items():
                if bssid_data['signals']:
                    bssid_list.append({
                        'bssid': bssid,
                        'channel': bssid_data['channel'],
                        'signal_avg': round(statistics.mean(bssid_data['signals']), 1),
                        'signal_min': min(bssid_data['signals']),
                        'signal_max': max(bssid_data['signals']),
                        'signal_std': round(statistics.stdev(bssid_data['signals']), 1) if len(bssid_data['signals']) > 1 else 0
                    })
            
            if bssid_list:
                # 计算所有采样点的统计数据
                all_signals = data['signal_samples']
                networks.append({
                    'ssid': ssid,
                    'authentication': data['authentication'],
                    'encryption': data['encryption'],
                    'bssids': bssid_list,
                    'signal_avg': round(statistics.mean(all_signals), 1),
                    'signal_max': max(all_signals),  # 新增：最大信号强度
                    'signal_min': min(all_signals),  # 新增：最小信号强度
                    'signals': all_signals,  # 新增：所有信号采样点
                    'signal_std': round(statistics.stdev(all_signals), 1) if len(all_signals) > 1 else 0,  # 新增：标准差
                    'signal_stability': self._calculate_stability(all_signals),
                    'stability': self._calculate_stability(all_signals),  # 兼容性字段
                    'ap_count': len(bssid_list)
                })
        
        return sorted(networks, key=lambda x: x['signal_avg'], reverse=True)
    
    def _calculate_stability(self, signals: List[int]) -> str:
        """计算信号稳定性"""
        if len(signals) < 2:
            return '数据不足'
        
        std = statistics.stdev(signals)
        if std < 5:
            return '优秀'
        elif std < 10:
            return '良好'
        elif std < 15:
            return '一般'
        else:
            return '较差'
    
    def _analyze_signal_quality(self, networks: List[Dict]) -> Dict:
        """分析信号质量（增强版 - IEEE 802.11标准）
        
        采用专业的信号评估模型:
        1. RSSI到质量的非线性转换
        2. 信号稳定性分析（标准差）
        3. 加权质量评分
        4. 信号分布均匀性评估
        """
        if not networks:
            return {'status': 'no_data'}
        
        all_signals_dbm = []  # dBm值列表
        all_signals_percent = []  # 百分比值列表
        signal_distribution = {'excellent': [], 'good': [], 'fair': [], 'poor': []}
        
        for network in networks:
            # 兼容三种数据格式：signal_avg（聚合后）、signal（原始数据）、signal_percent（百分比）
            signal_value = network.get('signal_avg') or network.get('signal') or network.get('signal_percent', 0)
            
            # 确保signal_value是有效数字
            if signal_value is None or signal_value == 'N/A':
                signal_value = 0
            
            # 转换为float并验证范围
            try:
                signal_value = float(signal_value)
            except (ValueError, TypeError):
                signal_value = 0
            
            # 判断是dBm值还是百分比值
            # dBm范围: -100 到 0
            # 百分比范围: 0 到 100
            if signal_value < 0 and signal_value >= -100:
                # 这是dBm值，转换为百分比
                all_signals_dbm.append(signal_value)
                # WiFi信号标准转换: -100dBm到-30dBm映射到0-100%
                # 公式: 百分比 = ((dBm + 100) / 70) * 100
                signal_percent = max(0, min(100, ((signal_value + 100) / 70) * 100))
            elif 0 <= signal_value <= 100:
                # 这是百分比值
                signal_percent = signal_value
                # 反推dBm值: dBm = (百分比 * 0.7) - 100
                # 确保在合理范围内
                calculated_dbm = (signal_percent * 0.7) - 100
                all_signals_dbm.append(max(-100, min(0, calculated_dbm)))
            else:
                # 无效值，使用默认值
                signal_percent = 0
                all_signals_dbm.append(-100)
            
            # 修复：再次确保百分比在0-100范围内，防止任何异常值进入统计
            signal_percent = max(0, min(100, signal_percent))
            all_signals_percent.append(signal_percent)
            
            # 分类统计
            if signal_percent >= 80:
                signal_distribution['excellent'].append(signal_percent)
            elif signal_percent >= 60:
                signal_distribution['good'].append(signal_percent)
            elif signal_percent >= 40:
                signal_distribution['fair'].append(signal_percent)
            else:
                signal_distribution['poor'].append(signal_percent)
        
        # 基础统计
        avg_signal = statistics.mean(all_signals_percent)
        avg_dbm = statistics.mean(all_signals_dbm) if all_signals_dbm else -100
        
        # 信号稳定性分析（标准差）
        std_dev = statistics.stdev(all_signals_percent) if len(all_signals_percent) > 1 else 0
        
        # 计算信号质量加权评分（考虑平均值和稳定性）
        # 评分 = 平均信号强度 * 0.7 + 稳定性奖励 * 0.3
        stability_score = max(0, 100 - std_dev * 2)  # 标准差越小稳定性越高
        weighted_quality_score = avg_signal * 0.7 + stability_score * 0.3
        
        # 信号分布均匀性评估（变异系数CV）
        cv = (std_dev / avg_signal * 100) if avg_signal > 0 else 0
        
        return {
            # 基础指标
            'average_signal': round(avg_signal, 1),
            'average_dbm': round(avg_dbm, 1),  # 新增：dBm平均值
            'average_score': round(weighted_quality_score),  # 加权评分（用于GUI显示）
            'max_signal': max(0, max(all_signals_percent)) if all_signals_percent else 0,  # 修复：确保非负
            'min_signal': max(0, min(all_signals_percent)) if all_signals_percent else 0,  # 修复：确保非负
            
            # 分级统计
            'excellent_count': len(signal_distribution['excellent']),
            'good_count': len(signal_distribution['good']),
            'fair_count': len(signal_distribution['fair']),
            'poor_count': len(signal_distribution['poor']),
            'total_networks': len(networks),
            
            # 质量评级
            'average_quality': self._get_quality_rating(avg_signal),
            'quality_rating': self._get_quality_rating(avg_signal),
            
            # 新增：稳定性和均匀性指标
            'stability': {
                'std_dev': round(std_dev, 2),
                'cv_percent': round(cv, 2),
                'stability_score': round(stability_score, 1),
                'stability_level': self._get_stability_level(std_dev)
            },
            
            # 新增：信号分布详情
            'distribution_details': {
                'excellent_avg': round(statistics.mean(signal_distribution['excellent']), 1) if signal_distribution['excellent'] else 0,
                'good_avg': round(statistics.mean(signal_distribution['good']), 1) if signal_distribution['good'] else 0,
                'fair_avg': round(statistics.mean(signal_distribution['fair']), 1) if signal_distribution['fair'] else 0,
                'poor_avg': round(statistics.mean(signal_distribution['poor']), 1) if signal_distribution['poor'] else 0
            }
        }
    
    def _get_quality_rating(self, avg_signal: float) -> str:
        """获取质量评级"""
        if avg_signal >= 80:
            return '优秀'
        elif avg_signal >= 60:
            return '良好'
        elif avg_signal >= 40:
            return '一般'
        else:
            return '较差'
    
    def _get_stability_level(self, std_dev: float) -> str:
        """获取信号稳定性评级
        
        根据标准差判断信号稳定性:
        - 极佳: 标准差 < 5 (信号非常稳定)
        - 良好: 5 <= 标准差 < 10
        - 一般: 10 <= 标准差 < 15
        - 较差: 标准差 >= 15 (信号波动大)
        """
        if std_dev < 5:
            return '极佳'
        elif std_dev < 10:
            return '良好'
        elif std_dev < 15:
            return '一般'
        else:
            return '较差'
    
    def _analyze_coverage(self, networks: List[Dict]) -> Dict:
        """分析覆盖情况"""
        # 兼容两种数据格式
        total_aps = 0
        freq_2_4g = 0
        freq_5g = 0
        
        for network in networks:
            # 如果有ap_count字段，使用它；否则计算bssids数量
            if 'ap_count' in network:
                total_aps += network['ap_count']
            else:
                bssid_list = network.get('bssids', [network])
                total_aps += len(bssid_list)
            
            # 统计频段分布
            bssid_list = network.get('bssids', [network])
            for bssid in bssid_list:
                channel = bssid.get('channel', 0)
                # 处理字符串类型的channel
                if isinstance(channel, str):
                    try:
                        channel = int(channel)
                    except ValueError:
                        channel = 0
                if channel <= 14 and channel > 0:
                    freq_2_4g += 1
                elif channel > 14:
                    freq_5g += 1
        
        return {
            'total_access_points': total_aps,
            'total_aps': total_aps,  # 添加别名字段
            'unique_ssids': len(networks),
            'avg_aps_per_network': round(total_aps / len(networks), 1) if networks else 0,
            'frequency_2_4g_count': freq_2_4g,
            'frequency_5g_count': freq_5g,
            '2.4ghz_count': freq_2_4g,  # 添加别名字段
            '5ghz_count': freq_5g,  # 添加别名字段
            'frequency_distribution': {
                '2.4GHz': round(freq_2_4g / total_aps * 100, 1) if total_aps > 0 else 0,
                '5GHz': round(freq_5g / total_aps * 100, 1) if total_aps > 0 else 0
            },
            'coverage_rating': self._get_coverage_rating(total_aps, len(networks))
        }
    
    def _get_coverage_rating(self, total_aps: int, unique_ssids: int) -> str:
        """获取覆盖评级"""
        if total_aps >= 10 and unique_ssids >= 5:
            return '密集覆盖'
        elif total_aps >= 5:
            return '良好覆盖'
        elif total_aps >= 2:
            return '基本覆盖'
        else:
            return '覆盖不足'
    
    def _analyze_interference(self, networks: List[Dict]) -> Dict:
        """分析干扰情况"""
        # 信道拥挤度分析
        channel_usage = {}
        for network in networks:
            # 兼容两种数据格式：bssids列表或单个network
            bssid_list = network.get('bssids', [network])
            for bssid in bssid_list:
                channel = bssid.get('channel', 0)
                # 处理字符串类型的channel
                if isinstance(channel, str):
                    try:
                        channel = int(channel)
                    except ValueError:
                        channel = 0
                if channel not in channel_usage:
                    channel_usage[channel] = []
                
                # 兼容signal_avg和signal字段
                signal = bssid.get('signal_avg') or bssid.get('signal', -100)
                if signal < 0:
                    signal = max(0, min(100, (signal + 100) * 2))
                
                channel_usage[channel].append({
                    'ssid': network.get('ssid', 'Unknown'),
                    'bssid': bssid.get('bssid', ''),
                    'signal': signal
                })
        
        # 找出最拥挤的信道
        crowded_channels = sorted(
            [(ch, len(aps)) for ch, aps in channel_usage.items()],
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # 计算干扰级别
        max_channel_count = max((len(aps) for aps in channel_usage.values()), default=0)
        
        return {
            'total_channels_used': len(channel_usage),
            'most_crowded_channels': [
                {'channel': ch, 'ap_count': count} for ch, count in crowded_channels
            ],
            'max_aps_on_channel': max_channel_count,
            'interference_level': self._get_interference_level(max_channel_count),
            'channel_details': channel_usage
        }
    
    def _get_interference_level(self, max_count: int) -> str:
        """获取干扰级别"""
        if max_count >= 10:
            return '严重'
        elif max_count >= 5:
            return '较高'
        elif max_count >= 3:
            return '中等'
        else:
            return '较低'
    
    def _analyze_channels(self, networks: List[Dict]) -> Dict:
        """分析信道使用情况"""
        channels_2_4g = {}
        channels_5g = {}
        
        for network in networks:
            # 兼容两种数据格式：bssids列表或单个network
            bssid_list = network.get('bssids', [network])
            for bssid in bssid_list:
                channel = bssid.get('channel', 0)
                # 处理字符串类型的channel
                if isinstance(channel, str):
                    try:
                        channel = int(channel)
                    except ValueError:
                        channel = 0
                
                # 兼容signal_avg和signal字段
                signal = bssid.get('signal_avg') or bssid.get('signal', -100)
                if signal < 0:
                    signal = max(0, min(100, (signal + 100) * 2))
                
                if channel <= 14:
                    if channel not in channels_2_4g:
                        channels_2_4g[channel] = []
                    channels_2_4g[channel].append(signal)
                else:
                    if channel not in channels_5g:
                        channels_5g[channel] = []
                    channels_5g[channel].append(signal)
        
        # 推荐最佳信道
        best_2_4g = self._find_best_channel(channels_2_4g, [1, 6, 11])
        best_5g = self._find_best_channel(channels_5g)
        
        return {
            '2.4GHz': {
                'used_channels': sorted(channels_2_4g.keys()),
                'channel_count': len(channels_2_4g),
                'recommended_channel': best_2_4g,
                'congestion': {ch: len(sigs) for ch, sigs in channels_2_4g.items()}
            },
            '5GHz': {
                'used_channels': sorted(channels_5g.keys()),
                'channel_count': len(channels_5g),
                'recommended_channel': best_5g,
                'congestion': {ch: len(sigs) for ch, sigs in channels_5g.items()}
            }
        }
    
    def _find_best_channel(self, channel_usage: Dict, preferred: List[int] = None) -> Optional[int]:
        """找出最佳信道"""
        if not channel_usage:
            return preferred[0] if preferred else None
        
        # 优先考虑未使用的信道
        if preferred:
            for ch in preferred:
                if ch not in channel_usage:
                    return ch
        
        # 选择使用最少的信道
        min_usage = min((len(sigs) for sigs in channel_usage.values()), default=0)
        candidates = [ch for ch, sigs in channel_usage.items() if len(sigs) == min_usage]
        
        if preferred:
            for ch in preferred:
                if ch in candidates:
                    return ch
        
        return candidates[0] if candidates else None
    
    def _generate_recommendations(self, results: Dict) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        # 信号质量建议
        quality = results.get('signal_quality', {})
        if quality.get('poor_count', 0) > 0:
            recommendations.append(
                f"发现 {quality['poor_count']} 个信号较弱的网络，建议增加接入点或调整位置"
            )
        
        # 覆盖建议
        coverage = results.get('coverage_analysis', {})
        if coverage.get('total_access_points', 0) < 2:
            recommendations.append("接入点数量较少，建议增加AP以提高覆盖范围和冗余性")
        
        # 干扰建议
        interference = results.get('interference_analysis', {})
        if interference.get('interference_level') in ['严重', '较高']:
            recommendations.append(
                f"检测到{interference['interference_level']}干扰，建议优化信道配置或使用5GHz频段"
            )
        
        # 信道建议
        channel = results.get('channel_analysis', {})
        if channel.get('2.4GHz', {}).get('recommended_channel'):
            rec_ch = channel['2.4GHz']['recommended_channel']
            recommendations.append(f"2.4GHz频段推荐使用信道 {rec_ch}")
        
        if channel.get('5GHz', {}).get('recommended_channel'):
            rec_ch = channel['5GHz']['recommended_channel']
            recommendations.append(f"5GHz频段推荐使用信道 {rec_ch}")
        
        # 频段建议
        if coverage.get('frequency_5g_count', 0) == 0:
            recommendations.append("建议启用5GHz频段以减少干扰和提高性能")
        
        if not recommendations:
            recommendations.append("网络配置良好，无需特别优化")
        
        return recommendations
    
    def analyze_network_data(self, wifi_data: List[Dict]) -> Dict:
        """
        分析已有的WiFi网络数据（不执行扫描）
        
        Args:
            wifi_data: WiFi网络数据列表，每项包含ssid, bssid, signal, channel等信息
            
        Returns:
            分析结果字典
        """
        self.logger.info(f"开始分析{len(wifi_data)}个WiFi网络")
        
        # 关键修复：为每个网络添加必需字段（如果缺失）
        # 报告生成器依赖signal_avg, signal_max, signal_min等字段
        processed_data = []
        for net in wifi_data:
            network = net.copy()
            
            # 获取信号值（兼容多种字段名）
            signal_value = network.get('signal_avg') or network.get('signal') or network.get('signal_percent', 0)
            if signal_value is None or signal_value == 'N/A':
                signal_value = 0.0
            else:
                try:
                    signal_value = float(signal_value)
                    # 验证信号值在合理范围内
                    # 如果是负值但超出dBm范围，设为0
                    if signal_value < -100:
                        signal_value = 0.0
                    # 如果是正值但超出百分比范围，限制在100以内
                    elif signal_value > 100:
                        signal_value = min(100, signal_value)
                except (ValueError, TypeError):
                    signal_value = 0.0
            
            # 如果没有signal_avg，使用signal字段的值
            if 'signal_avg' not in network or network.get('signal_avg') is None:
                network['signal_avg'] = signal_value
            
            # 如果没有signal_max，使用signal_avg值
            if 'signal_max' not in network or network.get('signal_max') is None:
                network['signal_max'] = signal_value
            
            # 如果没有signal_min，使用signal_avg值
            if 'signal_min' not in network or network.get('signal_min') is None:
                network['signal_min'] = signal_value
            
            # 如果没有signals列表，创建单元素列表
            if 'signals' not in network or not network.get('signals'):
                network['signals'] = [signal_value]
            
            # 如果没有signal_std，设置默认值
            if 'signal_std' not in network:
                network['signal_std'] = 0.0
            
            # 如果没有signal_stability，设置默认值
            if 'signal_stability' not in network:
                network['signal_stability'] = '数据不足'
            if 'stability' not in network:
                network['stability'] = network['signal_stability']
            
            # 如果没有ap_count，设置默认值
            if 'ap_count' not in network:
                network['ap_count'] = 1
            
            processed_data.append(network)
        
        results = {
            'scan_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_networks': len(processed_data),
            'scan_count': 1,  # 单次数据分析
            'networks': processed_data,  # 使用处理后的数据
            'signal_quality': {},
            'coverage_analysis': {},  # 修复字段名：coverage -> coverage_analysis
            'interference_analysis': {},  # 修复字段名：interference -> interference_analysis
            'channel_analysis': {},  # 修复字段名：channel_usage -> channel_analysis
            'recommendations': []
        }
        
        if processed_data:
            # 执行各项分析
            results['signal_quality'] = self._analyze_signal_quality(processed_data)
            results['coverage_analysis'] = self._analyze_coverage(processed_data)
            results['interference_analysis'] = self._analyze_interference(processed_data)
            results['channel_analysis'] = self._analyze_channels(processed_data)
            results['recommendations'] = self._generate_recommendations(results)
        
        self.logger.info(f"分析完成！总网络数: {len(processed_data)}")
        return results
