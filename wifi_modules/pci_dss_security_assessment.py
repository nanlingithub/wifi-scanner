#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PCI-DSS无线网络安全风险评估模块
功能：符合PCI-DSS标准的无线网络安全评估，检测加密、未授权AP、弱信号区域等
版本：1.6
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional
import re


class PCIDSSSecurityAssessment:
    """PCI-DSS无线网络安全风险评估器"""
    
    # PCI-DSS相关的无线安全要求
    PCI_DSS_REQUIREMENTS = {
        'req_1_2_3': '防火墙配置 - 限制无线网络连接',
        'req_2_1': '更改供应商默认设置',
        'req_4_1': '传输敏感数据时使用强加密',
        'req_11_1': '测试无线接入点的存在',
        'req_11_2': '定期扫描无线网络',
    }
    
    def __init__(self):
        self.assessment_results = {}
        self.security_risks = []
        self.compliance_status = {}
        
    def perform_assessment(self, wifi_data: List[Dict], 
                          authorized_aps: Optional[List[str]] = None) -> Dict:
        """
        执行PCI-DSS安全评估
        
        Args:
            wifi_data: WiFi扫描数据
            authorized_aps: 授权的AP MAC地址列表
            
        Returns:
            评估结果字典
        """
        if not wifi_data:
            return {
                'status': 'error',
                'message': '无WiFi数据可供评估'
            }
        
        self.security_risks = []
        authorized_aps = authorized_aps or []
        
        assessment = {
            'assessment_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_networks_detected': len(wifi_data),
            'encryption_analysis': self._analyze_encryption(wifi_data),
            'rogue_ap_detection': self._detect_rogue_aps(wifi_data, authorized_aps),
            'weak_signal_zones': self._identify_weak_zones(wifi_data),
            'vendor_default_detection': self._detect_vendor_defaults(wifi_data),
            'privacy_risks': self._assess_privacy_risks(wifi_data),
            'compliance_check': self._check_pci_compliance(wifi_data),
            'overall_risk_score': 0,
            'risk_level': '',
            'detailed_risks': self.security_risks
        }
        
        # 计算总体风险评分
        assessment['overall_risk_score'] = self._calculate_overall_risk()
        assessment['risk_level'] = self._get_risk_level(assessment['overall_risk_score'])
        
        self.assessment_results = assessment
        return assessment
    
    def _analyze_encryption(self, wifi_data: List[Dict]) -> Dict:
        """分析加密状态 (PCI-DSS Req 4.1)"""
        encryption_stats = {
            'WPA3_Enterprise': 0,
            'WPA3_Personal': 0,
            'WPA2_Enterprise': 0,
            'WPA2_Personal': 0,
            'WPA_Enterprise': 0,
            'WPA_Personal': 0,
            'WEP': 0,
            'Open': 0,
            'Unknown': 0
        }
        
        weak_encryption = []
        
        for network in wifi_data:
            ssid = network.get('ssid', 'Hidden')
            auth = network.get('authentication', 'Unknown').upper()
            signal = network.get('signal', -100)
            bssid = network.get('bssid', 'Unknown')
            
            # 分类加密类型
            # 支持中英文企业认证识别
            is_enterprise = 'ENTERPRISE' in auth or '802.1X' in auth or '企业' in auth
            
            if 'WPA3' in auth:
                if is_enterprise:
                    encryption_stats['WPA3_Enterprise'] += 1
                else:
                    encryption_stats['WPA3_Personal'] += 1
            elif 'WPA2' in auth:
                if is_enterprise:
                    encryption_stats['WPA2_Enterprise'] += 1
                else:
                    encryption_stats['WPA2_Personal'] += 1
            elif 'WPA' in auth:
                if is_enterprise:
                    encryption_stats['WPA_Enterprise'] += 1
                else:
                    encryption_stats['WPA_Personal'] += 1
                # WPA (非WPA2)被认为较弱
                weak_encryption.append({
                    'ssid': ssid,
                    'bssid': bssid,
                    'encryption': 'WPA',
                    'signal': signal,
                    'risk': 'medium'
                })
            elif 'WEP' in auth:
                encryption_stats['WEP'] += 1
                weak_encryption.append({
                    'ssid': ssid,
                    'bssid': bssid,
                    'encryption': 'WEP',
                    'signal': signal,
                    'risk': 'high'
                })
            elif 'OPEN' in auth or not auth:
                encryption_stats['Open'] += 1
                weak_encryption.append({
                    'ssid': ssid,
                    'bssid': bssid,
                    'encryption': 'Open',
                    'signal': signal,
                    'risk': 'critical'
                })
            else:
                encryption_stats['Unknown'] += 1
        
        # 添加风险记录
        if weak_encryption:
            self.security_risks.append({
                'requirement': 'PCI-DSS Req 4.1',
                'category': '弱加密检测',
                'severity': 'critical' if any(w['risk'] == 'critical' for w in weak_encryption) else 'high',
                'finding': f'发现{len(weak_encryption)}个使用弱加密或无加密的网络',
                'networks': weak_encryption,
                'remediation': '升级所有网络到WPA2-Enterprise或WPA3-Enterprise加密'
            })
        
        # 计算加密符合率
        total = len(wifi_data)
        compliant = (encryption_stats['WPA3_Enterprise'] + 
                    encryption_stats['WPA3_Personal'] +
                    encryption_stats['WPA2_Enterprise'] +
                    encryption_stats['WPA2_Personal'])
        compliance_rate = int((compliant / total * 100) if total > 0 else 0)
        
        return {
            'encryption_distribution': encryption_stats,
            'weak_encryption_count': len(weak_encryption),
            'compliance_rate': compliance_rate,
            'recommended_standard': 'WPA2-Enterprise (802.1X) 或 WPA3-Enterprise',
            'pci_compliant': len(weak_encryption) == 0
        }
    
    def _detect_rogue_aps(self, wifi_data: List[Dict], 
                         authorized_aps: List[str]) -> Dict:
        """检测未授权AP (PCI-DSS Req 11.1)"""
        rogue_aps = []
        suspicious_aps = []
        
        for network in wifi_data:
            bssid = network.get('bssid', '').upper()
            ssid = network.get('ssid', 'Hidden')
            signal = network.get('signal', -100)
            channel = network.get('channel', 0)
            auth = network.get('authentication', 'Unknown')
            
            # 检查是否在授权列表中
            if authorized_aps:
                is_authorized = any(auth_mac.upper() in bssid 
                                   for auth_mac in authorized_aps)
                
                if not is_authorized:
                    rogue_aps.append({
                        'ssid': ssid,
                        'bssid': bssid,
                        'signal': signal,
                        'channel': channel,
                        'encryption': auth,
                        'risk_reason': '未在授权AP列表中'
                    })
            
            # 检测可疑SSID模式
            suspicious_patterns = [
                r'.*free.*wifi.*',
                r'.*guest.*',
                r'.*public.*',
                r'.*test.*',
                r'^default$',
                r'.*setup.*',
                r'.*admin.*'
            ]
            
            for pattern in suspicious_patterns:
                if re.match(pattern, ssid.lower()):
                    suspicious_aps.append({
                        'ssid': ssid,
                        'bssid': bssid,
                        'signal': signal,
                        'pattern_matched': pattern,
                        'risk_reason': '可疑的SSID命名模式'
                    })
                    break
        
        # 添加风险记录
        if rogue_aps:
            self.security_risks.append({
                'requirement': 'PCI-DSS Req 11.1',
                'category': '未授权AP检测',
                'severity': 'critical',
                'finding': f'发现{len(rogue_aps)}个未授权的接入点',
                'networks': rogue_aps,
                'remediation': '立即调查并移除所有未授权AP，更新授权AP清单'
            })
        
        if suspicious_aps:
            self.security_risks.append({
                'requirement': 'PCI-DSS Req 11.1',
                'category': '可疑AP检测',
                'severity': 'high',
                'finding': f'发现{len(suspicious_aps)}个使用可疑SSID的网络',
                'networks': suspicious_aps,
                'remediation': '验证这些网络的合法性，考虑重命名为不易被仿冒的SSID'
            })
        
        return {
            'total_rogue_aps': len(rogue_aps),
            'suspicious_aps_count': len(suspicious_aps),
            'rogue_ap_details': rogue_aps,
            'suspicious_ap_details': suspicious_aps,
            'pci_compliant': len(rogue_aps) == 0
        }
    
    def _identify_weak_zones(self, wifi_data: List[Dict]) -> Dict:
        """识别弱信号区域"""
        weak_zones = []
        dead_zones = []
        
        # 按信号强度分类
        for network in wifi_data:
            signal = network.get('signal', -100)
            ssid = network.get('ssid', 'Hidden')
            bssid = network.get('bssid', 'Unknown')
            
            if signal < -85:  # 极弱信号
                dead_zones.append({
                    'ssid': ssid,
                    'bssid': bssid,
                    'signal': signal,
                    'issue': '信号极弱，可能存在覆盖盲区'
                })
            elif signal < -75:  # 弱信号
                weak_zones.append({
                    'ssid': ssid,
                    'bssid': bssid,
                    'signal': signal,
                    'issue': '信号较弱，可能影响连接质量'
                })
        
        # 弱信号可能导致安全问题
        if weak_zones or dead_zones:
            self.security_risks.append({
                'requirement': 'PCI-DSS Infrastructure',
                'category': '信号覆盖不足',
                'severity': 'medium',
                'finding': f'发现{len(weak_zones)}个弱信号区域和{len(dead_zones)}个盲区',
                'impact': '弱信号可能导致用户连接到未授权的强信号网络',
                'remediation': '优化AP部署，确保持卡人数据环境全面覆盖'
            })
        
        return {
            'weak_signal_count': len(weak_zones),
            'dead_zone_count': len(dead_zones),
            'weak_zones_details': weak_zones,
            'dead_zones_details': dead_zones,
            'coverage_adequate': len(dead_zones) == 0
        }
    
    def _detect_vendor_defaults(self, wifi_data: List[Dict]) -> Dict:
        """检测供应商默认配置 (PCI-DSS Req 2.1)"""
        default_ssids = [
            'linksys', 'netgear', 'dlink', 'tplink', 'asus', 
            'belkin', 'cisco', 'arris', 'motorola', 'technicolor',
            'default', 'wireless', 'wifi', '2wire', 'centurylink'
        ]
        
        default_configs = []
        
        for network in wifi_data:
            ssid = network.get('ssid', '').lower()
            bssid = network.get('bssid', 'Unknown')
            signal = network.get('signal', -100)
            
            # 检查是否使用默认SSID
            if any(default in ssid for default in default_ssids):
                default_configs.append({
                    'ssid': network.get('ssid', ''),
                    'bssid': bssid,
                    'signal': signal,
                    'issue': '可能使用供应商默认SSID',
                    'risk': 'medium'
                })
        
        if default_configs:
            self.security_risks.append({
                'requirement': 'PCI-DSS Req 2.1',
                'category': '供应商默认配置',
                'severity': 'high',
                'finding': f'发现{len(default_configs)}个可能使用默认配置的网络',
                'networks': default_configs,
                'remediation': '更改所有供应商默认SSID和密码，禁用默认管理账户'
            })
        
        return {
            'default_config_count': len(default_configs),
            'default_config_details': default_configs,
            'pci_compliant': len(default_configs) == 0
        }
    
    def _assess_privacy_risks(self, wifi_data: List[Dict]) -> Dict:
        """评估隐私风险"""
        privacy_risks = []
        
        # 检测广播SSID
        broadcast_count = sum(1 for n in wifi_data 
                             if n.get('ssid', '') != '' and n.get('ssid', '') != 'Hidden')
        
        # 检测包含敏感信息的SSID
        sensitive_patterns = [
            r'.*card.*',
            r'.*payment.*',
            r'.*pos.*',
            r'.*terminal.*',
            r'.*finance.*',
            r'.*bank.*'
        ]
        
        for network in wifi_data:
            ssid = network.get('ssid', '').lower()
            
            for pattern in sensitive_patterns:
                if re.match(pattern, ssid):
                    privacy_risks.append({
                        'ssid': network.get('ssid', ''),
                        'bssid': network.get('bssid', 'Unknown'),
                        'issue': 'SSID包含可能泄露业务信息的关键词',
                        'pattern': pattern
                    })
                    break
        
        if privacy_risks:
            self.security_risks.append({
                'requirement': 'PCI-DSS Privacy',
                'category': '隐私泄露风险',
                'severity': 'medium',
                'finding': f'发现{len(privacy_risks)}个SSID可能泄露敏感业务信息',
                'networks': privacy_risks,
                'remediation': '使用中性的SSID名称，避免透露业务用途'
            })
        
        return {
            'broadcast_ssid_count': broadcast_count,
            'sensitive_ssid_count': len(privacy_risks),
            'privacy_risk_details': privacy_risks
        }
    
    def _check_pci_compliance(self, wifi_data: List[Dict]) -> Dict:
        """检查PCI-DSS合规性"""
        compliance_checks = {}
        
        # Req 4.1: 强加密传输
        encryption_analysis = self.assessment_results.get('encryption_analysis', {}) \
                             if hasattr(self, 'assessment_results') else {}
        compliance_checks['req_4_1_encryption'] = {
            'requirement': 'PCI-DSS Req 4.1 - 传输敏感数据使用强加密',
            'status': 'compliant' if encryption_analysis.get('pci_compliant', False) else 'non-compliant',
            'details': f"加密合规率: {encryption_analysis.get('compliance_rate', 0)}%"
        }
        
        # Req 11.1: 无线接入点检测
        rogue_detection = self.assessment_results.get('rogue_ap_detection', {}) \
                         if hasattr(self, 'assessment_results') else {}
        compliance_checks['req_11_1_rogue_ap'] = {
            'requirement': 'PCI-DSS Req 11.1 - 测试无线接入点存在',
            'status': 'compliant' if rogue_detection.get('pci_compliant', False) else 'non-compliant',
            'details': f"未授权AP数量: {rogue_detection.get('total_rogue_aps', 0)}"
        }
        
        # Req 2.1: 更改默认配置
        vendor_defaults = self.assessment_results.get('vendor_default_detection', {}) \
                         if hasattr(self, 'assessment_results') else {}
        compliance_checks['req_2_1_defaults'] = {
            'requirement': 'PCI-DSS Req 2.1 - 更改供应商默认设置',
            'status': 'compliant' if vendor_defaults.get('pci_compliant', False) else 'non-compliant',
            'details': f"默认配置数量: {vendor_defaults.get('default_config_count', 0)}"
        }
        
        # 计算总体合规率
        total_checks = len(compliance_checks)
        compliant_checks = sum(1 for check in compliance_checks.values() 
                              if check['status'] == 'compliant')
        compliance_rate = int((compliant_checks / total_checks * 100) if total_checks > 0 else 0)
        
        return {
            'compliance_checks': compliance_checks,
            'total_checks': total_checks,
            'compliant_checks': compliant_checks,
            'compliance_rate': compliance_rate,
            'overall_status': 'compliant' if compliance_rate == 100 else 'non-compliant'
        }
    
    def _calculate_overall_risk(self) -> int:
        """计算总体风险评分 (0-100, 分数越低风险越高)"""
        if not self.security_risks:
            return 100
        
        severity_weights = {
            'critical': 40,
            'high': 25,
            'medium': 15,
            'low': 5
        }
        
        total_penalty = sum(severity_weights.get(risk['severity'], 10) 
                           for risk in self.security_risks)
        
        # 限制最大扣分
        total_penalty = min(100, total_penalty)
        risk_score = max(0, 100 - total_penalty)
        
        return risk_score
    
    def _get_risk_level(self, score: int) -> str:
        """获取风险等级"""
        if score >= 90:
            return '低风险 - 安全状况良好'
        elif score >= 70:
            return '中等风险 - 需要改进'
        elif score >= 50:
            return '高风险 - 存在明显安全问题'
        else:
            return '严重风险 - 立即采取行动'
    
    def generate_compliance_report(self) -> str:
        """生成PCI-DSS合规报告文本"""
        if not self.assessment_results:
            return "未进行评估"
        
        assessment = self.assessment_results
        
        report_lines = [
            "=" * 70,
            "PCI-DSS无线网络安全风险评估报告",
            "=" * 70,
            f"\n评估时间: {assessment.get('assessment_time', 'N/A')}",
            f"检测到的网络总数: {assessment.get('total_networks_detected', 0)}个",
            f"\n【总体风险评估】",
            f"  风险评分: {assessment.get('overall_risk_score', 0)}/100",
            f"  风险等级: {assessment.get('risk_level', 'N/A')}",
            f"  检测到的安全问题: {len(assessment.get('detailed_risks', []))}个",
        ]
        
        # 合规性检查
        compliance = assessment.get('compliance_check', {})
        report_lines.extend([
            f"\n【PCI-DSS合规性检查】",
            f"  总体状态: {compliance.get('overall_status', 'N/A').upper()}",
            f"  合规率: {compliance.get('compliance_rate', 0)}%",
            f"  通过检查: {compliance.get('compliant_checks', 0)}/{compliance.get('total_checks', 0)}"
        ])
        
        # 加密分析
        encryption = assessment.get('encryption_analysis', {})
        report_lines.extend([
            f"\n【加密状态分析】 (PCI-DSS Req 4.1)",
            f"  合规状态: {'✓ 合规' if encryption.get('pci_compliant', False) else '✗ 不合规'}",
            f"  弱加密网络: {encryption.get('weak_encryption_count', 0)}个",
            f"  加密合规率: {encryption.get('compliance_rate', 0)}%",
            f"  推荐标准: {encryption.get('recommended_standard', 'N/A')}"
        ])
        
        # 未授权AP检测
        rogue = assessment.get('rogue_ap_detection', {})
        report_lines.extend([
            f"\n【未授权AP检测】 (PCI-DSS Req 11.1)",
            f"  合规状态: {'✓ 合规' if rogue.get('pci_compliant', False) else '✗ 不合规'}",
            f"  未授权AP: {rogue.get('total_rogue_aps', 0)}个",
            f"  可疑AP: {rogue.get('suspicious_aps_count', 0)}个"
        ])
        
        # 供应商默认配置
        defaults = assessment.get('vendor_default_detection', {})
        report_lines.extend([
            f"\n【供应商默认配置检测】 (PCI-DSS Req 2.1)",
            f"  合规状态: {'✓ 合规' if defaults.get('pci_compliant', False) else '✗ 不合规'}",
            f"  默认配置网络: {defaults.get('default_config_count', 0)}个"
        ])
        
        # 覆盖问题
        weak_zones = assessment.get('weak_signal_zones', {})
        report_lines.extend([
            f"\n【信号覆盖分析】",
            f"  弱信号区域: {weak_zones.get('weak_signal_count', 0)}个",
            f"  覆盖盲区: {weak_zones.get('dead_zone_count', 0)}个",
            f"  覆盖状态: {'✓ 充足' if weak_zones.get('coverage_adequate', False) else '✗ 不足'}"
        ])
        
        # 详细风险列表
        risks = assessment.get('detailed_risks', [])
        if risks:
            report_lines.append(f"\n【详细安全风险】")
            for i, risk in enumerate(risks, 1):
                report_lines.append(f"\n  风险 {i}: [{risk['severity'].upper()}] {risk['category']}")
                report_lines.append(f"  相关要求: {risk['requirement']}")
                report_lines.append(f"  发现: {risk['finding']}")
                report_lines.append(f"  修复建议: {risk['remediation']}")
        
        # 总结
        report_lines.extend([
            f"\n{'=' * 70}",
            "【评估总结】",
        ])
        
        if assessment.get('overall_risk_score', 0) >= 90:
            report_lines.append("✓ 无线网络安全状况良好，符合PCI-DSS基本要求")
        else:
            report_lines.append("✗ 检测到安全问题，建议立即采取修复措施")
            report_lines.append("\n建议优先级:")
            critical_risks = [r for r in risks if r['severity'] == 'critical']
            high_risks = [r for r in risks if r['severity'] == 'high']
            
            if critical_risks:
                report_lines.append(f"  1. 【紧急】处理{len(critical_risks)}个严重风险")
            if high_risks:
                report_lines.append(f"  2. 【重要】处理{len(high_risks)}个高风险问题")
        
        report_lines.append("=" * 70)
        
        return "\n".join(report_lines)
    
    def export_to_json(self, filepath: str) -> bool:
        """导出评估结果为JSON"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.assessment_results, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"导出JSON失败: {e}")
            return False
