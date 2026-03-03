"""
安全评分增强模块 - 向后兼容重导出
所有函数已合并至 scoring.py，此文件保留以兼容现有导入路径。

新代码请直接从 wifi_modules.security.scoring 导入。
"""

# 相对导入，消除重复实现
from .scoring import (
    calculate_encryption_score,
    calculate_wps_risk_score,
    calculate_password_strength_score,
    get_security_grade,
    SecurityScorer,
)

__all__ = [
    'calculate_encryption_score',
    'calculate_wps_risk_score',
    'calculate_password_strength_score',
    'get_security_grade',
    'SecurityScorer',
]
