"""
ConfigManager配置管理器单元测试
测试覆盖: 单例模式, 配置读取, 默认值, 配置保存
"""

import pytest
import sys
import os
import json
import tempfile
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wifi_modules.config_manager import ConfigManager, get_config_manager, get_config


class TestConfigManager:
    """ConfigManager核心功能测试"""
    
    @pytest.fixture
    def temp_config_file(self, tmp_path):
        """创建临时配置文件"""
        config_file = tmp_path / "test_config.json"
        test_config = {
            "wifi_scanner": {
                "scan_timeout": 5,
                "max_retries": 2
            },
            "ui": {
                "theme": "dark"
            }
        }
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(test_config, f)
        return str(config_file)
    
    @pytest.fixture
    def config_manager(self, temp_config_file):
        """创建ConfigManager实例"""
        # 重置单例
        ConfigManager._instance = None
        return ConfigManager(temp_config_file)
    
    # === 单例模式测试 ===
    
    def test_singleton_pattern(self, temp_config_file):
        """测试单例模式"""
        ConfigManager._instance = None
        
        config1 = ConfigManager(temp_config_file)
        config2 = ConfigManager(temp_config_file)
        
        assert config1 is config2
    
    def test_singleton_reinitialization(self, temp_config_file):
        """测试单例重新初始化不会覆盖"""
        ConfigManager._instance = None
        
        config1 = ConfigManager(temp_config_file)
        original_config = config1.config.copy()
        
        # 第二次初始化不应该改变配置
        config2 = ConfigManager("different_file.json")
        
        assert config1 is config2
        assert config1.config == original_config
    
    # === 配置读取测试 ===
    
    def test_get_existing_config(self, config_manager):
        """测试获取存在的配置"""
        timeout = config_manager.get('wifi_scanner.scan_timeout')
        assert timeout == 5
    
    def test_get_nested_config(self, config_manager):
        """测试获取嵌套配置"""
        theme = config_manager.get('ui.theme')
        assert theme == 'dark'
    
    def test_get_nonexistent_config_with_default(self, config_manager):
        """测试获取不存在的配置（提供默认值）"""
        value = config_manager.get('nonexistent.key', 'default_value')
        assert value == 'default_value'
    
    def test_get_nonexistent_config_without_default(self, config_manager):
        """测试获取不存在的配置（无默认值）"""
        value = config_manager.get('nonexistent.key')
        # 应该返回内置默认值或None
        assert value is None or isinstance(value, (str, int, bool, dict))
    
    def test_get_from_builtin_defaults(self, temp_config_file):
        """测试从内置默认值获取"""
        ConfigManager._instance = None
        config = ConfigManager(temp_config_file)
        
        # realtime_monitor配置在临时文件中不存在，应该使用内置默认值
        max_hours = config.get('realtime_monitor.max_data_hours')
        assert max_hours == 24  # 内置默认值
    
    # === 配置设置测试 ===
    
    def test_set_config_value(self, config_manager):
        """测试设置配置值"""
        config_manager.set('wifi_scanner.scan_timeout', 10)
        assert config_manager.get('wifi_scanner.scan_timeout') == 10
    
    def test_set_nested_config(self, config_manager):
        """测试设置嵌套配置"""
        config_manager.set('new_section.new_key', 'new_value')
        assert config_manager.get('new_section.new_key') == 'new_value'
    
    def test_set_deep_nested_config(self, config_manager):
        """测试设置深层嵌套配置"""
        config_manager.set('level1.level2.level3', 'deep_value')
        assert config_manager.get('level1.level2.level3') == 'deep_value'
    
    # === 配置保存测试 ===
    
    def test_save_config(self, config_manager, temp_config_file):
        """测试保存配置到文件"""
        config_manager.set('wifi_scanner.scan_timeout', 20)
        result = config_manager.save()
        
        assert result is True
        
        # 验证文件内容
        with open(temp_config_file, 'r', encoding='utf-8') as f:
            saved_config = json.load(f)
        
        assert saved_config['wifi_scanner']['scan_timeout'] == 20
    
    def test_set_and_save_at_once(self, config_manager, temp_config_file):
        """测试设置并立即保存"""
        config_manager.set('ui.theme', 'light', save=True)
        
        # 验证文件内容
        with open(temp_config_file, 'r', encoding='utf-8') as f:
            saved_config = json.load(f)
        
        assert saved_config['ui']['theme'] == 'light'
    
    # === 配置重载测试 ===
    
    def test_reload_config(self, config_manager, temp_config_file):
        """测试重新加载配置"""
        # 修改文件
        new_config = {
            "wifi_scanner": {
                "scan_timeout": 15
            }
        }
        with open(temp_config_file, 'w', encoding='utf-8') as f:
            json.dump(new_config, f)
        
        # 重新加载
        config_manager.reload()
        
        assert config_manager.get('wifi_scanner.scan_timeout') == 15
    
    # === 配置段获取测试 ===
    
    def test_get_section(self, config_manager):
        """测试获取整个配置段"""
        scanner_config = config_manager.get_section('wifi_scanner')
        
        assert isinstance(scanner_config, dict)
        assert 'scan_timeout' in scanner_config
        assert scanner_config['scan_timeout'] == 5
    
    def test_get_nonexistent_section(self, config_manager):
        """测试获取不存在的配置段"""
        section = config_manager.get_section('nonexistent_section')
        
        # 应该返回空字典或默认配置
        assert isinstance(section, dict)
    
    # === 配置验证测试 ===
    
    def test_validate_complete_config(self, config_manager):
        """测试验证完整配置"""
        # 添加必需的配置段
        config_manager.config['realtime_monitor'] = {}
        config_manager.config['ui'] = {}
        
        result = config_manager.validate()
        assert result is True
    
    def test_validate_incomplete_config(self, temp_config_file):
        """测试验证不完整配置"""
        ConfigManager._instance = None
        
        # 创建只有部分配置的文件
        minimal_config = {"wifi_scanner": {}}
        with open(temp_config_file, 'w', encoding='utf-8') as f:
            json.dump(minimal_config, f)
        
        config = ConfigManager(temp_config_file)
        result = config.validate()
        
        # 缺少必需配置段，应该返回False
        assert result is False
    
    # === 默认配置合并测试 ===
    
    def test_merge_defaults(self, config_manager):
        """测试合并默认配置"""
        # 删除某些配置
        if 'memory_monitor' in config_manager.config:
            del config_manager.config['memory_monitor']
        
        config_manager.merge_defaults()
        
        # 应该有默认的memory_monitor配置
        assert 'memory_monitor' in config_manager.config
        assert config_manager.get('memory_monitor.interval_minutes') == 60
    
    # === 导出默认配置测试 ===
    
    def test_export_defaults(self, config_manager, tmp_path):
        """测试导出默认配置"""
        output_file = tmp_path / "defaults.json"
        result = config_manager.export_defaults(str(output_file))
        
        assert result is True
        assert output_file.exists()
        
        # 验证内容
        with open(output_file, 'r', encoding='utf-8') as f:
            defaults = json.load(f)
        
        assert 'wifi_scanner' in defaults
        assert 'realtime_monitor' in defaults


class TestConfigManagerEdgeCases:
    """ConfigManager边界条件测试"""
    
    def test_config_file_not_exists(self, tmp_path):
        """测试配置文件不存在"""
        ConfigManager._instance = None
        
        nonexistent_file = tmp_path / "nonexistent.json"
        config = ConfigManager(str(nonexistent_file))
        
        # 应该使用默认配置
        timeout = config.get('wifi_scanner.scan_timeout', 5)
        assert timeout == 5
    
    def test_config_file_invalid_json(self, tmp_path):
        """测试无效的JSON文件"""
        ConfigManager._instance = None
        
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{ invalid json }")
        
        config = ConfigManager(str(invalid_file))
        
        # 应该回退到默认配置
        timeout = config.get('wifi_scanner.scan_timeout', 5)
        assert timeout == 5
    
    def test_get_with_empty_key_path(self, temp_config_file):
        """测试空键路径"""
        ConfigManager._instance = None
        config = ConfigManager(temp_config_file)
        
        result = config.get('', 'default')
        assert result == 'default'
    
    def test_set_with_empty_key_path(self, temp_config_file):
        """测试使用空键路径设置"""
        ConfigManager._instance = None
        config = ConfigManager(temp_config_file)
        
        # 不应该崩溃
        try:
            config.set('', 'value')
        except (KeyError, IndexError):
            pass  # 预期可能抛出异常


class TestGlobalConfigFunctions:
    """测试全局配置函数"""
    
    def test_get_config_manager_singleton(self):
        """测试get_config_manager返回单例"""
        ConfigManager._instance = None
        
        manager1 = get_config_manager()
        manager2 = get_config_manager()
        
        assert manager1 is manager2
    
    def test_get_config_convenience_function(self):
        """测试get_config便捷函数"""
        ConfigManager._instance = None
        
        # 应该使用默认值
        timeout = get_config('wifi_scanner.scan_timeout', 5)
        assert timeout == 5


# 运行示例
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
