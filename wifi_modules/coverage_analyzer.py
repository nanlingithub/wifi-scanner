"""
专业无线网络规划设计系统 - 信号覆盖评估模块
功能：测量数据采集、信号覆盖分析、专业评估报告生成
"""

import numpy as np
from datetime import datetime
from typing import List, Dict, Tuple
import json


class CoverageAnalyzer:
    """信号覆盖分析器 - 专业无线网络评估"""
    
    # 信号质量分级标准（IEEE 802.11标准）
    SIGNAL_GRADES = {
        'excellent': (-30, -50, '优秀', '适合高密度应用'),
        'good': (-50, -60, '良好', '满足办公需求'),
        'fair': (-60, -70, '一般', '基本可用'),
        'poor': (-70, -80, '较差', '需改善'),
        'critical': (-80, -90, '极差', '不可用')
    }
    
    # 应用场景需求标准
    SCENARIO_REQUIREMENTS = {
        '高密度办公': {
            'min_signal': -60,
            'coverage_rate': 95,
            'max_ap_overlap': 3,
            'channel_bandwidth': 40,
            'recommended_standard': 'WiFi 6'
        },
        '普通办公': {
            'min_signal': -65,
            'coverage_rate': 90,
            'max_ap_overlap': 2,
            'channel_bandwidth': 40,
            'recommended_standard': 'WiFi 5'
        },
        '教育培训': {
            'min_signal': -60,
            'coverage_rate': 98,
            'max_ap_overlap': 2,
            'channel_bandwidth': 80,
            'recommended_standard': 'WiFi 6'
        },
        '医疗健康': {
            'min_signal': -55,
            'coverage_rate': 99,
            'max_ap_overlap': 1,
            'channel_bandwidth': 80,
            'recommended_standard': 'WiFi 6E'
        },
        '工业制造': {
            'min_signal': -70,
            'coverage_rate': 85,
            'max_ap_overlap': 2,
            'channel_bandwidth': 20,
            'recommended_standard': 'WiFi 4/5'
        }
    }
    
    def __init__(self, scenario: str = '普通办公'):
        """初始化覆盖分析器
        
        Args:
            scenario: 应用场景类型
        """
        self.scenario = scenario
        self.measurement_data = []
        self.analysis_result = None
        
        # 验证场景
        if scenario not in self.SCENARIO_REQUIREMENTS:
            raise ValueError(f"未知场景: {scenario}. 支持的场景: {list(self.SCENARIO_REQUIREMENTS.keys())}")
    
    def add_measurement(self, x: float, y: float, signal_dbm: float, 
                       band: str = '2.4GHz', timestamp: datetime = None):
        """添加测量点数据"""
        self.measurement_data.append({
            'x': x,
            'y': y,
            'signal_dbm': signal_dbm,
            'signal_percent': self._dbm_to_percent(signal_dbm),
            'band': band,
            'grade': self._get_signal_grade(signal_dbm),
            'timestamp': timestamp or datetime.now()
        })
    
    def analyze_coverage(self, area_sqm: float, scenario: str = None):
        """分析信号覆盖情况"""
        if not self.measurement_data:
            return None
        
        # 使用传入的scenario或对象的scenario
        scenario = scenario or self.scenario
        
        signals = [p['signal_dbm'] for p in self.measurement_data]
        
        # 基础统计
        avg_signal = np.mean(signals)
        min_signal = np.min(signals)
        max_signal = np.max(signals)
        std_signal = np.std(signals)
        
        # 覆盖率分析
        req = self.SCENARIO_REQUIREMENTS.get(scenario, self.SCENARIO_REQUIREMENTS['普通办公'])
        good_points = [s for s in signals if s >= req['min_signal']]
        coverage_rate = (len(good_points) / len(signals)) * 100
        
        # 信号均匀性分析（变异系数）
        cv = (std_signal / abs(avg_signal)) * 100 if avg_signal != 0 else 0
        uniformity = 'excellent' if cv < 10 else 'good' if cv < 20 else 'fair' if cv < 30 else 'poor'
        
        # 弱信号区域检测
        weak_zones = [p for p in self.measurement_data if p['signal_dbm'] < -70]
        
        # 过度覆盖检测（估算）
        over_coverage = self._detect_over_coverage()
        
        # 容量估算
        estimated_capacity = self._estimate_capacity(area_sqm, avg_signal, scenario)
        
        # 合规性评估
        compliance = self._check_compliance(scenario, coverage_rate, avg_signal)
        
        self.analysis_result = {
            'timestamp': datetime.now(),
            'scenario': scenario,
            'area_sqm': area_sqm,
            'measurement_count': len(self.measurement_data),
            
            # 信号统计
            'signal_stats': {
                'average': avg_signal,
                'minimum': min_signal,
                'maximum': max_signal,
                'std_dev': std_signal,
                'coefficient_variation': cv
            },
            
            # 覆盖分析
            'coverage': {
                'rate': coverage_rate,
                'requirement': req['coverage_rate'],
                'status': 'passed' if coverage_rate >= req['coverage_rate'] else 'failed',
                'weak_zone_count': len(weak_zones),
                'weak_zones': weak_zones
            },
            
            # 信号质量分布
            'quality_distribution': self._analyze_quality_distribution(),
            
            # 均匀性
            'uniformity': {
                'level': uniformity,
                'cv_percent': cv,
                'assessment': self._get_uniformity_assessment(uniformity)
            },
            
            # 过度覆盖
            'over_coverage': over_coverage,
            
            # 容量估算
            'capacity': estimated_capacity,
            
            # 合规性
            'compliance': compliance,
            
            # 改进建议
            'recommendations': self._generate_recommendations(
                coverage_rate, avg_signal, weak_zones, over_coverage, scenario
            )
        }
        
        return self.analysis_result
    
    def generate_professional_report(self, area_sqm: float = None) -> str:
        """生成专业评估报告
        
        Args:
            area_sqm: 区域面积（平方米），如果未提供则需先调用analyze_coverage
        """
        # 如果未执行分析，先执行
        if not self.analysis_result and area_sqm:
            self.analyze_coverage(area_sqm)
        
        if not self.analysis_result:
            return "请先执行覆盖分析或提供区域面积"
        
        r = self.analysis_result
        
        report = f"""
╔══════════════════════════════════════════════════════════════╗
║          无线网络信号覆盖专业评估报告                        ║
╚══════════════════════════════════════════════════════════════╝

【报告信息】
生成时间: {r['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
应用场景: {r['scenario']}
测试区域: {r['area_sqm']:.1f} 平方米
测量点数: {r['measurement_count']} 个

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【一、信号强度统计】

平均信号强度: {r['signal_stats']['average']:.1f} dBm
最大信号强度: {r['signal_stats']['maximum']:.1f} dBm
最小信号强度: {r['signal_stats']['minimum']:.1f} dBm
标准差:       {r['signal_stats']['std_dev']:.2f} dB
变异系数:     {r['signal_stats']['coefficient_variation']:.1f}%

信号质量评级: {self._get_signal_grade(r['signal_stats']['average'])[1]}
适用性评估:   {self._get_signal_grade(r['signal_stats']['average'])[2]}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【二、覆盖率分析】

实际覆盖率: {r['coverage']['rate']:.1f}%
需求覆盖率: {r['coverage']['requirement']:.1f}%
合规状态:   {r['coverage']['status'].upper()}

{'✅ 覆盖率达标' if r['coverage']['status'] == 'passed' else '❌ 覆盖率不达标'}

弱信号区域: {r['coverage']['weak_zone_count']} 处
"""
        
        # 弱信号区域详情
        if r['coverage']['weak_zones']:
            report += "\n弱信号区域位置:\n"
            for i, zone in enumerate(r['coverage']['weak_zones'][:5], 1):
                report += f"  {i}. 坐标({zone['x']:.1f}, {zone['y']:.1f}) - {zone['signal_dbm']:.1f} dBm\n"
            if len(r['coverage']['weak_zones']) > 5:
                report += f"  ... 还有 {len(r['coverage']['weak_zones'])-5} 处\n"
        
        # 信号质量分布
        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【三、信号质量分布】

"""
        for grade, data in r['quality_distribution'].items():
            bar = '█' * int(data['percentage'] / 2)
            report += f"{data['name']:6s} ({data['range']:15s}): {bar} {data['percentage']:5.1f}% ({data['count']:3d}点)\n"
        
        # 均匀性分析
        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【四、信号均匀性】

均匀性等级: {r['uniformity']['level'].upper()}
变异系数:   {r['uniformity']['cv_percent']:.1f}%
评估意见:   {r['uniformity']['assessment']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【五、过度覆盖分析】

重叠AP数量: {r['over_coverage']['overlap_count']} 个
资源浪费率: {r['over_coverage']['waste_rate']:.1f}%
优化建议:   {r['over_coverage']['suggestion']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【六、容量估算】

预计支持用户数: {r['capacity']['estimated_users']} 人
推荐AP数量:     {r['capacity']['recommended_aps']} 台
用户密度:       {r['capacity']['user_density']:.1f} 人/100㎡
容量等级:       {r['capacity']['capacity_level']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【七、合规性评估】

合规状态: {r['compliance']['overall']}
合规项目:
"""
        for item, status in r['compliance']['items'].items():
            icon = '✅' if status else '❌'
            report += f"  {icon} {item}\n"
        
        # 改进建议
        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【八、专业改进建议】

优先级P0 (立即执行):
"""
        for rec in r['recommendations']['p0']:
            report += f"  • {rec}\n"
        
        report += "\n优先级P1 (建议执行):\n"
        for rec in r['recommendations']['p1']:
            report += f"  • {rec}\n"
        
        report += "\n优先级P2 (长期优化):\n"
        for rec in r['recommendations']['p2']:
            report += f"  • {rec}\n"
        
        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【九、总体评估】

综合评分: {self._calculate_overall_score():.1f}/100

评估结论: {self._get_overall_conclusion()}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

报告生成者: WiFi专业工具 v1.6.3
技术标准:   IEEE 802.11 (WiFi联盟认证)
"""
        
        return report
    
    def _dbm_to_percent(self, dbm: float) -> float:
        """dBm转百分比"""
        return max(0, min(100, (dbm + 90) * 100 / 60))
    
    def _get_signal_grade(self, dbm: float) -> Tuple[str, str, str]:
        """获取信号等级"""
        for key, (min_dbm, max_dbm, name, desc) in self.SIGNAL_GRADES.items():
            if min_dbm <= dbm < max_dbm:
                return (key, name, desc)
        return ('critical', '极差', '不可用')
    
    def _analyze_quality_distribution(self) -> Dict:
        """分析信号质量分布"""
        distribution = {}
        total = len(self.measurement_data)
        
        for key, (min_dbm, max_dbm, name, _) in self.SIGNAL_GRADES.items():
            count = sum(1 for p in self.measurement_data 
                       if min_dbm <= p['signal_dbm'] < max_dbm)
            distribution[key] = {
                'name': name,
                'range': f'{min_dbm}~{max_dbm} dBm',
                'count': count,
                'percentage': (count / total * 100) if total > 0 else 0
            }
        
        return distribution
    
    def _get_uniformity_assessment(self, level: str) -> str:
        """获取均匀性评估"""
        assessments = {
            'excellent': '信号分布非常均匀，网络质量稳定',
            'good': '信号分布较均匀，整体表现良好',
            'fair': '信号波动较大，建议优化AP位置',
            'poor': '信号分布极不均匀，需重新规划'
        }
        return assessments.get(level, '未知')
    
    def _detect_over_coverage(self) -> Dict:
        """检测过度覆盖"""
        # 简化版：检测信号强度过高的区域
        strong_signals = [p for p in self.measurement_data if p['signal_dbm'] > -40]
        overlap_count = len(strong_signals)
        waste_rate = (overlap_count / len(self.measurement_data)) * 100 if self.measurement_data else 0
        
        if waste_rate > 30:
            suggestion = "存在严重过度覆盖，建议减少AP数量或降低功率"
        elif waste_rate > 15:
            suggestion = "存在轻度过度覆盖，可适当调整AP功率"
        else:
            suggestion = "覆盖合理，无明显资源浪费"
        
        return {
            'overlap_count': overlap_count,
            'waste_rate': waste_rate,
            'suggestion': suggestion
        }
    
    def _estimate_capacity(self, area_sqm: float, avg_signal: float, scenario: str) -> Dict:
        """估算网络容量"""
        # 基于面积和信号质量估算
        # WiFi 6: 每AP约50用户 (高密度)
        # WiFi 5: 每AP约30用户 (普通)
        
        req = self.SCENARIO_REQUIREMENTS[scenario]
        
        if 'WiFi 6' in req['recommended_standard']:
            users_per_ap = 50
            ap_coverage = 200  # 平方米
        elif 'WiFi 5' in req['recommended_standard']:
            users_per_ap = 30
            ap_coverage = 150
        else:
            users_per_ap = 20
            ap_coverage = 100
        
        # 根据信号质量调整
        if avg_signal > -50:
            users_per_ap = int(users_per_ap * 1.2)
        elif avg_signal < -70:
            users_per_ap = int(users_per_ap * 0.6)
        
        recommended_aps = max(1, int(np.ceil(area_sqm / ap_coverage)))
        estimated_users = recommended_aps * users_per_ap
        user_density = (estimated_users / area_sqm) * 100
        
        if user_density > 30:
            capacity_level = '高密度'
        elif user_density > 15:
            capacity_level = '中密度'
        else:
            capacity_level = '低密度'
        
        return {
            'estimated_users': estimated_users,
            'recommended_aps': recommended_aps,
            'user_density': user_density,
            'capacity_level': capacity_level
        }
    
    def _check_compliance(self, scenario: str, coverage_rate: float, avg_signal: float) -> Dict:
        """检查合规性"""
        req = self.SCENARIO_REQUIREMENTS[scenario]
        
        items = {
            '覆盖率要求': coverage_rate >= req['coverage_rate'],
            '信号强度要求': avg_signal >= req['min_signal'],
            '数据完整性': len(self.measurement_data) >= 10
        }
        
        overall = 'PASSED' if all(items.values()) else 'FAILED'
        
        return {
            'overall': overall,
            'items': items
        }
    
    def _generate_recommendations(self, coverage_rate: float, avg_signal: float,
                                 weak_zones: List, over_coverage: Dict, scenario: str) -> Dict:
        """生成改进建议"""
        p0, p1, p2 = [], [], []
        
        # P0 - 立即执行
        if coverage_rate < 90:
            p0.append(f"覆盖率仅{coverage_rate:.1f}%，需增加AP或调整位置")
        
        if len(weak_zones) > 5:
            p0.append(f"发现{len(weak_zones)}处弱信号区域，需重点优化")
        
        if avg_signal < -70:
            p0.append("平均信号过弱，建议增加AP数量或提升发射功率")
        
        # P1 - 建议执行
        if over_coverage['waste_rate'] > 15:
            p1.append("存在过度覆盖，可优化AP位置降低功耗")
        
        if len(self.measurement_data) < 20:
            p1.append("测量点数量较少，建议增加测量密度")
        
        req = self.SCENARIO_REQUIREMENTS[scenario]
        p1.append(f"建议使用{req['recommended_standard']}标准以满足场景需求")
        
        # P2 - 长期优化
        p2.append("定期复测信号覆盖，建立长期监测机制")
        p2.append("考虑部署智能天线系统，提升覆盖效率")
        p2.append("建议接入网络管理平台，实现自动化运维")
        
        if not p0:
            p0.append("当前网络状态良好，继续保持")
        
        return {'p0': p0, 'p1': p1, 'p2': p2}
    
    def _calculate_overall_score(self) -> float:
        """计算综合评分"""
        if not self.analysis_result:
            return 0.0
        
        r = self.analysis_result
        score = 0.0
        
        # 覆盖率 (40分)
        score += min(40, (r['coverage']['rate'] / r['coverage']['requirement']) * 40)
        
        # 信号强度 (30分)
        avg_signal = r['signal_stats']['average']
        if avg_signal >= -50:
            score += 30
        elif avg_signal >= -60:
            score += 25
        elif avg_signal >= -70:
            score += 20
        else:
            score += 10
        
        # 均匀性 (20分)
        uniformity_scores = {'excellent': 20, 'good': 15, 'fair': 10, 'poor': 5}
        score += uniformity_scores.get(r['uniformity']['level'], 0)
        
        # 合规性 (10分)
        if r['compliance']['overall'] == 'PASSED':
            score += 10
        
        return min(100, score)
    
    def _get_overall_conclusion(self) -> str:
        """获取总体结论"""
        score = self._calculate_overall_score()
        
        if score >= 90:
            return "网络覆盖优秀，完全满足使用需求"
        elif score >= 75:
            return "网络覆盖良好，基本满足使用需求"
        elif score >= 60:
            return "网络覆盖一般，建议进行优化改善"
        else:
            return "网络覆盖不佳，需要重新规划部署"
