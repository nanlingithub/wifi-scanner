"""
WiFi密码强度分析模块
功能：密码复杂度评估、字典检测、熵计算、破解时间估算
版本：V2.0 Enhanced (集成扩展密码字典库)
"""

import re
import math
from typing import Dict, List, Any, Optional

# 导入扩展密码字典库
try:
    from .password_dictionary import PasswordDictionary
    HAS_EXTENDED_DICT = True
except ImportError:
    HAS_EXTENDED_DICT = False


class PasswordStrengthAnalyzer:
    """密码强度分析器"""
    
    # 常见密码Top 100（简化版，实际应包含10000+）
    COMMON_PASSWORDS = {
        '123456', 'password', '12345678', 'qwerty', '123456789',
        '12345', '1234', '111111', '1234567', 'dragon',
        '123123', 'baseball', 'iloveyou', 'trustno1', '1234567890',
        'sunshine', 'master', '123321', '666666', '987654321',
        'password1', 'qwertyuiop', 'mynoob', '123abc', 'abc123',
        'qwerty123', '1q2w3e4r', 'admin', 'qwertyui', 'letmein',
        'monkey', '1234qwer', 'qazwsx', 'dragon', '111111',
        'baseball', 'iloveyou', 'welcome', 'login', 'princess',
        '1qaz2wsx', 'solo', 'passw0rd', 'starwars', 'charlie',
        'aa123456', 'donald', 'password123', '!@#$%^&*', 'zaq1zaq1',
        # 中文常见密码
        'woaini', 'wocaonima', 'woaini520', '5201314', '1314520',
        'qwe123', 'asd123', 'zxc123', 'abc123456', '11111111',
        '00000000', '88888888', '12341234', 'abcd1234', 'test123'
    }
    
    # 弱密码模式（正则表达式）
    WEAK_PATTERNS = [
        (r'^\d+$', '纯数字'),
        (r'^[a-z]+$', '纯小写字母'),
        (r'^[A-Z]+$', '纯大写字母'),
        (r'^(.)\1+$', '重复字符（如：aaaa）'),
        (r'(012|123|234|345|456|567|678|789|890)', '连续数字'),
        (r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', '连续字母'),
        (r'(qwer|asdf|zxcv|qaz|wsx|edc)', '键盘序列'),
        (r'^(password|passw0rd|admin|root|user|test|guest).*', '常见单词'),
    ]
    
    def __init__(self):
        # 初始化扩展密码字典库
        if HAS_EXTENDED_DICT:
            self.password_dict = PasswordDictionary()
        else:
            self.password_dict = None
    
    def evaluate_password(self, password: str, ssid: str = '') -> Dict[str, Any]:
        """
        评估密码强度（增强版）
        
        Args:
            password: 密码
            ssid: WiFi名称（检测密码是否包含SSID）
            
        Returns:
            评估结果字典
        """
        if not password:
            return {
                'score': 0,
                'rating': '未设置',
                'entropy': 0,
                'crack_time': '瞬间',
                'strength_percent': 0,
                'issues': ['密码为空'],
                'recommendations': ['必须设置密码']
            }
        
        # 优先使用扩展密码字典库
        if self.password_dict:
            detailed_result = self.password_dict.check_password_strength(password)
            
            # 转换为兼容格式
            return {
                'score': detailed_result['score'],
                'rating': self._convert_strength_rating(detailed_result['strength']),
                'entropy': detailed_result['details']['entropy']['entropy'],
                'crack_time': detailed_result['crack_time'],
                'strength_percent': detailed_result['score'],
                'issues': detailed_result['issues'],
                'recommendations': detailed_result['suggestions'],
                'details': detailed_result['details'],  # 新增详细信息
                'in_dictionary': detailed_result['in_dictionary']
            }
        
        # 回退到原有评估逻辑（向后兼容）
        score = 0
        issues = []
        
        # 1. 长度检查（最重要）
        length = len(password)
        if length < 8:
            issues.append(f'密码过短（{length}位 < 8位）')
        elif length >= 16:
            score += 3
        elif length >= 12:
            score += 2
        else:
            score += 1
        
        # 2. 复杂度检查
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?/~`]', password))
        
        complexity = sum([has_upper, has_lower, has_digit, has_special])
        
        if complexity == 4:
            score += 3
        elif complexity == 3:
            score += 2
        elif complexity >= 2:
            score += 1
        else:
            issues.append('缺少字符类型组合（大写/小写/数字/符号）')
        
        # 3. 字典攻击检查（最严重）
        if password.lower() in self.COMMON_PASSWORDS:
            score = 0  # 直接归零
            issues.append('⚠️ 密码在常见密码字典中，极易被破解！')
        
        # 4. 弱模式检查
        for pattern, description in self.WEAK_PATTERNS:
            if re.search(pattern, password, re.IGNORECASE):
                score = max(0, score - 1)
                issues.append(f'密码模式过于简单：{description}')
                break
        
        # 5. SSID检查（密码不应包含SSID）
        if ssid and ssid.lower() in password.lower():
            score = max(0, score - 1)
            issues.append('密码包含WiFi名称，容易被猜测')
        
        # 6. 重复字符检查
        if self._has_repeated_chars(password):
            score = max(0, score - 1)
            issues.append('包含过多重复字符')
        
        # 7. 计算熵（信息量）
        entropy = self._calculate_entropy(password, has_upper, has_lower, 
                                          has_digit, has_special)
        
        # 8. 估算破解时间
        crack_time = self._estimate_crack_time(entropy)
        
        # 9. 最终评分（0-5）
        final_score = min(max(score, 0), 5)
        
        # 10. 评级
        ratings = ['极弱', '弱', '中等', '较强', '强', '极强']
        rating = ratings[final_score]
        
        # 11. 生成建议
        recommendations = self._generate_recommendations(
            length, complexity, issues, entropy
        )
        
        return {
            'score': final_score,
            'rating': rating,
            'entropy': round(entropy, 1),
            'crack_time': crack_time,
            'strength_percent': min(int((entropy / 100) * 100), 100),
            'length': length,
            'complexity': {
                'has_upper': has_upper,
                'has_lower': has_lower,
                'has_digit': has_digit,
                'has_special': has_special,
                'types': complexity
            },
            'issues': issues,
            'recommendations': recommendations
        }
    
    def check_common_password(self, password: str) -> bool:
        """检查是否为常见密码"""
        return password.lower() in self.COMMON_PASSWORDS
    
    def generate_strong_password(self, length: int = 16) -> str:
        """
        生成强密码
        
        Args:
            length: 密码长度
            
        Returns:
            随机强密码
        """
        import random
        import string
        
        # 确保包含所有字符类型
        chars = []
        chars.append(random.choice(string.ascii_uppercase))  # 大写
        chars.append(random.choice(string.ascii_lowercase))  # 小写
        chars.append(random.choice(string.digits))           # 数字
        chars.append(random.choice('!@#$%^&*()_+-='))       # 符号
        
        # 填充剩余长度
        all_chars = string.ascii_letters + string.digits + '!@#$%^&*()_+-='
        chars.extend(random.choice(all_chars) for _ in range(length - 4))
        
        # 打乱顺序
        random.shuffle(chars)
        
        return ''.join(chars)
    
    # ===== 辅助方法 =====
    
    def _calculate_entropy(self, password: str, has_upper: bool, 
                          has_lower: bool, has_digit: bool, 
                          has_special: bool) -> float:
        """
        计算密码熵（信息量）
        
        熵 = log2(字符集大小^密码长度)
        """
        charset_size = 0
        
        if has_lower:
            charset_size += 26
        if has_upper:
            charset_size += 26
        if has_digit:
            charset_size += 10
        if has_special:
            charset_size += 32  # 常见符号
        
        if charset_size == 0:
            return 0
        
        length = len(password)
        entropy = length * math.log2(charset_size)
        
        return entropy
    
    def _estimate_crack_time(self, entropy: float) -> str:
        """
        估算破解时间
        
        假设：
        - 在线攻击：100次/秒（路由器限速）
        - 离线攻击：10^10次/秒（GPU集群）
        """
        # 使用离线攻击速度（更危险）
        attack_rate = 10**10  # 100亿次/秒
        
        combinations = 2 ** entropy
        seconds = combinations / (2 * attack_rate)  # 平均需要尝试一半
        
        # 转换为可读格式
        if seconds < 1:
            return "瞬间"
        elif seconds < 60:
            return f"{seconds:.0f}秒"
        elif seconds < 3600:
            return f"{seconds/60:.0f}分钟"
        elif seconds < 86400:
            return f"{seconds/3600:.1f}小时"
        elif seconds < 2592000:  # 30天
            return f"{seconds/86400:.0f}天"
        elif seconds < 31536000:  # 1年
            return f"{seconds/2592000:.1f}个月"
        elif seconds < 3153600000:  # 100年
            return f"{seconds/31536000:.0f}年"
        else:
            return "数世纪"
    
    def _convert_strength_rating(self, strength: str) -> str:
        """转换强度等级为中文评级"""
        mapping = {
            'VERY_WEAK': '极弱',
            'WEAK': '弱',
            'MODERATE': '中等',
            'STRONG': '强',
            'VERY_STRONG': '极强'
        }
        return mapping.get(strength, '未知')
    
    def _has_repeated_chars(self, password: str, threshold: int = 3) -> bool:
        """检测重复字符（连续3个以上相同字符）"""
        for i in range(len(password) - threshold + 1):
            if len(set(password[i:i+threshold])) == 1:
                return True
        return False
    
    def _generate_recommendations(self, length: int, complexity: int,
                                 issues: List[str], entropy: float) -> List[str]:
        """生成个性化建议"""
        recommendations = []
        
        # 长度建议
        if length < 8:
            recommendations.append('❗ 密码至少8位，建议12-16位')
        elif length < 12:
            recommendations.append('✅ 可增加长度到12-16位以提高安全性')
        
        # 复杂度建议
        if complexity < 3:
            recommendations.append('❗ 使用大写+小写+数字+符号的组合')
        elif complexity == 3:
            recommendations.append('✅ 可添加更多符号提高复杂度')
        
        # 熵建议
        if entropy < 40:
            recommendations.append('❗ 密码强度不足，易被暴力破解')
        elif entropy < 60:
            recommendations.append('⚠️ 密码强度一般，建议增强')
        elif entropy < 80:
            recommendations.append('✅ 密码强度良好')
        else:
            recommendations.append('✅ 密码强度优秀！')
        
        # 字典攻击建议
        if any('常见密码字典' in issue for issue in issues):
            recommendations.append('❗ 立即更换为随机密码，避免使用常见单词')
        
        # 通用建议
        if not recommendations:
            recommendations.append('✅ 密码强度达标，定期更换密码以保持安全')
        
        return recommendations
