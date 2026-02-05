#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
企业级WiFi网络信号分析报告生成器
版本: 1.6
功能: 生成专业的企业级WiFi信号分析报告
"""

import time
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional


class EnterpriseSignalAnalyzer:
    """企业级WiFi信号分析器"""
    
    def __init__(self):
        self.analysis_data = {}
        self.timestamp = datetime.now()
    
    def analyze_network_data(self, wifi_data: List[Dict]) -> Dict[str, Any]:
        """
        分析WiFi网络数据
        
        Args:
            wifi_data: WiFi扫描数据列表
            
        Returns:
            分析结果字典
        """
        if not wifi_data:
            return self._empty_analysis()
        
        analysis = {
            'timestamp': self.timestamp.isoformat(),
            'total_networks': len(wifi_data),
            'signal_distribution': self._analyze_signal_distribution(wifi_data),
            'channel_utilization': self._analyze_channel_utilization(wifi_data),
            'security_analysis': self._analyze_security(wifi_data),
            'vendor_distribution': self._analyze_vendors(wifi_data),
            'frequency_bands': self._analyze_frequency_bands(wifi_data),
            'interference_analysis': self._analyze_interference(wifi_data),
            'coverage_quality': self._analyze_coverage_quality(wifi_data),
            'recommendations': self._generate_recommendations(wifi_data)
        }
        
        self.analysis_data = analysis
        return analysis
    
    def _empty_analysis(self) -> Dict:
        """返回空分析结果"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'total_networks': 0,
            'signal_distribution': {},
            'channel_utilization': {},
            'security_analysis': {},
            'vendor_distribution': {},
            'frequency_bands': {},
            'interference_analysis': {},
            'coverage_quality': {},
            'recommendations': []
        }
    
    def _analyze_signal_distribution(self, wifi_data: List[Dict]) -> Dict:
        """分析信号强度分布"""
        distribution = {
            'excellent': 0,  # -50 dBm以上
            'good': 0,       # -50 ~ -60 dBm
            'fair': 0,       # -60 ~ -70 dBm
            'poor': 0,       # -70 ~ -80 dBm
            'very_poor': 0   # -80 dBm以下
        }
        
        signal_values = []
        
        for network in wifi_data:
            signal = network.get('signal', -100)
            signal_values.append(signal)
            
            if signal >= -50:
                distribution['excellent'] += 1
            elif signal >= -60:
                distribution['good'] += 1
            elif signal >= -70:
                distribution['fair'] += 1
            elif signal >= -80:
                distribution['poor'] += 1
            else:
                distribution['very_poor'] += 1
        
        # 计算统计信息
        if signal_values:
            distribution['average'] = sum(signal_values) / len(signal_values)
            distribution['max'] = max(signal_values)
            distribution['min'] = min(signal_values)
        else:
            distribution['average'] = -100
            distribution['max'] = -100
            distribution['min'] = -100
        
        return distribution
    
    def _analyze_channel_utilization(self, wifi_data: List[Dict]) -> Dict:
        """分析信道利用率"""
        channel_usage = {}
        
        for network in wifi_data:
            channel = network.get('channel', 'Unknown')
            if channel == 'Unknown':
                continue
            
            if channel not in channel_usage:
                channel_usage[channel] = {
                    'count': 0,
                    'networks': [],
                    'avg_signal': 0,
                    'max_signal': -100
                }
            
            channel_usage[channel]['count'] += 1
            channel_usage[channel]['networks'].append(network.get('ssid', 'Unknown'))
            signal = network.get('signal', -100)
            
            if signal > channel_usage[channel]['max_signal']:
                channel_usage[channel]['max_signal'] = signal
        
        # 计算平均信号
        for channel, data in channel_usage.items():
            signals = [n.get('signal', -100) for n in wifi_data if n.get('channel') == channel]
            if signals:
                data['avg_signal'] = sum(signals) / len(signals)
        
        # 识别拥塞信道
        congested_channels = [ch for ch, data in channel_usage.items() if data['count'] >= 3]
        
        return {
            'channel_usage': channel_usage,
            'congested_channels': congested_channels,
            'total_channels_used': len(channel_usage),
            'most_congested': max(channel_usage.items(), key=lambda x: x[1]['count'])[0] if channel_usage else None
        }
    
    def _analyze_security(self, wifi_data: List[Dict]) -> Dict:
        """分析安全配置"""
        security_types = {
            'WPA3': 0,
            'WPA2': 0,
            'WPA': 0,
            'WEP': 0,
            'Open': 0,
            'Unknown': 0
        }
        
        for network in wifi_data:
            security = network.get('security', 'Unknown')
            
            if 'WPA3' in security:
                security_types['WPA3'] += 1
            elif 'WPA2' in security:
                security_types['WPA2'] += 1
            elif 'WPA' in security:
                security_types['WPA'] += 1
            elif 'WEP' in security:
                security_types['WEP'] += 1
            elif security == 'Open' or 'Open' in security:
                security_types['Open'] += 1
            else:
                security_types['Unknown'] += 1
        
        # 安全评分
        total = len(wifi_data)
        if total > 0:
            security_score = (
                (security_types['WPA3'] * 100 +
                 security_types['WPA2'] * 80 +
                 security_types['WPA'] * 50 +
                 security_types['WEP'] * 20 +
                 security_types['Open'] * 0) / total
            )
        else:
            security_score = 0
        
        return {
            'distribution': security_types,
            'security_score': round(security_score, 2),
            'vulnerable_networks': security_types['WEP'] + security_types['Open'],
            'secure_networks': security_types['WPA3'] + security_types['WPA2']
        }
    
    def _analyze_vendors(self, wifi_data: List[Dict]) -> Dict:
        """分析设备厂商分布"""
        vendors = {}
        
        for network in wifi_data:
            vendor = network.get('vendor', 'Unknown')
            if vendor not in vendors:
                vendors[vendor] = 0
            vendors[vendor] += 1
        
        # 排序
        sorted_vendors = sorted(vendors.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'distribution': dict(sorted_vendors[:10]),  # 取前10
            'total_vendors': len(vendors),
            'top_vendor': sorted_vendors[0] if sorted_vendors else ('Unknown', 0)
        }
    
    def _analyze_frequency_bands(self, wifi_data: List[Dict]) -> Dict:
        """分析频段分布"""
        bands = {
            '2.4GHz': 0,
            '5GHz': 0,
            '6GHz': 0,
            'Unknown': 0
        }
        
        for network in wifi_data:
            channel = network.get('channel', 0)
            
            try:
                channel_num = int(channel)
                if 1 <= channel_num <= 14:
                    bands['2.4GHz'] += 1
                elif 36 <= channel_num <= 165:
                    bands['5GHz'] += 1
                elif channel_num >= 193:
                    bands['6GHz'] += 1
                else:
                    bands['Unknown'] += 1
            except (ValueError, TypeError):
                bands['Unknown'] += 1
        
        return bands
    
    def _analyze_interference(self, wifi_data: List[Dict]) -> Dict:
        """分析干扰情况"""
        overlapping_channels = []
        
        # 2.4GHz 非重叠信道: 1, 6, 11
        channels_24 = {}
        for network in wifi_data:
            try:
                channel = int(network.get('channel', 0))
                if 1 <= channel <= 14:
                    if channel not in channels_24:
                        channels_24[channel] = []
                    channels_24[channel].append(network.get('ssid', 'Unknown'))
            except (ValueError, TypeError):
                continue
        
        # 检查重叠
        for channel in [2, 3, 4, 5, 7, 8, 9, 10, 12, 13]:
            if channel in channels_24:
                overlapping_channels.append({
                    'channel': channel,
                    'count': len(channels_24[channel]),
                    'networks': channels_24[channel]
                })
        
        return {
            'overlapping_channels': overlapping_channels,
            'interference_level': 'High' if len(overlapping_channels) > 5 else 'Medium' if len(overlapping_channels) > 2 else 'Low',
            'total_interfering_networks': sum(len(ch['networks']) for ch in overlapping_channels)
        }
    
    def _analyze_coverage_quality(self, wifi_data: List[Dict]) -> Dict:
        """分析覆盖质量"""
        total = len(wifi_data)
        if total == 0:
            return {'quality_score': 0, 'rating': 'No Data'}
        
        signal_dist = self._analyze_signal_distribution(wifi_data)
        
        # 质量评分
        quality_score = (
            signal_dist['excellent'] * 100 +
            signal_dist['good'] * 80 +
            signal_dist['fair'] * 60 +
            signal_dist['poor'] * 30 +
            signal_dist['very_poor'] * 10
        ) / total
        
        # 评级
        if quality_score >= 80:
            rating = 'Excellent'
        elif quality_score >= 60:
            rating = 'Good'
        elif quality_score >= 40:
            rating = 'Fair'
        else:
            rating = 'Poor'
        
        return {
            'quality_score': round(quality_score, 2),
            'rating': rating,
            'strong_signal_percentage': round((signal_dist['excellent'] + signal_dist['good']) / total * 100, 2),
            'weak_signal_percentage': round((signal_dist['poor'] + signal_dist['very_poor']) / total * 100, 2)
        }
    
    def _generate_recommendations(self, wifi_data: List[Dict]) -> List[Dict]:
        """生成优化建议"""
        recommendations = []
        
        # 分析各项指标
        signal_dist = self._analyze_signal_distribution(wifi_data)
        channel_util = self._analyze_channel_utilization(wifi_data)
        security = self._analyze_security(wifi_data)
        interference = self._analyze_interference(wifi_data)
        
        # 信号强度建议
        if signal_dist['poor'] + signal_dist['very_poor'] > len(wifi_data) * 0.3:
            recommendations.append({
                'priority': 'High',
                'category': 'Signal Coverage',
                'issue': f"{signal_dist['poor'] + signal_dist['very_poor']} 个网络信号弱',
                'recommendation': '建议增加AP数量或调整AP位置以改善覆盖',
                'impact': '提升用户体验和网络稳定性'
            })
        
        # 信道拥塞建议
        if channel_util['congested_channels']:
            recommendations.append({
                'priority': 'High',
                'category': 'Channel Optimization',
                'issue': f"{len(channel_util['congested_channels'])} 个信道过度拥塞",
                'recommendation': f"建议将部分AP迁移到空闲信道，拥塞信道: {', '.join(map(str, channel_util['congested_channels']))}",
                'impact': '减少干扰，提高网络吞吐量'
            })
        
        # 安全性建议
        if security['vulnerable_networks'] > 0:
            recommendations.append({
                'priority': 'Critical',
                'category': 'Security',
                'issue': f"{security['vulnerable_networks']} 个网络使用弱加密或无加密",
                'recommendation': '强烈建议所有网络升级到WPA2/WPA3加密',
                'impact': '提升网络安全性，防止未授权访问'
            })
        
        # 干扰建议
        if interference['interference_level'] in ['High', 'Medium']:
            recommendations.append({
                'priority': 'Medium',
                'category': 'Interference',
                'issue': f"检测到{interference['interference_level']}级别的信道干扰",
                'recommendation': '建议使用1、6、11信道部署2.4GHz网络，避免信道重叠',
                'impact': '降低同频干扰，提高网络性能'
            })
        
        # 频段建议
        bands = self._analyze_frequency_bands(wifi_data)
        if bands['5GHz'] < bands['2.4GHz'] * 0.3:
            recommendations.append({
                'priority': 'Medium',
                'category': 'Frequency Band',
                'issue': '5GHz频段利用率低',
                'recommendation': '建议部署更多5GHz网络，分流2.4GHz频段压力',
                'impact': '提供更高带宽和更少干扰'
            })
        
        return recommendations
    
    def export_to_json(self, filepath: str) -> bool:
        """
        导出分析结果到JSON
        
        Args:
            filepath: 输出文件路径
            
        Returns:
            是否成功
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.analysis_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"导出JSON失败: {e}")
            return False
    
    def get_summary(self) -> str:
        """获取分析摘要"""
        if not self.analysis_data:
            return "暂无分析数据"
        
        summary = f"""
企业级WiFi网络分析摘要
{'='*50}
分析时间: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
网络总数: {self.analysis_data['total_networks']}

信号质量: {self.analysis_data['coverage_quality'].get('rating', 'N/A')}
质量评分: {self.analysis_data['coverage_quality'].get('quality_score', 0)}/100

安全评分: {self.analysis_data['security_analysis'].get('security_score', 0)}/100
脆弱网络: {self.analysis_data['security_analysis'].get('vulnerable_networks', 0)}

信道拥塞: {len(self.analysis_data['channel_utilization'].get('congested_channels', []))} 个
干扰级别: {self.analysis_data['interference_analysis'].get('interference_level', 'N/A')}

优化建议: {len(self.analysis_data['recommendations'])} 条
{'='*50}
"""
        return summary
