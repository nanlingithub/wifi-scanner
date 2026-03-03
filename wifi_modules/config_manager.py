"""
统一配置管理模块
集中管理所有应用配置，支持层级访问和默认值
"""

import json
import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigManager:
    """统一配置管理器（单例）

    职责:
    - JSON 应用配置 (config.json): 通过 get(key) / set(key) 访问
    - YAML 阈值配置 (config/thresholds.yml): 通过 get_yaml(key) 访问

    新代码统一使用本类，无需直接实例化 ConfigLoader。

    示例:
        config = ConfigManager()
        timeout = config.get('wifi_scanner.scan_timeout', 5)
        threshold = ConfigManager.get_yaml('signal_quality.thresholds.excellent', default=70)
    """
    
    _instance = None  # 单例模式
    
    def __new__(cls, *args, **kwargs):
        """单例模式: 确保全局只有一个配置管理器实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config_file: str = 'config.json'):
        """初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        # 避免重复初始化
        if hasattr(self, '_initialized'):
            return
        
        self.config_file = config_file
        self.config: Dict[str, Any] = {}
        self.logger = logging.getLogger('ConfigManager')
        
        # 默认配置
        self._defaults = {
            'wifi_scanner': {
                'scan_timeout': 5,
                'max_retries': 2,
                'retry_delay': 0.3,
                'cache_timeout_seconds': 2.0,
                'quick_mode': True
            },
            'realtime_monitor': {
                'max_data_hours': 24,
                'downsample_threshold': 1000,
                'update_interval_seconds': 0.5,
                'smoothing_enabled': True,
                'outlier_filter_enabled': True
            },
            'memory_monitor': {
                'interval_minutes': 60,
                'log_file': 'logs/memory_monitor.log',
                'baseline_threshold_mb': 200,
                'warning_threshold_mb': 500
            },
            'ui': {
                'default_theme': 'light',
                'window_width': 1400,
                'window_height': 900,
                'font_family': 'Microsoft YaHei UI',
                'font_size': 10
            },
            'export': {
                'default_format': 'csv',
                'compression_enabled': False,
                'timestamp_format': '%Y%m%d_%H%M%S'
            },
            'security': {
                'enable_wps_scan': True,
                'enable_dns_check': True,
                'risk_score_threshold': 60,
                'alert_on_open_network': True
            }
        }
        
        self._load_config()
        self._initialized = True
    
    def _load_config(self) -> None:
        """从文件加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                self.logger.info(f"✅ 配置文件已加载: {self.config_file}")
            else:
                self.logger.warning(f"⚠️ 配置文件不存在: {self.config_file}，使用默认配置")
                self.config = {}
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ 配置文件JSON格式错误: {e}")
            self.config = {}
        except Exception as e:
            self.logger.error(f"❌ 加载配置文件失败: {e}")
            self.config = {}
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """获取配置值（支持点号路径）
        
        Args:
            key_path: 配置路径，如 'wifi_scanner.timeout'
            default: 默认值（如果未指定，则使用内置默认值）
        
        Returns:
            配置值，如果不存在则返回默认值
        
        示例:
            timeout = config.get('wifi_scanner.scan_timeout', 5)
        """
        keys = key_path.split('.')
        value = self.config
        
        # 尝试从配置文件获取
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                # 尝试从默认配置获取
                return self._get_default(key_path, default)
        
        return value
    
    def _get_default(self, key_path: str, user_default: Any = None) -> Any:
        """从默认配置获取值
        
        Args:
            key_path: 配置路径
            user_default: 用户指定的默认值
        
        Returns:
            默认值（优先用户指定 > 内置默认值）
        """
        keys = key_path.split('.')
        value = self._defaults
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return user_default
        
        return value

    # ─────────────────────────────────────────────
    # YAML 阈值配置统一入口
    # 使 ConfigManager 成为所有配置的单一门面，
    # 避免调用方直接实例化 ConfigLoader。
    # ─────────────────────────────────────────────
    @classmethod
    def get_yaml(cls, key_path: str, config_file: str = 'thresholds.yml',
                 default=None):
        """从 YAML 配置文件获取阈值（委托给 ConfigLoader）。

        Args:
            key_path:    点号路径，如 'signal_quality.thresholds.excellent'
            config_file: YAML 文件名，默认 thresholds.yml
            default:     找不到时的返回值

        Returns:
            配置值或 default

        示例:
            threshold = ConfigManager.get_yaml('signal_quality.thresholds.excellent', default=70)
        """
        from .config_loader import ConfigLoader  # 延迟导入避免循环
        loader = ConfigLoader()
        return loader.get(key_path, default)

    def set(self, key_path: str, value: Any, save: bool = False) -> None:
        """设置配置值

        Args:
            key_path: 配置路径
            value: 配置值
            save: 是否立即保存到文件
        """
        keys = key_path.split('.')
        config = self.config

        # 创建嵌套字典结构
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # 设置值
        config[keys[-1]] = value
        
        if save:
            self.save()
    
    def save(self) -> bool:
        """保存配置到文件
        
        Returns:
            是否成功保存
        """
        try:
            # 确保目录存在
            config_dir = os.path.dirname(self.config_file)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            
            self.logger.info(f"✅ 配置已保存: {self.config_file}")
            return True
        except Exception as e:
            self.logger.error(f"❌ 保存配置失败: {e}")
            return False
    
    def reload(self) -> None:
        """重新加载配置文件"""
        self._load_config()
        self.logger.info("🔄 配置已重新加载")
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """获取整个配置段
        
        Args:
            section: 配置段名称，如 'wifi_scanner'
        
        Returns:
            配置段字典
        """
        return self.config.get(section, self._defaults.get(section, {}))
    
    def validate(self) -> bool:
        """验证配置完整性
        
        Returns:
            配置是否有效
        """
        required_sections = ['wifi_scanner', 'realtime_monitor', 'ui']
        missing_sections = [s for s in required_sections if s not in self.config]
        
        if missing_sections:
            self.logger.warning(f"⚠️ 缺少配置段: {missing_sections}，将使用默认值")
        
        return len(missing_sections) == 0
    
    def merge_defaults(self) -> None:
        """将默认配置合并到当前配置（不覆盖已存在的值）"""
        def deep_merge(target: dict, source: dict) -> dict:
            """深度合并字典"""
            for key, value in source.items():
                if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                    deep_merge(target[key], value)
                elif key not in target:
                    target[key] = value
            return target
        
        self.config = deep_merge(self.config, self._defaults)
        self.logger.info("✅ 默认配置已合并")
    
    def export_defaults(self, output_file: str = 'config.default.json') -> bool:
        """导出默认配置到文件（用于参考）
        
        Args:
            output_file: 输出文件路径
        
        Returns:
            是否成功导出
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self._defaults, f, indent=4, ensure_ascii=False)
            self.logger.info(f"✅ 默认配置已导出: {output_file}")
            return True
        except Exception as e:
            self.logger.error(f"❌ 导出默认配置失败: {e}")
            return False


# 全局配置管理器实例
_global_config_manager = None


def get_config_manager(config_file: str = 'config.json') -> ConfigManager:
    """获取全局配置管理器实例（单例）
    
    Args:
        config_file: 配置文件路径
    
    Returns:
        ConfigManager实例
    """
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = ConfigManager(config_file)
    return _global_config_manager


# 便捷函数
def get_config(key_path: str, default: Any = None) -> Any:
    """快捷获取配置值
    
    Args:
        key_path: 配置路径
        default: 默认值
    
    Returns:
        配置值
    """
    return get_config_manager().get(key_path, default)
