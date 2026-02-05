#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WiFi企业级网络信号分析报告模块
功能：生成企业级WiFi信号质量分析报告，包含覆盖率、干扰分析、优化建议等
版本：1.6
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import statistics


class EnterpriseSignalReport:
    """企业级WiFi信号分析报告生成器"""
    
    def __init__(self):
        self.report_data = {}
        self.analysis_results = {}
        
    def analyze_network_quality(self, wifi_data: List[Dict]) -> Dict:
        """
        分析WiFi网络信号质量
        
        Args:
            wifi_data: WiFi扫描数据列表
            
        Returns:
            包含分析结果的字典
        """
        if not wifi_data:
            return {
                'status': 'error',
                'message': '无WiFi数据可供分析'
            }
        
        analysis = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_networks': len(wifi_data),
            'signal_quality': self._analyze_signal_quality(wifi_data),
            'coverage_assessment': self._assess_coverage(wifi_data),
            'channel_utilization': self._analyze_channel_utilization(wifi_data),
            'interference_sources': self._identify_interference(wifi_data),
            'security_status': self._analyze_security(wifi_data),
            'performance_metrics': self._calculate_performance_metrics(wifi_data),
            'optimization_recommendations': []
        }
        
        # 生成优化建议
        analysis['optimization_recommendations'] = self._generate_recommendations(analysis)
        
        self.analysis_results = analysis
        return analysis
    
    def _analyze_signal_quality(self, wifi_data: List[Dict]) -> Dict:
        """分析信号质量分布"""
        signal_levels = {
            'excellent': 0,  # >= -50 dBm
            'good': 0,       # -50 to -60 dBm
            'fair': 0,       # -60 to -70 dBm
            'weak': 0,       # -70 to -80 dBm
            'poor': 0        # < -80 dBm
        }
        
        signals = []
        for network in wifi_data:
            signal = network.get('signal', -100)
            signals.append(signal)
            
            if signal >= -50:
                signal_levels['excellent'] += 1
            elif signal >= -60:
                signal_levels['good'] += 1
            elif signal >= -70:
                signal_levels['fair'] += 1
            elif signal >= -80:
                signal_levels['weak'] += 1
            else:
                signal_levels['poor'] += 1
        
        if signals:
            avg_signal = statistics.mean(signals)
            signal_std = statistics.stdev(signals) if len(signals) > 1 else 0
        else:
            avg_signal = -100
            signal_std = 0
        
        return {
            'distribution': signal_levels,
            'average_signal': round(avg_signal, 2),
            'signal_variance': round(signal_std, 2),
            'strongest_signal': max(signals) if signals else -100,
            'weakest_signal': min(signals) if signals else -100,
            'quality_score': self._calculate_quality_score(signal_levels, len(wifi_data))
        }
    
    def _calculate_quality_score(self, signal_levels: Dict, total: int) -> int:
        """计算整体质量评分 (0-100)"""
        if total == 0:
            return 0
        
        weights = {
            'excellent': 100,
            'good': 80,
            'fair': 60,
            'weak': 40,
            'poor': 20
        }
        
        weighted_sum = sum(signal_levels[level] * weight 
                          for level, weight in weights.items())
        score = int(weighted_sum / total)
        return min(100, max(0, score))
    
    def _assess_coverage(self, wifi_data: List[Dict]) -> Dict:
        """评估覆盖率"""
        total = len(wifi_data)
        
        # 按频段统计
        freq_2_4ghz = sum(1 for n in wifi_data 
                         if self._get_frequency(n.get('channel', 0)) < 5000)
        freq_5ghz = total - freq_2_4ghz
        
        # 统计可用AP数量
        available_aps = sum(1 for n in wifi_data if n.get('signal', -100) >= -70)
        
        coverage_score = min(100, int((available_aps / total * 100) if total > 0 else 0))
        
        return {
            'total_access_points': total,
            'available_aps': available_aps,
            'coverage_score': coverage_score,
            'frequency_distribution': {
                '2.4GHz': freq_2_4ghz,
                '5GHz': freq_5ghz
            },
            'coverage_level': self._get_coverage_level(coverage_score)
        }
    
    def _get_coverage_level(self, score: int) -> str:
        """获取覆盖等级"""
        if score >= 90:
            return '优秀 - 全面覆盖'
        elif score >= 75:
            return '良好 - 覆盖充足'
        elif score >= 60:
            return '一般 - 部分区域信号弱'
        elif score >= 40:
            return '较差 - 存在覆盖盲区'
        else:
            return '差 - 严重覆盖不足'
    
    def _analyze_channel_utilization(self, wifi_data: List[Dict]) -> Dict:
        """分析信道利用率"""
        channel_usage = {}
        
        for network in wifi_data:
            channel = network.get('channel', 0)
            if channel:
                channel_usage[channel] = channel_usage.get(channel, 0) + 1
        
        # 找出最拥挤的信道
        if channel_usage:
            max_channel = max(channel_usage.items(), key=lambda x: x[1])
            congestion_level = self._get_congestion_level(max_channel[1])
        else:
            max_channel = (0, 0)
            congestion_level = '无数据'
        
        return {
            'channel_distribution': channel_usage,
            'most_congested_channel': max_channel[0],
            'max_networks_on_channel': max_channel[1],
            'congestion_level': congestion_level,
            'total_channels_used': len(channel_usage)
        }
    
    def _get_congestion_level(self, count: int) -> str:
        """获取拥堵等级"""
        if count >= 10:
            return '严重拥堵'
        elif count >= 6:
            return '拥堵'
        elif count >= 3:
            return '适中'
        else:
            return '畅通'
    
    def _identify_interference(self, wifi_data: List[Dict]) -> Dict:
        """识别干扰源"""
        interference_risks = []
        overlapping_channels = self._find_overlapping_channels(wifi_data)
        
        # 检测同频干扰
        if overlapping_channels:
            interference_risks.append({
                'type': '同频干扰',
                'severity': 'high',
                'description': f'发现{len(overlapping_channels)}组信道重叠',
                'affected_channels': overlapping_channels
            })
        
        # 检测信号强度波动
        signals = [n.get('signal', -100) for n in wifi_data]
        if signals:
            signal_variance = statistics.stdev(signals) if len(signals) > 1 else 0
            if signal_variance > 15:
                interference_risks.append({
                    'type': '信号不稳定',
                    'severity': 'medium',
                    'description': f'信号强度波动较大 (方差: {signal_variance:.1f})',
                    'recommendation': '检查是否有移动干扰源或物理障碍'
                })
        
        return {
            'total_risks': len(interference_risks),
            'risk_details': interference_risks,
            'interference_score': self._calculate_interference_score(interference_risks)
        }
    
    def _find_overlapping_channels(self, wifi_data: List[Dict]) -> List[int]:
        """查找重叠信道"""
        overlapping = []
        channel_usage = {}
        
        for network in wifi_data:
            channel = network.get('channel', 0)
            if channel:
                channel_usage[channel] = channel_usage.get(channel, 0) + 1
        
        # 2.4GHz信道重叠检测 (信道1,6,11不重叠)
        for channel, count in channel_usage.items():
            if 1 <= channel <= 13 and count > 1:
                overlapping.append(channel)
        
        return overlapping
    
    def _calculate_interference_score(self, risks: List[Dict]) -> int:
        """计算干扰评分 (0-100, 分数越高干扰越少)"""
        if not risks:
            return 100
        
        severity_weights = {
            'high': 30,
            'medium': 15,
            'low': 5
        }
        
        total_penalty = sum(severity_weights.get(risk['severity'], 10) 
                           for risk in risks)
        score = max(0, 100 - total_penalty)
        return score
    
    def _analyze_security(self, wifi_data: List[Dict]) -> Dict:
        """分析安全状态"""
        security_stats = {
            'WPA3': 0,
            'WPA2': 0,
            'WPA': 0,
            'WEP': 0,
            'Open': 0,
            'Unknown': 0
        }
        
        for network in wifi_data:
            auth = network.get('authentication', 'Unknown').upper()
            
            if 'WPA3' in auth:
                security_stats['WPA3'] += 1
            elif 'WPA2' in auth:
                security_stats['WPA2'] += 1
            elif 'WPA' in auth:
                security_stats['WPA'] += 1
            elif 'WEP' in auth:
                security_stats['WEP'] += 1
            elif 'OPEN' in auth or auth == '':
                security_stats['Open'] += 1
            else:
                security_stats['Unknown'] += 1
        
        # 计算安全评分
        total = len(wifi_data)
        if total > 0:
            secure_count = security_stats['WPA3'] + security_stats['WPA2']
            security_score = int((secure_count / total) * 100)
        else:
            security_score = 0
        
        return {
            'security_distribution': security_stats,
            'security_score': security_score,
            'vulnerable_networks': security_stats['WEP'] + security_stats['Open'],
            'security_level': self._get_security_level(security_score)
        }
    
    def _get_security_level(self, score: int) -> str:
        """获取安全等级"""
        if score >= 90:
            return '优秀'
        elif score >= 75:
            return '良好'
        elif score >= 50:
            return '一般'
        else:
            return '需要改进'
    
    def _calculate_performance_metrics(self, wifi_data: List[Dict]) -> Dict:
        """计算性能指标"""
        if not wifi_data:
            return {
                'average_throughput_estimate': 0,
                'network_density': 0,
                'performance_score': 0
            }
        
        # 估算平均吞吐量 (基于信号强度和频段)
        throughput_estimates = []
        for network in wifi_data:
            signal = network.get('signal', -100)
            channel = network.get('channel', 0)
            freq = self._get_frequency(channel)
            
            # 简单估算: 5GHz通常更快，信号强度影响速率
            base_speed = 866 if freq > 5000 else 300  # Mbps
            signal_factor = max(0, min(1, (signal + 100) / 50))
            estimated_speed = base_speed * signal_factor
            throughput_estimates.append(estimated_speed)
        
        avg_throughput = statistics.mean(throughput_estimates) if throughput_estimates else 0
        network_density = len(wifi_data)
        
        # 性能评分综合考虑吞吐量和网络密度
        performance_score = min(100, int(avg_throughput / 10))
        
        return {
            'average_throughput_estimate': round(avg_throughput, 2),
            'network_density': network_density,
            'performance_score': performance_score,
            'density_level': self._get_density_level(network_density)
        }
    
    def _get_density_level(self, density: int) -> str:
        """获取网络密度等级"""
        if density >= 20:
            return '高密度'
        elif density >= 10:
            return '中密度'
        elif density >= 5:
            return '低密度'
        else:
            return '稀疏'
    
    def _get_frequency(self, channel: int) -> int:
        """根据信道获取频率 (MHz)"""
        if 1 <= channel <= 13:
            return 2412 + (channel - 1) * 5
        elif 36 <= channel <= 165:
            return 5000 + channel * 5
        return 0
    
    def _generate_recommendations(self, analysis: Dict) -> List[Dict]:
        """生成优化建议"""
        recommendations = []
        
        # 信号质量建议
        signal_quality = analysis.get('signal_quality', {})
        quality_score = signal_quality.get('quality_score', 0)
        if quality_score < 60:
            recommendations.append({
                'priority': 'high',
                'category': '信号质量',
                'issue': f'整体信号质量较差 (评分: {quality_score}/100)',
                'suggestion': '建议增加AP数量或调整现有AP位置以改善覆盖'
            })
        
        # 覆盖率建议
        coverage = analysis.get('coverage_assessment', {})
        coverage_score = coverage.get('coverage_score', 0)
        if coverage_score < 70:
            recommendations.append({
                'priority': 'high',
                'category': '覆盖范围',
                'issue': f'覆盖率不足 (评分: {coverage_score}/100)',
                'suggestion': '存在覆盖盲区，建议在信号弱的区域增设AP'
            })
        
        # 信道拥堵建议
        channel_util = analysis.get('channel_utilization', {})
        congestion = channel_util.get('congestion_level', '')
        if '拥堵' in congestion:
            most_congested = channel_util.get('most_congested_channel', 0)
            recommendations.append({
                'priority': 'medium',
                'category': '信道优化',
                'issue': f'信道{most_congested}严重拥堵',
                'suggestion': '建议切换到非重叠信道 (2.4GHz: 1,6,11; 5GHz: DFS信道)'
            })
        
        # 干扰问题建议
        interference = analysis.get('interference_sources', {})
        interference_score = interference.get('interference_score', 100)
        if interference_score < 70:
            recommendations.append({
                'priority': 'medium',
                'category': '干扰管理',
                'issue': f'检测到明显干扰 (评分: {interference_score}/100)',
                'suggestion': '检查并消除干扰源，考虑启用频谱分析功能'
            })
        
        # 安全性建议
        security = analysis.get('security_status', {})
        vulnerable = security.get('vulnerable_networks', 0)
        if vulnerable > 0:
            recommendations.append({
                'priority': 'high',
                'category': '网络安全',
                'issue': f'发现{vulnerable}个脆弱网络 (开放或WEP加密)',
                'suggestion': '升级所有网络到WPA2/WPA3加密，禁用开放网络'
            })
        
        # 性能优化建议
        performance = analysis.get('performance_metrics', {})
        perf_score = performance.get('performance_score', 0)
        if perf_score < 50:
            recommendations.append({
                'priority': 'medium',
                'category': '性能优化',
                'issue': f'网络性能较低 (评分: {perf_score}/100)',
                'suggestion': '考虑升级到WiFi 6 (802.11ax)，优化信道带宽设置'
            })
        
        return recommendations
    
    def export_to_json(self, filepath: str) -> bool:
        """导出分析结果为JSON"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.analysis_results, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"导出JSON失败: {e}")
            return False
    
    def get_summary(self) -> str:
        """获取分析摘要文本"""
        if not self.analysis_results:
            return "未进行分析"
        
        analysis = self.analysis_results
        
        summary_lines = [
            "=" * 60,
            "WiFi企业级网络信号分析报告",
            "=" * 60,
            f"\n分析时间: {analysis.get('timestamp', 'N/A')}",
            f"扫描到的网络总数: {analysis.get('total_networks', 0)}个",
            "\n【信号质量评估】",
            f"  整体评分: {analysis.get('signal_quality', {}).get('quality_score', 0)}/100",
            f"  平均信号: {analysis.get('signal_quality', {}).get('average_signal', 0)} dBm",
            "\n【覆盖率评估】",
            f"  覆盖评分: {analysis.get('coverage_assessment', {}).get('coverage_score', 0)}/100",
            f"  覆盖等级: {analysis.get('coverage_assessment', {}).get('coverage_level', 'N/A')}",
            "\n【干扰分析】",
            f"  干扰评分: {analysis.get('interference_sources', {}).get('interference_score', 0)}/100",
            f"  检测到的风险: {analysis.get('interference_sources', {}).get('total_risks', 0)}个",
            "\n【安全状态】",
            f"  安全评分: {analysis.get('security_status', {}).get('security_score', 0)}/100",
            f"  脆弱网络: {analysis.get('security_status', {}).get('vulnerable_networks', 0)}个",
            "\n【性能指标】",
            f"  性能评分: {analysis.get('performance_metrics', {}).get('performance_score', 0)}/100",
            f"  网络密度: {analysis.get('performance_metrics', {}).get('density_level', 'N/A')}",
            "\n【优化建议】"
        ]
        
        recommendations = analysis.get('optimization_recommendations', [])
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                summary_lines.append(f"  {i}. [{rec['priority'].upper()}] {rec['category']}")
                summary_lines.append(f"     问题: {rec['issue']}")
                summary_lines.append(f"     建议: {rec['suggestion']}")
        else:
            summary_lines.append("  暂无优化建议，网络状态良好")
        
        summary_lines.append("\n" + "=" * 60)
        
        return "\n".join(summary_lines)
