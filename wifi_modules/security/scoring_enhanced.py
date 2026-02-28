"""
安全评分增强模块
实现独立的安全评分函数，支持测试用例
"""


def calculate_encryption_score(encryption_type: str, authentication: str = None) -> int:
    """
    计算加密方式评分（返回整数分数）
    
    Args:
        encryption_type: 加密类型 (WPA3-SAE, WPA2-CCMP, WEP, Open等)
        authentication: 认证方式 (可选)
    
    Returns:
        int: 0-100的整数分数
    """
    encryption_type = str(encryption_type).upper()
    
    # WPA3 - 最高安全级别
    if 'WPA3' in encryption_type:
        if 'ENTERPRISE' in encryption_type or 'EAP' in encryption_type:
            return 100
        if 'SAE' in encryption_type or 'PERSONAL' in encryption_type:
            return 100
        return 95  # 其他WPA3变体
    
    # WPA2 - 良好安全级别（注意：Enterprise必须先于PSK/AES检测）
    if 'WPA2' in encryption_type:
        if 'ENTERPRISE' in encryption_type or 'EAP' in encryption_type:
            return 90
        # 混合模式检测
        if 'WPA3' in encryption_type:
            return 90  # WPA2/WPA3混合模式
        if 'WPA' in encryption_type and 'WPA2' in encryption_type and encryption_type.index('WPA') < encryption_type.index('WPA2'):
            return 70  # WPA/WPA2混合模式
        # 单一WPA2模式
        if 'AES' in encryption_type or 'CCMP' in encryption_type or 'PSK' in encryption_type:
            return 85  # WPA2-AES/PSK都是85分
        return 85  # WPA2默认85分
    
    # WPA (旧版) - 中等安全级别
    if 'WPA' in encryption_type:
        if 'WPA2' in encryption_type:
            return 70  # WPA/WPA2混合模式
        if 'TKIP' in encryption_type or 'PSK' in encryption_type:
            return 50  # WPA-TKIP/PSK分数降至50
        return 55  # WPA其他变体
    
    # WEP - 严重不安全
    if 'WEP' in encryption_type:
        return 10
    
    # Open - 无加密
    if 'OPEN' in encryption_type or 'NONE' in encryption_type or not encryption_type:
        return 0
    
    # 未知加密
    return 30


def calculate_wps_risk_score(wps_enabled=False, wps_locked=False, has_pixie_dust=False, 
                             pin_enabled=False, pbc_enabled=False, 
                             pin_retries_exceeded=False, has_null_pin=False) -> int:
    """
    计算WPS风险评分（返回整数分数）
    
    Args:
        wps_enabled: WPS是否启用
        wps_locked: WPS是否锁定
        has_pixie_dust: 是否存在Pixie Dust漏洞
        pin_enabled: 是否启用PIN方法
        pbc_enabled: 是否启用PBC方法
        pin_retries_exceeded: PIN重试是否超限
        has_null_pin: 是否存在空PIN漏洞
    
    Returns:
        int: 0-100的整数分数（越低越危险）
    """
    if not wps_enabled:
        return 100
    
    score = 80  # 基础分（WPS开启）
    
    # 检查是否锁定（锁定可提升安全性）
    if wps_locked:
        score += 5
    else:
        score -= 30  # 未锁定，风险较高
    
    # 严重漏洞检测
    if has_pixie_dust:
        score -= 50
    
    if has_null_pin:
        score -= 40
    
    if pin_retries_exceeded:
        score += 5  # 重试超限会自动锁定，稍微安全点
    
    # 检查WPS方法
    if pin_enabled:
        score -= 10
    
    return max(0, min(100, score))



def calculate_password_strength_score(password: str) -> int:
    """
    计算密码强度评分（返回整数分数）
    
    Args:
        password: 密码字符串
    
    Returns:
        int: 0-100的整数分数
    """
    if not password:
        return 0
    
    score = 0
    
    # 长度检查（调整权重以满足测试边界）
    length = len(password)
    if length >= 16:
        score += 40  # 16+字符
    elif length >= 12:
        score += 25  # 12-15字符
    elif length >= 8:
        score += 15  # 8-11字符
    else:
        score += 5
    
    # 字符多样性检查
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    
    diversity_count = sum([has_lower, has_upper, has_digit, has_special])
    score += diversity_count * 15  # 每种字符类型15分
    
    # 常见密码检查
    common_passwords = [
        'password', '12345678', 'qwerty', 'admin', '123456',
        'password123', 'admin123', '11111111', '00000000', '1234567890'
    ]
    if password.lower() in common_passwords:
        score = min(score, 20)
    
    # 连续字符检查（简化）
    if '123' in password or 'abc' in password.lower():
        score -= 5
    
    # 重复字符检查（简化）
    if len(set(password)) < len(password) / 2:
        score -= 5
    
    return max(0, min(100, score))



def get_security_grade(score: int) -> tuple:
    """
    根据分数获取安全等级（返回元组）
    
    Args:
        score: 安全评分 (0-100)
    
    Returns:
        tuple: (grade, color)
            grade: 安全等级 ('A+'|'A'|'B'|'C'|'D'|'F')
            color: 颜色代码
    """
    if score >= 95:
        return ('A+', '#00C853')
    elif score >= 85:
        return ('A', '#4CAF50')
    elif score >= 75:
        return ('B', '#8BC34A')
    elif score >= 65:
        return ('C', '#FFC107')
    elif score >= 50:
        return ('D', '#FF9800')
    else:
        return ('F', '#F44336')



class SecurityScorer:
    """
    安全评分器 - 综合评分类
    """
    
    def __init__(self):
        self.weights = {
            'encryption': 0.4,
            'wps': 0.2,
            'password': 0.2,
            'authentication': 0.2
        }
    
    def calculate_score(self, encryption="Unknown", authentication="", wps_enabled=False,
                       wps_locked=True, has_pixie_dust=False, password_strength=None,
                       password=None) -> dict:
        """
        对网络进行综合安全评分
        
        Args:
            encryption: 加密类型
            authentication: 认证方式
            wps_enabled: WPS是否启用
            wps_locked: WPS是否锁定
            has_pixie_dust: 是否存在Pixie Dust漏洞
            password_strength: 密码强度分数（可选）
            password: 密码字符串（可选）
        
        Returns:
            dict: {
                'total_score': int,
                'encryption_score': int,
                'wps_score': int,
                'password_score': int,
                'grade': str,
                'color': str,
                'vulnerabilities': list,
                'recommendations': list
            }
        """
        scores = {}
        vulnerabilities = []
        
        # 加密评分
        scores['encryption'] = calculate_encryption_score(encryption, authentication)
        if scores['encryption'] < 70:
            vulnerabilities.append('encryption')
        
        # WPS评分
        scores['wps'] = calculate_wps_risk_score(
            wps_enabled=wps_enabled,
            wps_locked=wps_locked,
            has_pixie_dust=has_pixie_dust
        )
        if wps_enabled:
            vulnerabilities.append('wps')
        if has_pixie_dust:
            vulnerabilities.append('pixie_dust')
        
        # 密码评分（优先使用password_strength参数）
        if password_strength is not None:
            scores['password'] = password_strength
        elif password:
            scores['password'] = calculate_password_strength_score(password)
        else:
            scores['password'] = 50  # 默认中等
        
        if scores['password'] < 60:
            vulnerabilities.append('weak_password')
        
        # 认证评分
        auth = str(authentication).upper() if authentication else encryption.upper()
        if 'WPA3' in auth and 'ENTERPRISE' in auth:
            scores['authentication'] = 100
        elif 'WPA2' in auth and 'ENTERPRISE' in auth:
            scores['authentication'] = 90
        elif 'WPA3' in auth:
            scores['authentication'] = 95
        elif 'WPA2' in auth:
            scores['authentication'] = 80
        elif 'WPA' in auth:
            scores['authentication'] = 50
        elif 'WEP' in auth:
            scores['authentication'] = 10
            vulnerabilities.append('wep')
        else:
            scores['authentication'] = 0
        
        # 计算加权总分
        total_score = int(sum(
            scores[key] * self.weights[key]
            for key in scores
        ))
        
        grade, color = get_security_grade(total_score)
        
        # 生成建议
        recommendations = []
        if scores['encryption'] < 70:
            recommendations.append('升级到WPA2-AES或WPA3加密')
        if wps_enabled:
            recommendations.append('禁用WPS功能以提高安全性')
        if has_pixie_dust:
            recommendations.append('WPS存在Pixie Dust漏洞，立即禁用')
        if scores['password'] < 60:
            recommendations.append('使用更强的密码（至少12位，包含大小写字母、数字、特殊字符）')
        
        return {
            'total_score': total_score,
            'encryption_score': scores['encryption'],
            'wps_score': scores['wps'],
            'password_score': scores['password'],
            'grade': grade,
            'color': color,
            'vulnerabilities': vulnerabilities,
            'recommendations': recommendations
        }
