"""
PCI-DSS无线网络安全风险评估模块
基于PCI-DSS标准评估WiFi网络的安全风险
支持生成符合合规要求的安全评估报告
版本: 1.7 - 集成配置加载器和日志系统
"""

from datetime import datetime
from typing import Dict, List, Tuple
import re
import json

# 新增：导入配置加载器和日志系统
from wifi_modules.config_loader import ConfigLoader
from wifi_modules.logger import get_logger

class PCIDSSSecurityAssessor:
    """PCI-DSS无线网络安全评估器"""
    
    def __init__(self):
        """初始化评估器"""
        # 初始化配置加载器和日志系统
        self.config = ConfigLoader()
        self.logger = get_logger('PCIDSSSecurityAssessor')
        self.logger.info("PCI-DSS安全评估器初始化")
        
        # 从配置文件加载合规等级阈值
        compliance_config = self.config.get('security.compliance_levels')
        self.full_compliance_threshold = compliance_config.get('full', 90) if compliance_config else 90
        self.partial_compliance_threshold = compliance_config.get('partial', 70) if compliance_config else 70
        
        # 评估状态
        self.assessment_time = None
        self.networks_assessed = []
    
    # PCI-DSS 4.0 无线安全要求
    PCI_REQUIREMENTS = {
        '2.1.1': '更改供应商提供的默认值',
        '4.1': '加密传输的持卡人数据',
        '11.2': '执行内部和外部网络脆弱性扫描',
        '11.3': '执行渗透测试',
        '12.3': '制定关键技术的使用策略'
    }
    
    # 安全加密类型评级
    ENCRYPTION_RATINGS = {
        'WPA3': {'score': 100, 'level': '优秀', 'compliant': True},
        'WPA2-Enterprise': {'score': 90, 'level': '良好', 'compliant': True},
        'WPA2': {'score': 70, 'level': '一般', 'compliant': True},
        'WPA': {'score': 30, 'level': '较差', 'compliant': False},
        'WEP': {'score': 10, 'level': '极差', 'compliant': False},
        'Open': {'score': 0, 'level': '不安全', 'compliant': False},
        '未知': {'score': 0, 'level': '未知', 'compliant': False}
    }
    
    def perform_security_assessment(self, networks: List[Dict]) -> Dict:
        """
        执行PCI-DSS安全评估
        
        Args:
            networks: 网络列表数据
            
        Returns:
            安全评估结果字典
        """
        self.assessment_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.networks_assessed = networks
        
        results = {
            'assessment_time': self.assessment_time,
            'total_networks': len(networks),
            'encryption_analysis': self._analyze_encryption(networks),
            'authentication_analysis': self._analyze_authentication(networks),
            'compliance_status': self._check_compliance(networks),
            'risk_assessment': self._assess_risks(networks),
            'vulnerability_scan': self._scan_vulnerabilities(networks),
            'recommendations': self._generate_security_recommendations(networks),
            'overall_score': 0,
            'compliance_level': ''
        }
        
        # 计算总体得分
        results['overall_score'] = self._calculate_overall_score(results)
        results['compliance_level'] = self._determine_compliance_level(results)
        
        return results
    
    def _analyze_encryption(self, networks: List[Dict]) -> Dict:
        """分析加密方式"""
        encryption_stats = {}
        total_aps = 0
        
        for network in networks:
            encryption = network.get('encryption', '未知')
            # 标准化加密类型名称
            encryption = self._normalize_encryption_type(encryption)
            
            ap_count = network.get('ap_count', len(network.get('bssids', [])))
            
            if encryption not in encryption_stats:
                encryption_stats[encryption] = {
                    'count': 0,
                    'networks': [],
                    'rating': self.ENCRYPTION_RATINGS.get(encryption, self.ENCRYPTION_RATINGS['未知'])
                }
            
            encryption_stats[encryption]['count'] += ap_count
            encryption_stats[encryption]['networks'].append(network['ssid'])
            total_aps += ap_count
        
        # 计算百分比
        for enc_type, data in encryption_stats.items():
            data['percentage'] = round(data['count'] / total_aps * 100, 1) if total_aps > 0 else 0
        
        return {
            'statistics': encryption_stats,
            'total_access_points': total_aps,
            'secure_percentage': self._calculate_secure_percentage(encryption_stats, total_aps),
            'weakest_encryption': self._find_weakest_encryption(encryption_stats)
        }
    
    def _normalize_encryption_type(self, encryption: str) -> str:
        """标准化加密类型名称"""
        encryption = encryption.upper()
        
        if 'WPA3' in encryption:
            return 'WPA3'
        elif 'WPA2' in encryption and 'ENTERPRISE' in encryption:
            return 'WPA2-Enterprise'
        elif 'WPA2' in encryption or 'CCMP' in encryption:
            return 'WPA2'
        elif 'WPA' in encryption and 'WPA2' not in encryption:
            return 'WPA'
        elif 'WEP' in encryption:
            return 'WEP'
        elif 'OPEN' in encryption or '开放' in encryption:
            return 'Open'
        else:
            return '未知'
    
    def _calculate_secure_percentage(self, encryption_stats: Dict, total_aps: int) -> float:
        """计算安全加密的百分比"""
        secure_count = sum(
            data['count'] for enc_type, data in encryption_stats.items()
            if self.ENCRYPTION_RATINGS.get(enc_type, {}).get('compliant', False)
        )
        return round(secure_count / total_aps * 100, 1) if total_aps > 0 else 0
    
    def _find_weakest_encryption(self, encryption_stats: Dict) -> Dict:
        """找出最弱的加密方式"""
        if not encryption_stats:
            return {'type': '无', 'count': 0}
        
        weakest = min(
            encryption_stats.items(),
            key=lambda x: self.ENCRYPTION_RATINGS.get(x[0], {}).get('score', 0)
        )
        
        return {
            'type': weakest[0],
            'count': weakest[1]['count'],
            'networks': weakest[1]['networks']
        }
    
    def _analyze_authentication(self, networks: List[Dict]) -> Dict:
        """分析身份验证方式"""
        auth_stats = {}
        
        for network in networks:
            auth = network.get('authentication', '未知')
            if auth not in auth_stats:
                auth_stats[auth] = {
                    'count': 0,
                    'networks': []
                }
            
            auth_stats[auth]['count'] += 1
            auth_stats[auth]['networks'].append(network['ssid'])
        
        # 评估身份验证强度
        # 支持中文和英文的企业认证识别
        enterprise_count = sum(
            data['count'] for auth, data in auth_stats.items()
            if 'Enterprise' in auth or '802.1X' in auth or '企业' in auth
        )
        
        return {
            'statistics': auth_stats,
            'enterprise_auth_count': enterprise_count,
            'enterprise_percentage': round(enterprise_count / len(networks) * 100, 1) if networks else 0,
            'recommendation': 'WPA2-Enterprise with 802.1X' if enterprise_count == 0 else None
        }
    
    def _check_compliance(self, networks: List[Dict]) -> Dict:
        """检查PCI-DSS合规性"""
        compliance_checks = {}
        
        # 检查项目2.1.1: 默认配置
        default_ssids = self._check_default_ssids(networks)
        compliance_checks['2.1.1'] = {
            'requirement': self.PCI_REQUIREMENTS['2.1.1'],
            'status': 'PASS' if not default_ssids else 'FAIL',
            'details': f'发现 {len(default_ssids)} 个默认SSID' if default_ssids else '未发现默认SSID',
            'findings': default_ssids
        }
        
        # 检查项目4.1: 加密要求
        weak_encryption = [
            net for net in networks
            if not self.ENCRYPTION_RATINGS.get(
                self._normalize_encryption_type(net.get('encryption', '')),
                {}
            ).get('compliant', False)
        ]
        compliance_checks['4.1'] = {
            'requirement': self.PCI_REQUIREMENTS['4.1'],
            'status': 'PASS' if not weak_encryption else 'FAIL',
            'details': f'发现 {len(weak_encryption)} 个使用弱加密的网络' if weak_encryption else '所有网络使用强加密',
            'findings': [net['ssid'] for net in weak_encryption]
        }
        
        # 检查项目12.3: 使用策略
        open_networks = [
            net for net in networks
            if 'Open' in self._normalize_encryption_type(net.get('encryption', ''))
        ]
        compliance_checks['12.3'] = {
            'requirement': self.PCI_REQUIREMENTS['12.3'],
            'status': 'PASS' if not open_networks else 'FAIL',
            'details': f'发现 {len(open_networks)} 个开放网络' if open_networks else '未发现开放网络',
            'findings': [net['ssid'] for net in open_networks]
        }
        
        # 计算合规性百分比
        passed = sum(1 for check in compliance_checks.values() if check['status'] == 'PASS')
        total = len(compliance_checks)
        
        return {
            'checks': compliance_checks,
            'passed_count': passed,
            'failed_count': total - passed,
            'total_checks': total,
            'compliance_percentage': round(passed / total * 100, 1) if total > 0 else 0,
            'overall_status': 'COMPLIANT' if passed == total else 'NON-COMPLIANT'
        }
    
    def _check_default_ssids(self, networks: List[Dict]) -> List[str]:
        """检查默认SSID"""
        default_patterns = [
            r'linksys', r'netgear', r'dlink', r'd-link', r'tp-link', 
            r'asus', r'belkin', r'cisco', r'default', r'wireless'
        ]
        
        default_ssids = []
        for network in networks:
            ssid = network.get('ssid', '').lower()
            for pattern in default_patterns:
                if re.search(pattern, ssid):
                    default_ssids.append(network['ssid'])
                    break
        
        return default_ssids
    
    def _assess_risks(self, networks: List[Dict]) -> Dict:
        """评估安全风险（增强版 - CVSS v3.1模型）
        
        采用多维度安全风险评估模型:
        1. 加密强度风险（基于PCI-DSS 4.0标准）
        2. 认证机制风险
        3. 信号暴露风险（过高信号强度）
        4. SSID配置风险（默认配置/信息泄露）
        5. 潜在攻击向量分析
        """
        risks = {
            'critical': [],  # 严重风险 (CVSS 9.0-10.0)
            'high': [],      # 高风险 (CVSS 7.0-8.9)
            'medium': [],    # 中等风险 (CVSS 4.0-6.9)
            'low': [],       # 低风险 (CVSS 0.1-3.9)
            'info': []       # 信息类
        }
        
        # 统计各类风险的暴露指数
        exposure_metrics = {
            'open_networks': 0,
            'weak_encryption': 0,
            'default_configs': 0,
            'high_signal_exposure': 0,
            'total_aps_at_risk': 0
        }
        
        for network in networks:
            ssid = network.get('ssid', '未知')
            encryption = self._normalize_encryption_type(network.get('encryption', ''))
            ap_count = network.get('ap_count', len(network.get('bssids', [])))
            
            # 关键风险: 开放网络 (CVSS 9.8 - Critical)
            if encryption == 'Open':
                exposure_metrics['open_networks'] += ap_count
                exposure_metrics['total_aps_at_risk'] += ap_count
                risks['critical'].append({
                    'ssid': ssid,
                    'issue': f'使用开放网络，无任何加密保护',
                    'impact': '所有数据明文传输，可被轻易截获和篡改，严重违反PCI-DSS 4.1',
                    'remediation': '立即启用WPA3-Enterprise或最低WPA2-Enterprise加密',
                    'cvss_score': 9.8,
                    'pci_dss_ref': 'Req 4.1.1',
                    'affected_aps': ap_count
                })
            
            # 关键风险: WEP加密 (CVSS 9.1 - Critical)
            elif encryption == 'WEP':
                exposure_metrics['weak_encryption'] += ap_count
                exposure_metrics['total_aps_at_risk'] += ap_count
                risks['critical'].append({
                    'ssid': ssid,
                    'issue': f'使用已被破解的WEP加密',
                    'impact': '可在60秒内被破解，提供虚假安全保护，严重违反PCI-DSS',
                    'remediation': '立即替换为WPA2或WPA3加密',
                    'cvss_score': 9.1,
                    'pci_dss_ref': 'Req 4.1.1',
                    'affected_aps': ap_count,
                    'exploit_time': '< 60秒'
                })
            
            # 高风险: WPA (CVSS 7.5 - High)
            elif encryption == 'WPA':
                exposure_metrics['weak_encryption'] += ap_count
                risks['high'].append({
                    'ssid': ssid,
                    'issue': '使用已过时的WPA加密',
                    'impact': '存在KRACK攻击等已知漏洞，TKIP加密不符合当前安全标准',
                    'remediation': '升级到WPA2-AES或WPA3',
                    'cvss_score': 7.5,
                    'pci_dss_ref': 'Req 4.1',
                    'affected_aps': ap_count,
                    'vulnerabilities': ['KRACK', 'TKIP弱加密']
                })
            
            # 中等风险: WPA2个人版而非企业版 (CVSS 5.3 - Medium)
            # 支持中英文企业认证识别
            auth = network.get('authentication', '')
            is_enterprise = 'Enterprise' in auth or '802.1X' in auth or '企业' in auth
            
            if encryption == 'WPA2' and not is_enterprise:
                risks['medium'].append({
                    'ssid': ssid,
                    'issue': '使用WPA2个人版而非企业版',
                    'impact': '缺少集中式身份验证，无法实现用户级访问控制和审计',
                    'remediation': '对于企业环境，建议升级到WPA2-Enterprise (802.1X) 或WPA3-Enterprise',
                    'cvss_score': 5.3,
                    'pci_dss_ref': 'Req 8.2, 8.3',
                    'affected_aps': ap_count,
                    'enterprise_recommendation': '启用RADIUS服务器进行802.1X认证'
                })
            
            # 低风险: 默认SSID (CVSS 3.1 - Low)
            if self._check_default_ssids([network]):
                exposure_metrics['default_configs'] += 1
                risks['low'].append({
                    'ssid': ssid,
                    'issue': '使用默认或通用SSID',
                    'impact': '暴露设备类型和厂商信息，更容易成为攻击目标',
                    'remediation': '更改为自定义SSID，避免使用公司名称或敏感信息',
                    'cvss_score': 3.1,
                    'pci_dss_ref': 'Req 2.1',
                    'affected_aps': ap_count
                })
            
            # 信息类: 信号强度过高风险（暴露面过大）
            # 兼容三种数据格式：signal_avg、signal、signal_percent
            signal_strength = network.get('signal_avg') or network.get('signal') or network.get('signal_percent', 0)
            
            # 确保signal_strength是有效数字
            if signal_strength is None or signal_strength == 'N/A':
                signal_strength = 0
            
            if signal_strength > 90 or (signal_strength < 0 and signal_strength > -40):  # > -40 dBm
                exposure_metrics['high_signal_exposure'] += ap_count
                risks['info'].append({
                    'ssid': ssid,
                    'issue': f'信号强度过高 ({signal_strength})',
                    'impact': '可能扩大物理政击面，增加未授权访问风险',
                    'remediation': '调整AP功率以限制覆盖范围在必要区域内',
                    'affected_aps': ap_count,
                    'recommended_action': '减少发射功率到20-30%'
                })
        
        # 计算综合风险评分（采用CVSS加权模型）
        risk_score = self._calculate_risk_score_cvss(risks, exposure_metrics)
        
        # 生成威胁情报报告
        threat_intelligence = self._generate_threat_intelligence(exposure_metrics, len(networks))
        
        return {
            'summary': {
                'critical': len(risks['critical']),
                'high': len(risks['high']),
                'medium': len(risks['medium']),
                'low': len(risks['low']),
                'info': len(risks['info'])
            },
            'details': risks,
            'risk_score': risk_score,
            'exposure_metrics': exposure_metrics,
            'threat_intelligence': threat_intelligence,
            'remediation_priority': self._generate_remediation_priority(risks)
        }
    
    def _calculate_risk_score(self, risks: Dict) -> int:
        """计算风险得分（0-100，越低越好） - 简单加权模型"""
        weights = {
            'critical': 40,
            'high': 25,
            'medium': 15,
            'low': 10,
            'info': 5
        }
        
        total_score = 0
        for level, weight in weights.items():
            count = len(risks.get(level, []))
            total_score += count * weight
        
        # 限制在0-100范围内
        return min(100, total_score)
    
    def _calculate_risk_score_cvss(self, risks: Dict, exposure_metrics: Dict) -> int:
        """计算综合风险评分（基于CVSS v3.1模型）
        
        评分模型:
        1. 基础分: 根据漏洞数量和CVSS评分计算
        2. 暴露分: 根据受影响AP数量计算
        3. 最终得分 = 基础分 * 0.7 + 暴露分 * 0.3
        
        Returns:
            0-100的风险评分，值越高风险越大
        """
        # 1. 计算基础分（基于CVSS加权）
        base_score = 0
        for risk_level, risk_list in risks.items():
            for risk in risk_list:
                cvss = risk.get('cvss_score', 0)
                # CVSS转换为0-100的分数
                base_score += (cvss / 10.0) * 10
        
        # 2. 计算暴露分（受影响AP比例）
        total_aps_at_risk = exposure_metrics.get('total_aps_at_risk', 0)
        open_networks = exposure_metrics.get('open_networks', 0)
        weak_encryption = exposure_metrics.get('weak_encryption', 0)
        
        # 开放网络和弱加密的严重性最高
        exposure_score = 0
        if open_networks > 0:
            exposure_score += open_networks * 15  # 每个开放网络15分
        if weak_encryption > 0:
            exposure_score += weak_encryption * 10  # 每个弱加密网络10分
        
        # 3. 加权计算最终得分
        final_score = base_score * 0.7 + exposure_score * 0.3
        
        # 限制在0-100范围
        return min(100, int(final_score))
    
    def _generate_threat_intelligence(self, exposure_metrics: Dict, total_networks: int) -> Dict:
        """生成威胁情报分析
        
        提供安全威胁的全局视角
        """
        open_networks = exposure_metrics.get('open_networks', 0)
        weak_encryption = exposure_metrics.get('weak_encryption', 0)
        total_at_risk = exposure_metrics.get('total_aps_at_risk', 0)
        
        # 计算风险暴露率
        risk_exposure_rate = (total_at_risk / max(total_networks, 1)) * 100
        
        # 威胁等级
        if risk_exposure_rate >= 50:
            threat_level = '严重'
            threat_color = 'critical'
        elif risk_exposure_rate >= 30:
            threat_level = '高'
            threat_color = 'high'
        elif risk_exposure_rate >= 10:
            threat_level = '中等'
            threat_color = 'medium'
        else:
            threat_level = '低'
            threat_color = 'low'
        
        return {
            'threat_level': threat_level,
            'threat_color': threat_color,
            'risk_exposure_rate': round(risk_exposure_rate, 1),
            'open_network_count': open_networks,
            'weak_encryption_count': weak_encryption,
            'total_at_risk_aps': total_at_risk,
            'attack_surface_analysis': {
                '明文数据传输风险': open_networks > 0,
                '弱加密破解风险': weak_encryption > 0,
                '需立即处理': risk_exposure_rate >= 30
            },
            'compliance_impact': {
                'pci_dss_violation': open_networks > 0 or weak_encryption > 0,
                'requires_immediate_action': risk_exposure_rate >= 50,
                'remediation_urgency': '紧急' if risk_exposure_rate >= 50 else '高' if risk_exposure_rate >= 30 else '中等'
            }
        }
    
    def _generate_remediation_priority(self, risks: Dict) -> List[Dict]:
        """生成修复优先级列表
        
        按照CVSS评分和影响AP数量排序
        """
        all_risks = []
        
        for level in ['critical', 'high', 'medium', 'low']:
            for risk in risks.get(level, []):
                all_risks.append({
                    'level': level,
                    'ssid': risk['ssid'],
                    'issue': risk['issue'],
                    'cvss_score': risk.get('cvss_score', 0),
                    'affected_aps': risk.get('affected_aps', 1),
                    'remediation': risk['remediation'],
                    'pci_dss_ref': risk.get('pci_dss_ref', '')
                })
        
        # 按CVSS分数和影响AP数量排序
        all_risks.sort(key=lambda x: (x['cvss_score'], x['affected_aps']), reverse=True)
        
        return all_risks[:10]  # 返回前10个最高优先级
    
    def _scan_vulnerabilities(self, networks: List[Dict]) -> Dict:
        """扫描已知漏洞"""
        vulnerabilities = []
        
        for network in networks:
            ssid = network.get('ssid', '未知')
            encryption = self._normalize_encryption_type(network.get('encryption', ''))
            
            # WPS漏洞检测
            vulnerabilities.append({
                'ssid': ssid,
                'vulnerability': 'WPS PIN暴力破解',
                'severity': 'HIGH',
                'description': 'WPS功能可能存在PIN暴力破解漏洞',
                'cve': 'CVE-2011-5053',
                'recommendation': '禁用WPS功能'
            })
            
            # KRACK攻击检测（WPA2）
            if encryption == 'WPA2':
                vulnerabilities.append({
                    'ssid': ssid,
                    'vulnerability': 'KRACK攻击',
                    'severity': 'MEDIUM',
                    'description': 'WPA2可能受到密钥重装攻击',
                    'cve': 'CVE-2017-13077',
                    'recommendation': '确保所有设备已安装安全补丁或升级到WPA3'
                })
            
            # 弱加密漏洞
            if encryption in ['WEP', 'WPA']:
                vulnerabilities.append({
                    'ssid': ssid,
                    'vulnerability': '弱加密算法',
                    'severity': 'CRITICAL',
                    'description': f'{encryption}存在已知的严重安全漏洞',
                    'cve': 'Multiple',
                    'recommendation': f'立即停用{encryption}，启用WPA2或WPA3'
                })
        
        # 统计漏洞类型分布
        vuln_by_type = {}
        for vuln in vulnerabilities:
            v_type = vuln.get('vulnerability', '未知')
            vuln_by_type[v_type] = vuln_by_type.get(v_type, 0) + 1
        
        return {
            'total_vulnerabilities': len(vulnerabilities),
            'by_severity': {
                'critical': sum(1 for v in vulnerabilities if v['severity'] == 'CRITICAL'),
                'high': sum(1 for v in vulnerabilities if v['severity'] == 'HIGH'),
                'medium': sum(1 for v in vulnerabilities if v['severity'] == 'MEDIUM'),
                'low': sum(1 for v in vulnerabilities if v['severity'] == 'LOW')
            },
            'by_type': vuln_by_type,
            'details': vulnerabilities
        }
    
    def _generate_security_recommendations(self, networks: List[Dict]) -> List[Dict]:
        """生成安全建议"""
        recommendations = []
        
        # 优先级1: 关键安全问题
        weak_networks = [
            net for net in networks
            if self._normalize_encryption_type(net.get('encryption', '')) in ['Open', 'WEP', 'WPA']
        ]
        if weak_networks:
            recommendations.append({
                'priority': 'CRITICAL',
                'category': '加密安全',
                'title': '立即修复弱加密网络',
                'description': f'发现 {len(weak_networks)} 个使用不安全加密的网络',
                'action': '将所有网络升级到WPA2-Enterprise或WPA3',
                'pci_requirement': '4.1',
                'networks': [net['ssid'] for net in weak_networks]
            })
        
        # 优先级2: 企业级认证
        # 支持中英文企业认证识别
        non_enterprise = sum(
            1 for net in networks
            if not ('Enterprise' in net.get('authentication', '') or 
                    '802.1X' in net.get('authentication', '') or 
                    '企业' in net.get('authentication', ''))
        )
        if non_enterprise > 0:
            recommendations.append({
                'priority': 'HIGH',
                'category': '身份验证',
                'title': '部署企业级身份验证',
                'description': f'{non_enterprise} 个网络未使用企业级认证',
                'action': '实施802.1X/RADIUS认证系统',
                'pci_requirement': '8.2',
                'networks': [
                    net['ssid'] for net in networks
                    if not ('Enterprise' in net.get('authentication', '') or 
                            '802.1X' in net.get('authentication', '') or 
                            '企业' in net.get('authentication', ''))
                ]
            })
        
        # 优先级3: 网络隔离
        if len(networks) > 1:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': '网络分段',
                'title': '实施网络隔离',
                'description': '建议将持卡人数据环境与其他网络隔离',
                'action': '配置独立的VLAN和防火墙规则',
                'pci_requirement': '1.2.3',
                'networks': None
            })
        
        # 优先级4: 监控和审计
        recommendations.append({
            'priority': 'MEDIUM',
            'category': '安全监控',
            'title': '建立无线网络监控',
            'description': '定期监控无线网络活动和异常',
            'action': '部署WIDS/WIPS系统，启用日志记录',
            'pci_requirement': '10.1, 11.2',
            'networks': None
        })
        
        # 优先级5: 定期评估
        recommendations.append({
            'priority': 'LOW',
            'category': '合规维护',
            'title': '定期安全评估',
            'description': '按照PCI-DSS要求定期进行安全扫描',
            'action': '每季度执行漏洞扫描，每年进行渗透测试',
            'pci_requirement': '11.2, 11.3',
            'networks': None
        })
        
        return recommendations
    
    def _calculate_overall_score(self, results: Dict) -> int:
        """计算总体安全得分（0-100）"""
        # 基础分数
        base_score = 100
        
        # 加密安全 (40%)
        secure_percentage = results['encryption_analysis'].get('secure_percentage', 0)
        encryption_score = secure_percentage * 0.4
        
        # 合规性 (30%)
        compliance_percentage = results['compliance_status'].get('compliance_percentage', 0)
        compliance_score = compliance_percentage * 0.3
        
        # 风险评估 (30%)
        risk_score = results['risk_assessment'].get('risk_score', 100)
        # 风险分数越低越好，需要反转
        risk_component = (100 - risk_score) * 0.3
        
        overall_score = encryption_score + compliance_score + risk_component
        
        return round(overall_score)
    
    def _determine_compliance_level(self, results: Dict) -> str:
        """确定合规等级（使用配置文件阈值）"""
        score = results.get('overall_score', 0)
        
        # 使用配置文件中的阈值
        if score >= self.full_compliance_threshold:
            self.logger.debug(f"评分{score}达到完全合规阈值{self.full_compliance_threshold}")
            return '完全合规'
        elif score >= self.partial_compliance_threshold:
            self.logger.debug(f"评分{score}达到基本合规阈值{self.partial_compliance_threshold}")
            return '基本合规'
        elif score >= 60:
            self.logger.debug(f"评分{score}为部分合规")
            return '部分合规'
        else:
            self.logger.warning(f"评分{score}不合规")
            return '不合规'
    
    # 兼容方法：与GUI界面调用匹配
    def assess_network(self, wifi_data: List[Dict], config: Dict = None) -> Dict:
        """
        评估网络安全（兼容方法）
        
        Args:
            wifi_data: WiFi数据列表
            config: 配置参数（可选）
            
        Returns:
            评估结果，包含overall_risk_score和risk_level
        """
        self.logger.info(f"开始评估{len(wifi_data)}个网络的安全性")
        results = self.perform_security_assessment(wifi_data)
        
        # 转换为GUI期望的格式
        score = results.get('overall_score', 0)
        self.logger.info(f"安全评分: {score}/100")
        
        # 使用配置文件阈值进行风险等级判定
        full_threshold = self.full_compliance_threshold
        partial_threshold = self.partial_compliance_threshold
        
        # 风险等级反向映射（分数越高安全性越高，风险越低）
        if score >= full_threshold:
            risk_level = "低风险"
            risk_score = 10
            self.logger.info(f"风险等级: {risk_level}（达到完全合规标准）")
        elif score >= partial_threshold:
            risk_level = "中低风险"
            risk_score = 30
            self.logger.info(f"风险等级: {risk_level}（达到基本合规标准）")
        elif score >= 60:
            risk_level = "中等风险"
            risk_score = 50
            self.logger.warning(f"风险等级: {risk_level}")
        elif score >= 40:
            risk_level = "中高风险"
            risk_score = 70
            self.logger.warning(f"风险等级: {risk_level}")
        else:
            risk_level = "高风险"
            risk_score = 90
            self.logger.error(f"风险等级: {risk_level}（严重不合规）")
        
        results['overall_risk_score'] = risk_score
        results['risk_level'] = risk_level
        
        return results
    
    def generate_executive_summary(self) -> str:
        """
        生成执行摘要报告
        
        Returns:
            格式化的文本报告
        """
        if not hasattr(self, 'networks_assessed') or not self.networks_assessed:
            return "尚未执行安全评估"
        
        results = self.perform_security_assessment(self.networks_assessed)
        
        summary = f"""
========================================
       PCI-DSS 无线网络安全评估报告
========================================

评估时间: {results['assessment_time']}
评估网络数量: {results['total_networks']}
总体安全评分: {results['overall_score']}/100
合规等级: {results['compliance_level']}

----------------------------------------
1. 加密方式分析
----------------------------------------
{self._format_encryption_analysis(results['encryption_analysis'])}

----------------------------------------
2. 认证方式分析
----------------------------------------
{self._format_authentication_analysis(results['authentication_analysis'])}

----------------------------------------
3. PCI-DSS合规性检查
----------------------------------------
{self._format_compliance_status(results['compliance_status'])}

----------------------------------------
4. 风险评估
----------------------------------------
{self._format_risk_assessment(results['risk_assessment'])}

----------------------------------------
5. 漏洞扫描
----------------------------------------
{self._format_vulnerability_scan(results['vulnerability_scan'])}

----------------------------------------
6. 安全建议
----------------------------------------
{self._format_recommendations(results['recommendations'])}

========================================
"""
        return summary
    
    def _format_encryption_analysis(self, data: Dict) -> str:
        """格式化加密分析"""
        lines = []
        for enc_type, count in data.get('encryption_distribution', {}).items():
            rating = self.encryption_ratings.get(enc_type, {'score': 0, 'level': '未知'})
            lines.append(f"  - {enc_type}: {count}个 (安全等级: {rating['level']}, 得分: {rating['score']})")
        
        lines.append(f"\n安全AP比例: {data.get('secure_percentage', 0):.1f}%")
        
        weakest = data.get('weakest_encryption', {})
        if weakest:
            lines.append(f"最弱加密: {weakest.get('type', '未知')} ({weakest.get('count', 0)}个)")
        
        return "\n".join(lines)
    
    def _format_authentication_analysis(self, data: Dict) -> str:
        """格式化认证分析"""
        lines = []
        for auth_type, count in data.get('auth_distribution', {}).items():
            lines.append(f"  - {auth_type}: {count}个")
        
        lines.append(f"\n企业级认证比例: {data.get('enterprise_percentage', 0):.1f}%")
        
        if data.get('open_networks'):
            lines.append(f"⚠️ 发现 {len(data['open_networks'])} 个开放网络")
        
        return "\n".join(lines)
    
    def _format_compliance_status(self, data: Dict) -> str:
        """格式化合规状态"""
        lines = []
        
        # 如果data包含checks字段，使用它；否则假设data本身就是checks
        checks = data.get('checks', data)
        
        for req_id, check in checks.items():
            status_icon = "✓" if check.get('status') == 'PASS' else "✗"
            lines.append(f"{status_icon} {check.get('requirement', 'N/A')}")
            lines.append(f"   状态: {check.get('status', 'UNKNOWN')}")
            lines.append(f"   详情: {check.get('details', 'N/A')}\n")
        
        # 如果有总体统计信息，也显示
        if 'compliance_percentage' in data:
            lines.append(f"\n合规性: {data.get('compliance_percentage', 0):.1f}%")
            lines.append(f"通过: {data.get('passed_count', 0)}/{data.get('total_checks', 0)}")
        
        return "\n".join(lines)
    
    def _format_risk_assessment(self, data: Dict) -> str:
        """格式化风险评估"""
        lines = []
        for level in ['critical', 'high', 'medium', 'low']:
            risks = data.get(level, [])
            if risks:
                lines.append(f"\n{level.upper()}级风险 ({len(risks)}个):")
                for risk in risks[:3]:  # 只显示前3个
                    lines.append(f"  - {risk}")
        
        return "\n".join(lines)
    
    def _format_vulnerability_scan(self, data: Dict) -> str:
        """格式化漏洞扫描"""
        lines = []
        lines.append(f"发现漏洞总数: {data.get('total_vulnerabilities', 0)}")
        lines.append(f"高危漏洞: {data.get('high_severity', 0)}")
        lines.append(f"中危漏洞: {data.get('medium_severity', 0)}")
        lines.append(f"低危漏洞: {data.get('low_severity', 0)}")
        
        return "\n".join(lines)
    
    def _format_recommendations(self, recommendations: List[Dict]) -> str:
        """格式化建议"""
        lines = []
        for i, rec in enumerate(recommendations, 1):
            lines.append(f"{i}. {rec['title']}")
            lines.append(f"   优先级: {rec['priority']}")
            lines.append(f"   说明: {rec['description']}\n")
        
        return "\n".join(lines)
    
    def export_to_json(self, filepath: str) -> bool:
        """
        导出评估结果为JSON
        
        Args:
            filepath: 文件路径
            
        Returns:
            是否成功
        """
        try:
            import json
            
            if not hasattr(self, 'networks_assessed') or not self.networks_assessed:
                return False
            
            results = self.perform_security_assessment(self.networks_assessed)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"JSON报告导出成功: {filepath}")
            return True
        except IOError as e:
            self.logger.error(f"JSON文件写入失败: {e}")
            return False
        except Exception as e:
            self.logger.exception(f"导出JSON失败: {e}")
            return False
