"""
WiFi安全评分系统
功能：多维度风险评分、优先级排序、安全等级评定
版本：V2.0 Enhanced (集成动态权重评分)
"""

from typing import Dict, List, Any, Optional

# 导入动态权重评分系统
try:
    from .dynamic_scoring import DynamicScoring, NetworkType, ThreatLevel
    HAS_DYNAMIC_SCORING = True
except ImportError:
    HAS_DYNAMIC_SCORING = False


class SecurityScoreCalculator:
    """安全评分计算器"""
    
    # 评分权重（总和=100%）
    WEIGHTS = {
        'encryption': 0.30,      # 加密方式（30%）
        'wps': 0.25,             # WPS漏洞（25%）
        'password': 0.20,        # 密码强度（20%）
        'management': 0.15,      # 管理配置（15%）
        'exposure': 0.10         # 暴露程度（10%）
    }
    
    def __init__(self):
        # 初始化动态权重评分系统
        if HAS_DYNAMIC_SCORING:
            self.dynamic_scorer = DynamicScoring()
        else:
            self.dynamic_scorer = None
    
    def calculate_network_score(self, network: Dict[str, Any],
                                encryption_analysis: Dict[str, Any],
                                wps_result: Dict[str, Any],
                                password_result: Optional[Dict[str, Any]] = None,
                                environment: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        计算网络综合安全评分
        
        Args:
            network: 网络基本信息
            encryption_analysis: 加密详细分析
            wps_result: WPS漏洞检测结果
            password_result: 密码强度评估（如果已连接）
            environment: 环境信息（周边网络数量等）
            
        Returns:
            评分结果字典
        """
        scores = {}
        
        # 1. 加密评分（30%）
        scores['encryption'] = encryption_analysis.get('security_level', 0)
        
        # 2. WPS评分（25%）
        scores['wps'] = self._score_wps(wps_result)
        
        # 3. 密码评分（20%）
        if password_result:
            # 已连接，有实际密码评估
            scores['password'] = (password_result.get('score', 0) / 5) * 100
        else:
            # 未连接，基于加密类型推测
            scores['password'] = self._estimate_password_score(network, encryption_analysis)
        
        # 4. 管理配置评分（15%）
        scores['management'] = self._score_management(network)
        
        # 5. 暴露程度评分（10%）
        scores['exposure'] = self._score_exposure(network, environment)
        
        # 加权求和
        total_score = sum(
            score * self.WEIGHTS[category]
            for category, score in scores.items()
        )
        
        # 识别风险
        risks = self._identify_risks(scores, encryption_analysis, wps_result)
        
        # 生成优先行动
        priority_actions = self._generate_priority_actions(risks)
        
        return {
            'total_score': round(total_score, 1),
            'rating': self._get_rating(total_score),
            'rating_emoji': self._get_rating_emoji(total_score),
            'category_scores': {
                '加密安全': round(scores['encryption'], 1),
                'WPS安全': round(scores['wps'], 1),
                '密码强度': round(scores['password'], 1),
                '管理配置': round(scores['management'], 1),
                '暴露程度': round(scores['exposure'], 1)
            },
            'risks': risks,
            'priority_actions': priority_actions,
            'security_level': self._get_security_level(total_score)
        }
    
    def calculate_environment_score(self, networks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        计算环境整体安全评分
        
        Args:
            networks: 所有扫描到的网络列表
            
        Returns:
            环境评分
        """
        if not networks:
            return {
                'score': 100,
                'rating': '安全',
                'issues': ['未检测到WiFi网络']
            }
        
        total = len(networks)
        open_count = 0
        weak_encryption_count = 0
        wps_vulnerable_count = 0
        suspicious_count = 0
        
        for net in networks:
            auth = net.get('authentication', '').upper()
            
            # 开放网络
            if 'OPEN' in auth or auth == '开放':
                open_count += 1
            
            # 弱加密
            elif 'WEP' in auth or ('WPA' in auth and 'WPA2' not in auth and 'WPA3' not in auth):
                weak_encryption_count += 1
            
            # 默认SSID（可疑）
            ssid = net.get('ssid', '').lower()
            if ssid in ['tp-link', 'netgear', 'linksys', 'default']:
                suspicious_count += 1
        
        # 环境评分
        deduction = 0
        deduction += open_count * 10
        deduction += weak_encryption_count * 5
        deduction += suspicious_count * 3
        
        score = max(0, 100 - deduction)
        
        issues = []
        if open_count > 0:
            issues.append(f'{open_count}个开放网络（高风险）')
        if weak_encryption_count > 0:
            issues.append(f'{weak_encryption_count}个弱加密网络')
        if suspicious_count > 0:
            issues.append(f'{suspicious_count}个可疑AP')
        
        return {
            'score': round(score, 1),
            'rating': self._get_rating(score),
            'rating_emoji': self._get_rating_emoji(score),
            'total_networks': total,
            'open_networks': open_count,
            'weak_encryption': weak_encryption_count,
            'suspicious_aps': suspicious_count,
            'issues': issues
        }
    
    # ===== 各维度评分方法 =====
    
    def _score_wps(self, wps_result: Dict[str, Any]) -> float:
        """WPS漏洞评分（0-100）"""
        if not wps_result.get('wps_enabled'):
            return 100  # WPS未启用，满分
        
        severity = wps_result.get('severity', 'LOW')
        
        if severity == 'CRITICAL':
            return 10  # PixieDust漏洞
        elif severity == 'HIGH':
            return 30  # PIN暴力破解
        elif severity == 'MEDIUM':
            return 60  # WPS启用但无已知漏洞
        else:
            return 80  # WPS启用但风险低
    
    def _estimate_password_score(self, network: Dict[str, Any],
                                 encryption_analysis: Dict[str, Any]) -> float:
        """估算密码评分（未连接时）"""
        auth = network.get('authentication', '').upper()
        
        # 开放网络：0分
        if 'OPEN' in auth or auth == '开放':
            return 0
        
        # WEP：10分（密码形同虚设）
        if 'WEP' in auth:
            return 10
        
        # WPA：30分（协议弱）
        if 'WPA' in auth and 'WPA2' not in auth and 'WPA3' not in auth:
            return 30
        
        # WPA2-PSK：估算60分（假设用户使用中等密码）
        if 'WPA2' in auth and 'ENTERPRISE' not in auth:
            return 60
        
        # WPA2-Enterprise：90分（企业级，密码通常较强）
        if 'ENTERPRISE' in auth:
            return 90
        
        # WPA3：95分（最新协议）
        if 'WPA3' in auth:
            return 95
        
        return 50  # 默认
    
    def _score_management(self, network: Dict[str, Any]) -> float:
        """管理配置评分（0-100）"""
        score = 100
        
        ssid = network.get('ssid', '').lower()
        
        # 使用默认SSID（-30分）
        default_ssids = ['tp-link', 'netgear', 'linksys', 'dlink', 
                        'd-link', 'asus', 'default', 'wireless']
        if ssid in default_ssids:
            score -= 30
        
        # 隐藏SSID（-10分，伪装安全）
        if not ssid or ssid == '':
            score -= 10
        
        # SSID过短（-10分）
        if len(ssid) < 4:
            score -= 10
        
        # SSID包含MAC地址后缀（常见默认配置，-15分）
        if any(ssid.endswith(suffix) for suffix in ['_2.4g', '_5g', '-2g', '-5g']):
            score -= 15
        
        return max(0, score)
    
    def _score_exposure(self, network: Dict[str, Any], 
                       environment: Optional[Dict[str, Any]]) -> float:
        """暴露程度评分（0-100）"""
        score = 100
        
        # 修复：确保signal是整数类型
        signal = network.get('signal', -100)
        if isinstance(signal, str):
            # 移除"dBm"等后缀
            import re
            match = re.search(r'-?\d+', signal)
            signal = int(match.group()) if match else -100
        
        signal_percent = network.get('signal_percent', 0)
        # 修复：确保signal_percent是数字类型
        if isinstance(signal_percent, str):
            signal_percent = int(signal_percent.rstrip('%')) if signal_percent != '未知' else 0
        elif not isinstance(signal_percent, (int, float)):
            signal_percent = 0
        
        # 信号过强（可能在公共场所，-20分）
        if signal > -40 or signal_percent > 80:
            score -= 20
        
        # 信号适中（家用范围，-10分）
        elif signal > -60 or signal_percent > 50:
            score -= 10
        
        # 环境因素
        if environment:
            # 周边网络过多（拥挤环境，-15分）
            nearby_count = environment.get('nearby_networks', 0)
            if nearby_count > 20:
                score -= 15
            elif nearby_count > 10:
                score -= 10
        
        return max(0, score)
    
    # ===== 风险识别 =====
    
    def _identify_risks(self, scores: Dict[str, float],
                       encryption_analysis: Dict[str, Any],
                       wps_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """识别具体风险"""
        risks = []
        
        # 加密风险
        if scores['encryption'] < 50:
            risks.append({
                'category': '加密安全',
                'type': '加密不足',
                'severity': 'CRITICAL' if scores['encryption'] < 20 else 'HIGH',
                'score': scores['encryption'],
                'description': '加密方式过时或不安全',
                'impact': '数据传输可被窃听和破解',
                'vulnerabilities': encryption_analysis.get('vulnerabilities', [])
            })
        
        # WPS风险
        if scores['wps'] < 50:
            vulnerability_type = wps_result.get('vulnerability_type', '')
            exploit_time = wps_result.get('exploit_time', '未知')
            
            risks.append({
                'category': 'WPS安全',
                'type': 'WPS漏洞',
                'severity': wps_result.get('severity', 'HIGH'),
                'score': scores['wps'],
                'description': f'{vulnerability_type}',
                'impact': f'密码可在{exploit_time}内被破解',
                'vulnerabilities': [vulnerability_type] if vulnerability_type else []
            })
        
        # 密码风险
        if scores['password'] < 60:
            risks.append({
                'category': '密码强度',
                'type': '密码弱',
                'severity': 'HIGH' if scores['password'] < 30 else 'MEDIUM',
                'score': scores['password'],
                'description': '密码强度不足',
                'impact': '易被暴力破解或字典攻击',
                'vulnerabilities': ['弱密码']
            })
        
        # 管理配置风险
        if scores['management'] < 70:
            risks.append({
                'category': '管理配置',
                'type': '配置不当',
                'severity': 'MEDIUM',
                'score': scores['management'],
                'description': '使用默认配置或不安全设置',
                'impact': '易被识别和攻击',
                'vulnerabilities': ['默认配置']
            })
        
        # 暴露风险
        if scores['exposure'] < 80:
            risks.append({
                'category': '暴露程度',
                'type': '暴露过度',
                'severity': 'LOW',
                'score': scores['exposure'],
                'description': '信号覆盖范围过大',
                'impact': '增加被攻击的可能性',
                'vulnerabilities': ['信号过强']
            })
        
        # 按严重程度排序
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        risks.sort(key=lambda r: (severity_order.get(r['severity'], 4), r['score']))
        
        return risks
    
    def _generate_priority_actions(self, risks: List[Dict[str, Any]]) -> List[str]:
        """生成优先行动清单"""
        actions = []
        
        for risk in risks:
            severity = risk['severity']
            category = risk['category']
            
            if category == '加密安全' and severity in ['CRITICAL', 'HIGH']:
                actions.append('🔴 立即升级到WPA2-AES或WPA3加密')
            
            elif category == 'WPS安全' and severity == 'CRITICAL':
                actions.append('🔴 立即禁用WPS功能或更新路由器固件')
            
            elif category == 'WPS安全' and severity == 'HIGH':
                actions.append('🟠 禁用WPS或启用WPS锁定功能')
            
            elif category == '密码强度' and severity == 'HIGH':
                actions.append('🟠 更换为12位以上强密码（大小写+数字+符号）')
            
            elif category == '管理配置':
                actions.append('🟡 修改默认SSID并更新管理员密码')
        
        # 通用建议
        if not actions:
            actions.append('✅ 安全配置良好，保持定期检查和更新')
        else:
            actions.append('💡 定期更新路由器固件以修复安全漏洞')
        
        return actions[:5]  # 最多5条
    
    # ===== 评级方法 =====
    
    def _get_rating(self, score: float) -> str:
        """获取评级文字"""
        if score >= 90:
            return '优秀'
        elif score >= 75:
            return '良好'
        elif score >= 60:
            return '一般'
        elif score >= 40:
            return '较差'
        else:
            return '危险'
    
    def _get_rating_emoji(self, score: float) -> str:
        """获取评级表情"""
        if score >= 90:
            return '🟢'
        elif score >= 75:
            return '🟡'
        elif score >= 60:
            return '🟠'
        else:
            return '🔴'
    
    def _get_security_level(self, score: float) -> str:
        """获取安全等级"""
        if score >= 90:
            return 'A'
        elif score >= 75:
            return 'B'
        elif score >= 60:
            return 'C'
        elif score >= 40:
            return 'D'
        else:
            return 'F'
