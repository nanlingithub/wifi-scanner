"""
WiFi安全检测核心模块
提供漏洞检测、密码分析、风险评分等功能
"""

import re
from datetime import datetime
from typing import List, Dict


class VulnerabilityDetector:
    """漏洞检测器"""
    
    def analyze_encryption_detail(self, network: Dict) -> Dict:
        """分析加密详情（增强WiFi 6E/7协议支持）"""
        auth = network.get('authentication', 'N/A').lower()
        wifi_standard = network.get('wifi_standard', 'N/A')
        
        security_level = 0
        if auth in ['open', '开放']:
            security_level = 0
        elif 'wep' in auth:
            security_level = 20
        elif 'wpa' in auth and 'wpa2' not in auth and 'wpa3' not in auth:
            security_level = 40
        elif 'wpa2' in auth:
            security_level = 70
        elif 'wpa3' in auth:
            security_level = 95
        else:
            security_level = 50
        
        # WiFi 6E/7协议建议
        protocol_note = ""
        if 'WiFi 6E' in wifi_standard or 'WiFi 7' in wifi_standard:
            if 'wpa3' not in auth:
                protocol_note = " [警告：WiFi 6E/7应使用WPA3加密]"
                security_level = min(security_level, 60)  # 降低评分
        
        return {
            'security_level': security_level,
            'encryption_type': auth,
            'wifi_protocol': wifi_standard,
            'recommendation': self._get_encryption_recommendation(security_level, wifi_standard) + protocol_note
        }
    
    def _get_encryption_recommendation(self, level: int, wifi_standard: str = 'N/A') -> str:
        """获取加密建议（考虑WiFi协议版本）"""
        # WiFi 6E/7强制建议WPA3
        if 'WiFi 6E' in wifi_standard or 'WiFi 7' in wifi_standard:
            if level < 95:
                return "WiFi 6E/7网络强烈建议使用WPA3加密"
            else:
                return "加密方式符合WiFi 6E/7标准"
        
        # 其他WiFi协议的通用建议
        if level < 40:
            return "强烈建议升级到WPA2或WPA3"
        elif level < 70:
            return "建议升级到WPA2或WPA3"
        elif level < 95:
            return "安全性良好，建议升级到WPA3"
        else:
            return "加密方式安全"
    
    def check_wps_vulnerability(self, network: Dict) -> Dict:
        """评估WPS漏洞风险（统计估算，非实测）
        
        注意：Windows netsh 命令不返回WPS启用状态，
        本函数基于统计规律对WPS风险进行估算，并非实际检测。
        要确认WPS状态需使用 Wireshark 或专业无线扫描工具。
        """
        signal_percent = network.get('signal_percent', 0)
        # 确保signal_percent是数字类型
        if isinstance(signal_percent, str):
            signal_percent = int(signal_percent.rstrip('%')) if signal_percent != '未知' else 0
        elif not isinstance(signal_percent, (int, float)):
            signal_percent = 0

        auth = network.get('authentication', '').lower()

        # WPA3网络默认不支持WPS（SAE认证替代），开放网络无需WPS
        # WPA/WPA2网络大概率开启了WPS（家用路由器出厂默认开启）
        if 'wpa3' in auth or 'open' in auth or '开放' in auth:
            return {
                'vulnerable': False,
                'vulnerability_type': 'N/A',
                'severity': '低',
                'exploit_time': 'N/A',
                'note': 'WPA3/开放网络无WPS风险'
            }

        # WPA/WPA2：基于统计估算风险，信号强弱影响实际可利用性
        if 'wpa' in auth:
            # 仅在信号足够强（>50%）时才标记为可疑风险，避免误报
            if signal_percent > 50:
                return {
                    'vulnerable': True,
                    'vulnerability_type': 'WPS PIN暴力破解（估算）',
                    'severity': '中',
                    'exploit_time': '4-12小时（视WPS锁定策略而定）',
                    'note': '⚠️ 此为统计估算，建议用专业工具确认WPS状态后再判断'
                }
            else:
                return {
                    'vulnerable': False,
                    'vulnerability_type': 'WPS PIN暴力破解（低风险）',
                    'severity': '低',
                    'exploit_time': 'N/A',
                    'note': '信号弱，实际利用难度高；建议在路由器后台确认WPS是否已关闭'
                }

        return {
            'vulnerable': False,
            'vulnerability_type': 'N/A',
            'severity': '低',
            'exploit_time': 'N/A',
            'note': '无法评估'
        }
    
    def detect_evil_twin(self, networks: List[Dict]) -> List[Dict]:
        """检测Evil Twin（钓鱼热点）"""
        evil_twins = []
        ssid_groups = {}
        
        # 按SSID分组
        for network in networks:
            ssid = network.get('ssid', '')
            if ssid and ssid != 'N/A':
                if ssid not in ssid_groups:
                    ssid_groups[ssid] = []
                ssid_groups[ssid].append(network)
        
        # 检测同名但不同BSSID的网络
        for ssid, group in ssid_groups.items():
            if len(group) > 1:
                # 如果有多个相同SSID但不同BSSID
                auths = set(net.get('authentication', '') for net in group)
                
                for network in group:
                    reasons = []
                    confidence = 50
                    
                    # 检测开放网络（常见钓鱼手段）
                    if network.get('authentication', '').lower() in ['open', '开放']:
                        reasons.append('开放网络')
                        confidence += 20
                    
                    # 信号异常强（可能在附近）
                    signal_percent = network.get('signal_percent', 0)
                    # 修复：确保signal_percent是数字类型
                    if isinstance(signal_percent, str):
                        signal_percent = int(signal_percent.rstrip('%')) if signal_percent != '未知' else 0
                    elif not isinstance(signal_percent, (int, float)):
                        signal_percent = 0
                    
                    if signal_percent > 80:
                        reasons.append('信号异常强')
                        confidence += 15
                    
                    # 多种加密方式并存
                    if len(auths) > 1:
                        reasons.append('加密方式不一致')
                        confidence += 15
                    
                    if reasons:
                        evil_twins.append({
                            'ssid': ssid,
                            'bssid': network.get('bssid', 'N/A'),
                            'reasons': reasons,
                            'confidence': min(confidence, 95),
                            'recommendation': '谨慎连接，验证网络真实性'
                        })
        
        return evil_twins
    
    def detect_ssid_spoofing(self, networks: List[Dict]) -> List[Dict]:
        """检测SSID欺骗（相似SSID）"""
        spoofing = []
        ssids = [net.get('ssid', '') for net in networks if net.get('ssid') and net.get('ssid') != 'N/A']
        
        # 检测相似SSID
        for i, ssid1 in enumerate(ssids):
            for ssid2 in ssids[i+1:]:
                similarity = self._calculate_similarity(ssid1, ssid2)
                
                if similarity > 70 and similarity < 100:  # 相似但不完全相同
                    severity = '高' if similarity > 85 else '中'
                    spoofing.append({
                        'ssid1': ssid1,
                        'ssid2': ssid2,
                        'similarity': similarity,
                        'warning': f'两个SSID高度相似，可能是欺骗网络',
                        'severity': severity
                    })
        
        return spoofing
    
    def _calculate_similarity(self, s1: str, s2: str) -> int:
        """计算字符串相似度（简化版）"""
        if s1 == s2:
            return 100
        
        s1_lower = s1.lower()
        s2_lower = s2.lower()
        
        # Levenshtein距离简化版
        if s1_lower in s2_lower or s2_lower in s1_lower:
            return 80
        
        # 检查共同字符
        common = set(s1_lower) & set(s2_lower)
        total = set(s1_lower) | set(s2_lower)
        
        if total:
            return int((len(common) / len(total)) * 100)
        
        return 0


class PasswordStrengthAnalyzer:
    """密码强度分析器"""
    
    def analyze(self, password: str) -> Dict:
        """分析密码强度"""
        score = 0
        feedback = []
        
        # 长度检查
        if len(password) < 8:
            feedback.append("密码太短（至少8位）")
        elif len(password) < 12:
            score += 20
            feedback.append("建议使用12位以上密码")
        else:
            score += 40
        
        # 复杂度检查
        if re.search(r'[a-z]', password):
            score += 15
        else:
            feedback.append("缺少小写字母")
        
        if re.search(r'[A-Z]', password):
            score += 15
        else:
            feedback.append("缺少大写字母")
        
        if re.search(r'[0-9]', password):
            score += 15
        else:
            feedback.append("缺少数字")
        
        if re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"|,.<>/?]', password):
            score += 15
        else:
            feedback.append("缺少特殊字符")
        
        # 强度等级
        if score < 40:
            strength = "弱"
        elif score < 70:
            strength = "中"
        else:
            strength = "强"
        
        return {
            'score': score,
            'strength': strength,
            'feedback': feedback
        }


class SecurityScoreCalculator:
    """安全评分计算器"""
    
    def calculate(self, scan_results: Dict) -> Dict:
        """计算综合安全评分"""
        total_networks = scan_results.get('total', 0)
        
        if total_networks == 0:
            return {
                'score': 100,
                'grade': 'A',
                'risks': []
            }
        
        score = 100
        risks = []
        
        # 开放网络扣分
        open_count = len(scan_results.get('open', []))
        if open_count > 0:
            deduction = min(open_count * 10, 30)
            score -= deduction
            risks.append(f"发现 {open_count} 个开放网络")
        
        # 弱加密扣分
        weak_count = len(scan_results.get('weak', []))
        if weak_count > 0:
            deduction = min(weak_count * 8, 25)
            score -= deduction
            risks.append(f"发现 {weak_count} 个弱加密网络")
        
        # WPS漏洞扣分
        wps_count = len(scan_results.get('wps', []))
        if wps_count > 0:
            deduction = min(wps_count * 15, 30)
            score -= deduction
            risks.append(f"发现 {wps_count} 个WPS漏洞")
        
        # Evil Twin扣分
        evil_count = len(scan_results.get('evil_twin', []))
        if evil_count > 0:
            deduction = min(evil_count * 12, 25)
            score -= deduction
            risks.append(f"发现 {evil_count} 个可疑钓鱼热点")
        
        # SSID欺骗扣分
        spoof_count = len(scan_results.get('ssid_spoof', []))
        if spoof_count > 0:
            deduction = min(spoof_count * 5, 15)
            score -= deduction
            risks.append(f"发现 {spoof_count} 个SSID欺骗")
        
        score = max(score, 0)
        
        # 评级
        if score >= 90:
            grade = 'A'
        elif score >= 80:
            grade = 'B'
        elif score >= 70:
            grade = 'C'
        elif score >= 60:
            grade = 'D'
        else:
            grade = 'F'
        
        return {
            'score': score,
            'grade': grade,
            'risks': risks,
            'total_networks': total_networks
        }


class DNSHijackDetector:
    """DNS劫持检测器（旧版存根，已由 wifi_modules/security/dns_detector.py 取代）"""

    def check(self) -> Dict:
        """检测DNS劫持（存根—始终返回安全状态）
        
        ⚠️ 此方法是向后兼容存根，不做真实检测。
        新代码应使用 wifi_modules.security.DNSHijackDetector.check_dns_hijacking()。
        """
        return {
            'hijacked': False,
            'dns_servers': ['未检测（请使用新版 DNSHijackDetector）'],
            'recommendation': '此为旧版存根，请使用 security.DNSHijackDetector.check_dns_hijacking() 进行实际检测'
        }

    def check_dns_hijacking(self) -> Dict:
        """与新版接口兼容的委托方法（旧版存根，不做实际检测）"""
        result = self.check()
        # 适配新版输出格式
        return {
            'hijacked': result['hijacked'],
            'hijacked_domains': [],
            'current_dns': result['dns_servers'],
            'test_results': [],
            'recommendations': [result['recommendation']]
        }
