#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PCI-DSS无线网络安全风险评估模块
版本: 1.6
功能: 基于PCI-DSS标准进行无线网络安全评估
参考: PCI DSS v4.0 Requirements 2, 4, 11
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
import json


class PCIDSSAssessment:
    """PCI-DSS无线网络安全评估"""
    
    # PCI-DSS 无线安全要求
    PCI_REQUIREMENTS = {
        'REQ_2': {
            'title': '默认配置安全',
            'description': '不使用供应商提供的默认值',
            'tests': ['default_passwords', 'default_ssid', 'admin_access']
        },
        'REQ_4': {
            'title': '加密传输',
            'description': '加密开放公共网络传输持卡人数据',
            'tests': ['encryption_strength', 'wpa_version', 'open_networks']
        },
        'REQ_11': {
            'title': '安全测试',
            'description': '定期测试安全系统和流程',
            'tests': ['rogue_ap_detection', 'vulnerability_scan', 'penetration_test']
        }
    }
    
    def __init__(self):
        self.assessment_data = {}
        self.timestamp = datetime.now()
        self.risk_score = 0
        self.compliance_status = 'Unknown'
    
    def assess_network(self, wifi_data: List[Dict], network_config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        执行PCI-DSS安全评估
        
        Args:
            wifi_data: WiFi扫描数据
            network_config: 网络配置信息（可选）
            
        Returns:
            评估结果
        """
        if not wifi_data:
            return self._empty_assessment()
        
        assessment = {
            'timestamp': self.timestamp.isoformat(),
            'pci_dss_version': '4.0',
            'total_networks': len(wifi_data),
            'requirements': {},
            'findings': [],
            'risk_level': 'Unknown',
            'compliance_score': 0,
            'recommendations': []
        }
        
        # 评估各项要求
        assessment['requirements']['REQ_2'] = self._assess_req_2(wifi_data, network_config)
        assessment['requirements']['REQ_4'] = self._assess_req_4(wifi_data)
        assessment['requirements']['REQ_11'] = self._assess_req_11(wifi_data)
        
        # 汇总发现
        assessment['findings'] = self._collect_findings(assessment['requirements'])
        
        # 计算合规分数
        assessment['compliance_score'] = self._calculate_compliance_score(assessment['requirements'])
        
        # 确定风险级别
        assessment['risk_level'] = self._determine_risk_level(assessment['findings'])
        
        # 生成建议
        assessment['recommendations'] = self._generate_pci_recommendations(assessment)
        
        self.assessment_data = assessment
        self.risk_score = assessment['compliance_score']
        self.compliance_status = 'Compliant' if assessment['compliance_score'] >= 80 else 'Non-Compliant'
        
        return assessment
    
    def _empty_assessment(self) -> Dict:
        """空评估结果"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'pci_dss_version': '4.0',
            'total_networks': 0,
            'requirements': {},
            'findings': [],
            'risk_level': 'Unknown',
            'compliance_score': 0,
            'recommendations': []
        }
    
    def _assess_req_2(self, wifi_data: List[Dict], network_config: Optional[Dict]) -> Dict:
        """
        评估要求2: 默认配置安全
        
        检查项:
        - 默认SSID (如: TP-Link, NETGEAR, Linksys等)
        - 管理接口暴露
        - 默认凭据风险
        """
        findings = []
        score = 100
        
        # 检测默认SSID
        default_ssids = [
            'TP-Link', 'TPLINK', 'NETGEAR', 'Linksys', 'ASUS', 'D-Link',
            'Belkin', 'Buffalo', 'Huawei', 'ZTE', 'ChinaNet', 'ChinaUnicom'
        ]
        
        default_networks = []
        for network in wifi_data:
            ssid = network.get('ssid', '')
            for default_ssid in default_ssids:
                if default_ssid.lower() in ssid.lower():
                    default_networks.append(ssid)
                    break
        
        if default_networks:
            score -= 20
            findings.append({
                'severity': 'High',
                'requirement': 'REQ_2.2',
                'issue': f'发现 {len(default_networks)} 个使用默认SSID的网络',
                'details': f'网络列表: {", ".join(default_networks[:5])}{"..." if len(default_networks) > 5 else ""}',
                'remediation': '更改所有网络SSID为自定义名称，不使用设备型号或默认名称',
                'pci_reference': 'PCI DSS 2.2.1 - 配置标准应实施'
            })
        
        # 检测管理SSID
        admin_keywords = ['admin', '管理', 'config', 'setup', 'test']
        admin_networks = []
        for network in wifi_data:
            ssid = network.get('ssid', '').lower()
            if any(keyword in ssid for keyword in admin_keywords):
                admin_networks.append(network.get('ssid', ''))
        
        if admin_networks:
            score -= 15
            findings.append({
                'severity': 'Medium',
                'requirement': 'REQ_2.2.2',
                'issue': f'发现 {len(admin_networks)} 个疑似管理网络暴露',
                'details': f'网络列表: {", ".join(admin_networks)}',
                'remediation': '管理网络应使用单独的VLAN和隐藏SSID',
                'pci_reference': 'PCI DSS 2.2.2 - 启用必要的服务、协议和守护进程'
            })
        
        return {
            'title': self.PCI_REQUIREMENTS['REQ_2']['title'],
            'score': max(score, 0),
            'status': 'Pass' if score >= 80 else 'Fail',
            'findings': findings,
            'tests_performed': len(findings)
        }
    
    def _assess_req_4(self, wifi_data: List[Dict]) -> Dict:
        """
        评估要求4: 加密传输
        
        检查项:
        - 开放网络（无加密）
        - 弱加密（WEP, WPA）
        - 强加密（WPA2/WPA3）
        """
        findings = []
        score = 100
        
        # 统计加密类型
        encryption_stats = {
            'Open': [],
            'WEP': [],
            'WPA': [],
            'WPA2': [],
            'WPA3': []
        }
        
        for network in wifi_data:
            ssid = network.get('ssid', 'Unknown')
            security = network.get('security', 'Unknown')
            
            if security == 'Open' or 'Open' in security:
                encryption_stats['Open'].append(ssid)
            elif 'WEP' in security:
                encryption_stats['WEP'].append(ssid)
            elif 'WPA3' in security:
                encryption_stats['WPA3'].append(ssid)
            elif 'WPA2' in security:
                encryption_stats['WPA2'].append(ssid)
            elif 'WPA' in security:
                encryption_stats['WPA'].append(ssid)
        
        # 开放网络 - 严重违规
        if encryption_stats['Open']:
            score -= 40
            findings.append({
                'severity': 'Critical',
                'requirement': 'REQ_4.1.1',
                'issue': f'发现 {len(encryption_stats["Open"])} 个开放网络（无加密）',
                'details': f'网络列表: {", ".join(encryption_stats["Open"][:5])}{"..." if len(encryption_stats["Open"]) > 5 else ""}',
                'remediation': '所有无线网络必须启用WPA2或WPA3加密',
                'pci_reference': 'PCI DSS 4.1 - 使用强加密和安全协议保护传输中的持卡人数据'
            })
        
        # WEP加密 - 严重违规
        if encryption_stats['WEP']:
            score -= 35
            findings.append({
                'severity': 'Critical',
                'requirement': 'REQ_4.1.1',
                'issue': f'发现 {len(encryption_stats["WEP"])} 个使用WEP加密的网络',
                'details': f'WEP加密已被破解，网络列表: {", ".join(encryption_stats["WEP"])}',
                'remediation': '立即升级到WPA2-AES或WPA3加密',
                'pci_reference': 'PCI DSS 4.1 - WEP不被视为强加密'
            })
        
        # WPA加密 - 高风险
        if encryption_stats['WPA']:
            score -= 20
            findings.append({
                'severity': 'High',
                'requirement': 'REQ_4.1',
                'issue': f'发现 {len(encryption_stats["WPA"])} 个使用旧版WPA加密的网络',
                'details': f'网络列表: {", ".join(encryption_stats["WPA"])}',
                'remediation': '升级到WPA2-AES或WPA3',
                'pci_reference': 'PCI DSS 4.1 - 建议使用当前最佳实践'
            })
        
        # 无WPA2/WPA3
        if not encryption_stats['WPA2'] and not encryption_stats['WPA3']:
            score -= 50
            findings.append({
                'severity': 'Critical',
                'requirement': 'REQ_4.1',
                'issue': '未检测到任何WPA2或WPA3加密网络',
                'details': '所有网络均使用弱加密或无加密',
                'remediation': '部署符合PCI-DSS标准的WPA2/WPA3加密网络',
                'pci_reference': 'PCI DSS 4.1'
            })
        
        # 推荐WPA3
        if encryption_stats['WPA2'] and not encryption_stats['WPA3']:
            findings.append({
                'severity': 'Low',
                'requirement': 'REQ_4.1',
                'issue': '未使用最新的WPA3加密标准',
                'details': f'当前有{len(encryption_stats["WPA2"])}个WPA2网络',
                'remediation': '建议逐步升级到WPA3以获得更好的安全性',
                'pci_reference': 'PCI DSS 最佳实践'
            })
        
        return {
            'title': self.PCI_REQUIREMENTS['REQ_4']['title'],
            'score': max(score, 0),
            'status': 'Pass' if score >= 80 else 'Fail',
            'findings': findings,
            'encryption_distribution': {
                'Open': len(encryption_stats['Open']),
                'WEP': len(encryption_stats['WEP']),
                'WPA': len(encryption_stats['WPA']),
                'WPA2': len(encryption_stats['WPA2']),
                'WPA3': len(encryption_stats['WPA3'])
            }
        }
    
    def _assess_req_11(self, wifi_data: List[Dict]) -> Dict:
        """
        评估要求11: 安全测试
        
        检查项:
        - 未授权AP检测（Rogue AP）
        - 信号覆盖范围
        - 可疑设备
        """
        findings = []
        score = 100
        
        # 检测疑似未授权AP
        # 基于信号强度和常见模式判断
        suspicious_aps = []
        weak_signal_aps = []
        
        for network in wifi_data:
            ssid = network.get('ssid', '')
            signal = network.get('signal', -100)
            security = network.get('security', '')
            
            # 信号异常强（可能在内部）且使用开放网络
            if signal > -40 and ('Open' in security or security == 'Open'):
                suspicious_aps.append({
                    'ssid': ssid,
                    'signal': signal,
                    'security': security,
                    'reason': '强信号开放网络'
                })
            
            # 弱信号可能来自外部
            if signal < -80:
                weak_signal_aps.append(ssid)
        
        if suspicious_aps:
            score -= 25
            findings.append({
                'severity': 'High',
                'requirement': 'REQ_11.2.1',
                'issue': f'检测到 {len(suspicious_aps)} 个疑似未授权AP',
                'details': f'发现强信号开放网络，可能是恶意AP或配置错误: {", ".join([ap["ssid"] for ap in suspicious_aps[:3]])}',
                'remediation': '1. 验证这些AP是否授权\n2. 实施无线IDS/IPS系统\n3. 定期进行Rogue AP扫描',
                'pci_reference': 'PCI DSS 11.2.1 - 至少每季度进行无线分析'
            })
        
        # 检测测试/临时网络
        test_keywords = ['test', 'temp', 'guest', '测试', '临时', 'demo']
        test_networks = []
        for network in wifi_data:
            ssid = network.get('ssid', '').lower()
            if any(keyword in ssid for keyword in test_keywords):
                test_networks.append(network.get('ssid', ''))
        
        if test_networks:
            score -= 15
            findings.append({
                'severity': 'Medium',
                'requirement': 'REQ_11.3',
                'issue': f'发现 {len(test_networks)} 个疑似测试/临时网络',
                'details': f'网络列表: {", ".join(test_networks)}',
                'remediation': '移除所有测试和临时网络，或确保其符合安全标准',
                'pci_reference': 'PCI DSS 11.3 - 实施变更检测机制'
            })
        
        # 建议实施监控
        findings.append({
            'severity': 'Info',
            'requirement': 'REQ_11.2',
            'issue': '无线网络安全监控建议',
            'details': f'当前检测到 {len(wifi_data)} 个网络',
            'remediation': '建议:\n1. 部署无线入侵检测系统(WIDS)\n2. 至少每季度进行无线网络扫描\n3. 记录所有授权AP的MAC地址',
            'pci_reference': 'PCI DSS 11.2 - 安全测试程序'
        })
        
        return {
            'title': self.PCI_REQUIREMENTS['REQ_11']['title'],
            'score': max(score, 0),
            'status': 'Pass' if score >= 80 else 'Fail',
            'findings': findings,
            'suspicious_aps_detected': len(suspicious_aps),
            'test_networks_detected': len(test_networks)
        }
    
    def _collect_findings(self, requirements: Dict) -> List[Dict]:
        """汇总所有发现"""
        all_findings = []
        
        for req_key, req_data in requirements.items():
            findings = req_data.get('findings', [])
            for finding in findings:
                finding['requirement_group'] = req_key
                all_findings.append(finding)
        
        # 按严重性排序
        severity_order = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3, 'Info': 4}
        all_findings.sort(key=lambda x: severity_order.get(x['severity'], 999))
        
        return all_findings
    
    def _calculate_compliance_score(self, requirements: Dict) -> float:
        """计算整体合规分数"""
        if not requirements:
            return 0
        
        total_score = sum(req['score'] for req in requirements.values())
        avg_score = total_score / len(requirements)
        
        return round(avg_score, 2)
    
    def _determine_risk_level(self, findings: List[Dict]) -> str:
        """确定风险级别"""
        critical_count = sum(1 for f in findings if f['severity'] == 'Critical')
        high_count = sum(1 for f in findings if f['severity'] == 'High')
        
        if critical_count > 0:
            return 'Critical'
        elif high_count >= 3:
            return 'High'
        elif high_count > 0:
            return 'Medium'
        else:
            return 'Low'
    
    def _generate_pci_recommendations(self, assessment: Dict) -> List[Dict]:
        """生成PCI-DSS合规建议"""
        recommendations = []
        
        compliance_score = assessment['compliance_score']
        
        # 基于分数的建议
        if compliance_score < 60:
            recommendations.append({
                'priority': 'Critical',
                'category': 'Overall Compliance',
                'action': '立即整改',
                'description': f'当前合规分数仅{compliance_score}/100，存在严重安全隐患',
                'steps': [
                    '1. 识别并修复所有Critical级别的问题',
                    '2. 建立无线网络安全策略',
                    '3. 实施WPA2/WPA3加密',
                    '4. 部署无线入侵检测系统'
                ],
                'timeline': '立即 - 1周内'
            })
        elif compliance_score < 80:
            recommendations.append({
                'priority': 'High',
                'category': 'Compliance Improvement',
                'action': '改进建议',
                'description': f'当前合规分数{compliance_score}/100，需要改进',
                'steps': [
                    '1. 修复High级别的安全问题',
                    '2. 定期进行安全评估',
                    '3. 更新无线网络配置标准'
                ],
                'timeline': '1-2周内'
            })
        
        # 基于发现的具体建议
        critical_findings = [f for f in assessment['findings'] if f['severity'] == 'Critical']
        if critical_findings:
            recommendations.append({
                'priority': 'Critical',
                'category': 'Security Vulnerabilities',
                'action': '修复严重漏洞',
                'description': f'发现{len(critical_findings)}个严重安全问题',
                'steps': [f['remediation'] for f in critical_findings[:3]],
                'timeline': '立即'
            })
        
        # 最佳实践建议
        recommendations.append({
            'priority': 'Medium',
            'category': 'Best Practices',
            'action': 'PCI-DSS最佳实践',
            'description': '建议实施的安全措施',
            'steps': [
                '1. 至少每季度进行无线网络安全评估',
                '2. 维护授权AP清单',
                '3. 实施802.1X认证',
                '4. 隔离持卡人数据环境（CDE）',
                '5. 记录无线网络访问日志'
            ],
            'timeline': '持续实施'
        })
        
        return recommendations
    
    def export_to_json(self, filepath: str) -> bool:
        """导出评估结果到JSON"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.assessment_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"导出JSON失败: {e}")
            return False
    
    def generate_executive_summary(self) -> str:
        """生成执行摘要"""
        if not self.assessment_data:
            return "暂无评估数据"
        
        data = self.assessment_data
        
        summary = f"""
PCI-DSS无线网络安全评估 - 执行摘要
{'='*60}
评估时间: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
PCI-DSS版本: {data.get('pci_dss_version', 'N/A')}
评估网络数: {data.get('total_networks', 0)}

合规状态: {self.compliance_status}
合规分数: {data.get('compliance_score', 0)}/100
风险级别: {data.get('risk_level', 'Unknown')}

关键发现:
{'='*60}
"""
        
        # 按严重性统计
        findings = data.get('findings', [])
        critical = len([f for f in findings if f['severity'] == 'Critical'])
        high = len([f for f in findings if f['severity'] == 'High'])
        medium = len([f for f in findings if f['severity'] == 'Medium'])
        
        summary += f"""
严重 (Critical): {critical}
高   (High):     {high}
中   (Medium):   {medium}

要求评估结果:
{'='*60}
"""
        
        for req_key, req_data in data.get('requirements', {}).items():
            summary += f"{req_key} - {req_data['title']}: {req_data['status']} (分数: {req_data['score']}/100)\n"
        
        summary += f"""
{'='*60}
建议措施数: {len(data.get('recommendations', []))}

注: 此摘要基于自动化扫描结果，建议结合人工审核和渗透测试
"""
        
        return summary
