"""
配置文件加载器
支持YAML配置文件读取和管理
"""

import os
import yaml
from typing import Dict, Any, Optional


class ConfigLoader:
    """配置文件加载器"""
    
    def __init__(self, config_dir: str = 'config'):
        """
        初始化配置加载器
        
        Args:
            config_dir: 配置文件目录
        """
        self.config_dir = config_dir
        self._config_cache: Dict[str, Any] = {}
    
    def load(self, config_file: str = 'thresholds.yml') -> Dict:
        """
        加载配置文件
        
        Args:
            config_file: 配置文件名
            
        Returns:
            配置字典
        """
        # 检查缓存
        if config_file in self._config_cache:
            return self._config_cache[config_file]
        
        config_path = os.path.join(self.config_dir, config_file)
        
        # 如果配置文件不存在，返回默认配置
        if not os.path.exists(config_path):
            return self._get_default_config()
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 缓存配置
            self._config_cache[config_file] = config
            return config
        
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return self._get_default_config()
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值（支持点号路径）
        
        Args:
            key_path: 配置键路径，如 'signal_quality.thresholds.excellent'
            default: 默认值
            
        Returns:
            配置值
        """
        config = self.load()
        
        keys = key_path.split('.')
        value = config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            'signal_quality': {
                'thresholds': {
                    'excellent': 70,
                    'good': 50,
                    'fair': 30,
                    'poor': 0
                },
                'stability': {
                    'stable': 5,
                    'moderate': 10,
                    'unstable': 10
                }
            },
            'security': {
                'compliance_levels': {
                    'full': 90,
                    'partial': 70,
                    'non_compliant': 0
                }
            },
            'report': {
                'cache': {
                    'signal_analysis_duration': 300,
                    'security_assessment_duration': 600,
                    'enable_cache': True
                }
            }
        }


# 全局配置实例
_config_loader = None


def get_config() -> ConfigLoader:
    """获取配置加载器实例（单例）"""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader


# 便捷函数
def get_value(key_path: str, default: Any = None) -> Any:
    """快速获取配置值"""
    return get_config().get(key_path, default)
