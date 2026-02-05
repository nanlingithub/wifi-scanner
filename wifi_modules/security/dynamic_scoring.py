#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
动态权重评分系统
功能：根据网络类型、威胁环境自适应调整安全评分权重
版本：V1.0
"""

from typing import Dict, List, Optional
from enum import Enum


class NetworkType(Enum):
    """网络类型枚举"""
    HOME = "家用网络"
    ENTERPRISE = "企业网络"
    PUBLIC = "公共网络"
    GUEST = "访客网络"
    IOT = "物联网网络"
    UNKNOWN = "未知类型"


class ThreatLevel(Enum):
    """威胁等级枚举"""
    LOW = "低威胁"
    MEDIUM = "中等威胁"
    HIGH = "高威胁"
    CRITICAL = "严重威胁"


class DynamicScoring:
    """动态权重评分系统"""
    
    # 基础权重配置（原SecurityScoreCalculator的权重）
    BASE_WEIGHTS = {
        'encryption': 0.30,      # 加密强度
        'wps': 0.25,             # WPS漏洞
        'password': 0.20,        # 密码强度
        'management': 0.15,      # 管理配置
        'exposure': 0.10         # 信号暴露
    }
    
    # 网络类型权重调整矩阵
    NETWORK_TYPE_WEIGHTS = {
        NetworkType.HOME: {
            'encryption': 0.25,   # 家用网络：密码和WPS更重要
            'wps': 0.30,
            'password': 0.25,
            'management': 0.10,
            'exposure': 0.10
        },
        NetworkType.ENTERPRISE: {
            'encryption': 0.35,   # 企业网络：加密和管理更重要
            'wps': 0.15,
            'password': 0.20,
            'management': 0.25,
            'exposure': 0.05
        },
        NetworkType.PUBLIC: {
            'encryption': 0.20,   # 公共网络：暴露和劫持更重要
            'wps': 0.15,
            'password': 0.15,
            'management': 0.20,
            'exposure': 0.30
        },
        NetworkType.GUEST: {
            'encryption': 0.25,   # 访客网络：隔离和加密重要
            'wps': 0.20,
            'password': 0.20,
            'management': 0.20,
            'exposure': 0.15
        },
        NetworkType.IOT: {
            'encryption': 0.30,   # 物联网：安全性最重要
            'wps': 0.35,
            'password': 0.20,
            'management': 0.10,
            'exposure': 0.05
        },
        NetworkType.UNKNOWN: {
            'encryption': 0.30,   # 未知类型：使用基础权重
            'wps': 0.25,
            'password': 0.20,
            'management': 0.15,
            'exposure': 0.10
        }
    }
    
    # 威胁等级调整系数
    THREAT_MODIFIERS = {
        ThreatLevel.LOW: {
            'encryption': 1.0,
            'wps': 1.0,
            'password': 1.0,
            'management': 1.0,
            'exposure': 1.0
        },
        ThreatLevel.MEDIUM: {
            'encryption': 1.1,
            'wps': 1.2,
            'password': 1.1,
            'management': 1.0,
            'exposure': 1.1
        },
        ThreatLevel.HIGH: {
            'encryption': 1.2,
            'wps': 1.4,
            'password': 1.3,
            'management': 1.1,
            'exposure': 1.3
        },
        ThreatLevel.CRITICAL: {
            'encryption': 1.3,
            'wps': 1.5,
            'password': 1.4,
            'management': 1.2,
            'exposure': 1.4
        }
    }
    
    def __init__(self):
        """初始化动态评分系统"""
        self.current_network_type = NetworkType.UNKNOWN
        self.current_threat_level = ThreatLevel.MEDIUM
        self.active_weights = self.BASE_WEIGHTS.copy()
    
    def detect_network_type(self, network_info: Dict) -> NetworkType:
        """
        检测网络类型
        
        Args:
            network_info: 网络信息字典
                - ssid: 网络名称
                - authentication: 认证方式
                - channel: 信道
                - signal: 信号强度
                - vendor: 厂商
                
        Returns:
            网络类型
        """
        ssid = network_info.get('ssid', '').lower()
        auth = network_info.get('authentication', '').lower()
        
        # 企业网络特征
        if any(keyword in ssid for keyword in ['corp', 'office', 'company', 'enterprise', 'work']):
            return NetworkType.ENTERPRISE
        
        # 访客网络特征
        if any(keyword in ssid for keyword in ['guest', 'visitor', 'public wifi']):
            return NetworkType.GUEST
        
        # 公共网络特征
        if any(keyword in ssid for keyword in ['starbucks', 'mcdonalds', 'airport', 'hotel', 
                                                'cafe', 'restaurant', 'free', 'public']):
            return NetworkType.PUBLIC
        
        # 物联网网络特征
        if any(keyword in ssid for keyword in ['iot', 'smart', 'camera', 'device']):
            return NetworkType.IOT
        
        # 家用网络特征（默认）
        if auth in ['wpa2-personal', 'wpa-personal', 'wpa3-personal']:
            return NetworkType.HOME
        
        return NetworkType.UNKNOWN
    
    def assess_threat_level(self, security_issues: Dict) -> ThreatLevel:
        """
        评估威胁等级
        
        Args:
            security_issues: 安全问题字典
                - wps_vulnerable: WPS漏洞
                - weak_encryption: 弱加密
                - weak_password: 弱密码
                - dns_hijacked: DNS劫持
                - evil_twin: 伪AP
                
        Returns:
            威胁等级
        """
        threat_score = 0
        
        # WPS漏洞（高危）
        if security_issues.get('wps_vulnerable'):
            severity = security_issues.get('wps_severity', 'LOW')
            if severity == 'CRITICAL':
                threat_score += 40
            elif severity == 'HIGH':
                threat_score += 30
            else:
                threat_score += 20
        
        # 弱加密（严重）
        if security_issues.get('weak_encryption'):
            encryption = security_issues.get('encryption_type', '')
            if encryption in ['Open', 'WEP']:
                threat_score += 35
            elif encryption in ['WPA', 'WPA-TKIP']:
                threat_score += 20
        
        # 弱密码
        if security_issues.get('weak_password'):
            pwd_score = security_issues.get('password_score', 50)
            if pwd_score < 30:
                threat_score += 25
            elif pwd_score < 50:
                threat_score += 15
        
        # DNS劫持（严重）
        if security_issues.get('dns_hijacked'):
            threat_score += 30
        
        # 伪AP检测（严重）
        if security_issues.get('evil_twin'):
            threat_score += 35
        
        # 其他威胁
        threat_score += security_issues.get('other_issues', 0) * 5
        
        # 确定威胁等级
        if threat_score >= 80:
            return ThreatLevel.CRITICAL
        elif threat_score >= 50:
            return ThreatLevel.HIGH
        elif threat_score >= 20:
            return ThreatLevel.MEDIUM
        else:
            return ThreatLevel.LOW
    
    def calculate_dynamic_weights(self, network_info: Dict, 
                                 security_issues: Dict) -> Dict[str, float]:
        """
        计算动态权重
        
        Args:
            network_info: 网络信息
            security_issues: 安全问题
            
        Returns:
            动态权重字典
        """
        # 检测网络类型
        network_type = self.detect_network_type(network_info)
        self.current_network_type = network_type
        
        # 评估威胁等级
        threat_level = self.assess_threat_level(security_issues)
        self.current_threat_level = threat_level
        
        # 获取基础权重
        base_weights = self.NETWORK_TYPE_WEIGHTS.get(
            network_type, 
            self.BASE_WEIGHTS
        )
        
        # 应用威胁等级调整
        threat_modifiers = self.THREAT_MODIFIERS[threat_level]
        
        # 计算动态权重
        dynamic_weights = {}
        for key in base_weights:
            adjusted_weight = base_weights[key] * threat_modifiers[key]
            dynamic_weights[key] = adjusted_weight
        
        # 归一化（确保总和为1.0）
        total_weight = sum(dynamic_weights.values())
        for key in dynamic_weights:
            dynamic_weights[key] /= total_weight
        
        self.active_weights = dynamic_weights
        return dynamic_weights
    
    def calculate_score(self, component_scores: Dict[str, float], 
                       network_info: Dict = None,
                       security_issues: Dict = None) -> Dict:
        """
        计算动态评分
        
        Args:
            component_scores: 各组件分数
                - encryption: 加密分数 (0-100)
                - wps: WPS分数 (0-100)
                - password: 密码分数 (0-100)
                - management: 管理分数 (0-100)
                - exposure: 暴露分数 (0-100)
            network_info: 网络信息（可选）
            security_issues: 安全问题（可选）
            
        Returns:
            评分结果字典
        """
        # 如果提供了网络信息和安全问题，重新计算权重
        if network_info and security_issues:
            weights = self.calculate_dynamic_weights(network_info, security_issues)
        else:
            weights = self.active_weights
        
        # 计算加权总分
        total_score = 0
        for component, score in component_scores.items():
            if component in weights:
                total_score += score * weights[component]
        
        # 生成结果
        result = {
            'total_score': round(total_score, 2),
            'network_type': self.current_network_type.value,
            'threat_level': self.current_threat_level.value,
            'active_weights': weights,
            'component_scores': component_scores,
            'breakdown': self._generate_breakdown(component_scores, weights)
        }
        
        return result
    
    def _generate_breakdown(self, component_scores: Dict[str, float], 
                           weights: Dict[str, float]) -> List[Dict]:
        """
        生成评分明细
        
        Args:
            component_scores: 组件分数
            weights: 权重
            
        Returns:
            评分明细列表
        """
        breakdown = []
        
        component_names = {
            'encryption': '加密强度',
            'wps': 'WPS安全',
            'password': '密码强度',
            'management': '管理配置',
            'exposure': '信号暴露'
        }
        
        for component, score in component_scores.items():
            if component in weights:
                breakdown.append({
                    'component': component_names.get(component, component),
                    'score': score,
                    'weight': weights[component],
                    'weighted_score': round(score * weights[component], 2)
                })
        
        # 按权重分数排序
        breakdown.sort(key=lambda x: x['weighted_score'], reverse=True)
        
        return breakdown
    
    def get_recommendations(self, result: Dict) -> List[str]:
        """
        生成针对性建议
        
        Args:
            result: 评分结果
            
        Returns:
            建议列表
        """
        recommendations = []
        
        network_type = self.current_network_type
        threat_level = self.current_threat_level
        
        # 基于网络类型的建议
        if network_type == NetworkType.HOME:
            recommendations.append("【家用网络建议】")
            recommendations.append("• 确保WPS功能已关闭")
            recommendations.append("• 使用强密码（12位以上，包含大小写+数字+符号）")
            recommendations.append("• 定期更换WiFi密码")
        
        elif network_type == NetworkType.ENTERPRISE:
            recommendations.append("【企业网络建议】")
            recommendations.append("• 使用WPA3-Enterprise加密")
            recommendations.append("• 启用802.1X认证")
            recommendations.append("• 定期审计接入设备")
            recommendations.append("• 部署网络入侵检测系统(NIDS)")
        
        elif network_type == NetworkType.PUBLIC:
            recommendations.append("【公共网络建议】")
            recommendations.append("⚠️ 避免在公共WiFi上进行敏感操作")
            recommendations.append("• 使用VPN加密流量")
            recommendations.append("• 验证WiFi名称的真实性")
            recommendations.append("• 关闭文件共享")
        
        elif network_type == NetworkType.IOT:
            recommendations.append("【物联网网络建议】")
            recommendations.append("• 使用独立VLAN隔离IoT设备")
            recommendations.append("• 更改设备默认密码")
            recommendations.append("• 定期更新设备固件")
        
        # 基于威胁等级的建议
        if threat_level == ThreatLevel.CRITICAL:
            recommendations.append("\n🚨 【严重威胁警告】")
            recommendations.append("• 立即断开网络连接")
            recommendations.append("• 检查路由器是否被入侵")
            recommendations.append("• 重置路由器到出厂设置")
            recommendations.append("• 更新路由器固件到最新版本")
        
        elif threat_level == ThreatLevel.HIGH:
            recommendations.append("\n⚠️ 【高威胁警告】")
            recommendations.append("• 尽快修复检测到的安全问题")
            recommendations.append("• 更换为更强的密码")
            recommendations.append("• 禁用不必要的服务")
        
        # 基于具体组件的建议
        breakdown = result.get('breakdown', [])
        if breakdown:
            lowest_component = breakdown[-1]
            if lowest_component['score'] < 50:
                recommendations.append(f"\n💡 【优先优化】{lowest_component['component']}")
        
        return recommendations


# 测试代码
if __name__ == '__main__':
    print("=" * 80)
    print("动态权重评分系统测试")
    print("=" * 80)
    
    scorer = DynamicScoring()
    
    # 测试场景1：家用网络
    print("\n【场景1】家用网络 - 中等威胁")
    print("-" * 80)
    
    network_info = {
        'ssid': 'MyHome-WiFi',
        'authentication': 'WPA2-Personal',
        'channel': 6,
        'signal': -45
    }
    
    security_issues = {
        'wps_vulnerable': True,
        'wps_severity': 'HIGH',
        'weak_encryption': False,
        'weak_password': True,
        'password_score': 45,
        'dns_hijacked': False,
        'evil_twin': False
    }
    
    component_scores = {
        'encryption': 85,
        'wps': 30,
        'password': 45,
        'management': 70,
        'exposure': 60
    }
    
    result = scorer.calculate_score(component_scores, network_info, security_issues)
    
    print(f"网络类型: {result['network_type']}")
    print(f"威胁等级: {result['threat_level']}")
    print(f"总分: {result['total_score']}/100")
    
    print("\n权重分配:")
    for comp, weight in result['active_weights'].items():
        print(f"  {comp}: {weight*100:.1f}%")
    
    print("\n评分明细:")
    for item in result['breakdown']:
        print(f"  {item['component']}: {item['score']}/100 × {item['weight']*100:.1f}% = {item['weighted_score']:.1f}")
    
    print("\n建议:")
    for rec in scorer.get_recommendations(result):
        print(rec)
    
    # 测试场景2：企业网络
    print("\n\n【场景2】企业网络 - 低威胁")
    print("-" * 80)
    
    network_info2 = {
        'ssid': 'Company-Corp',
        'authentication': 'WPA3-Enterprise',
        'channel': 11,
        'signal': -50
    }
    
    security_issues2 = {
        'wps_vulnerable': False,
        'weak_encryption': False,
        'weak_password': False,
        'password_score': 90,
        'dns_hijacked': False,
        'evil_twin': False
    }
    
    component_scores2 = {
        'encryption': 95,
        'wps': 95,
        'password': 90,
        'management': 85,
        'exposure': 90
    }
    
    result2 = scorer.calculate_score(component_scores2, network_info2, security_issues2)
    
    print(f"网络类型: {result2['network_type']}")
    print(f"威胁等级: {result2['threat_level']}")
    print(f"总分: {result2['total_score']}/100")
    
    # 测试场景3：公共网络
    print("\n\n【场景3】公共WiFi - 严重威胁")
    print("-" * 80)
    
    network_info3 = {
        'ssid': 'Starbucks Free WiFi',
        'authentication': 'Open',
        'channel': 1,
        'signal': -35
    }
    
    security_issues3 = {
        'wps_vulnerable': False,
        'weak_encryption': True,
        'encryption_type': 'Open',
        'weak_password': True,
        'password_score': 0,
        'dns_hijacked': True,
        'evil_twin': True
    }
    
    component_scores3 = {
        'encryption': 0,
        'wps': 50,
        'password': 0,
        'management': 30,
        'exposure': 20
    }
    
    result3 = scorer.calculate_score(component_scores3, network_info3, security_issues3)
    
    print(f"网络类型: {result3['network_type']}")
    print(f"威胁等级: {result3['threat_level']}")
    print(f"总分: {result3['total_score']}/100")
    
    print("\n权重分配 (对比基础权重):")
    base = DynamicScoring.BASE_WEIGHTS
    for comp in result3['active_weights']:
        active = result3['active_weights'][comp]
        baseline = base[comp]
        change = ((active - baseline) / baseline) * 100
        print(f"  {comp}: {active*100:.1f}% (基础: {baseline*100:.1f}%, 变化: {change:+.1f}%)")
    
    print("\n建议:")
    for rec in scorer.get_recommendations(result3):
        print(rec)
    
    print("\n" + "=" * 80)
    print("✅ 测试完成！")
