"""
企业级日志系统配置
替换print语句，提供结构化日志记录
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler


class EnterpriseLogger:
    """企业级日志管理器"""
    
    def __init__(self, name: str = 'enterprise_report', log_dir: str = 'logs'):
        """
        初始化日志系统
        
        Args:
            name: 日志器名称
            log_dir: 日志目录
        """
        self.log_dir = log_dir
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # 确保日志目录存在
        os.makedirs(log_dir, exist_ok=True)
        
        # 清除已有的处理器（避免重复）
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # 配置处理器
        self._setup_handlers()
    
    def _setup_handlers(self):
        """设置日志处理器"""
        # 1. 文件处理器（所有日志）
        log_file = os.path.join(self.log_dir, 'enterprise_report.log')
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        # 2. 错误日志文件（仅ERROR及以上）
        error_log_file = os.path.join(self.log_dir, 'errors.log')
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        
        # 3. 控制台处理器（INFO及以上）
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        # 添加所有处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
    
    def debug(self, msg: str, **kwargs):
        """调试日志"""
        self.logger.debug(msg, extra=kwargs)
    
    def info(self, msg: str, **kwargs):
        """信息日志"""
        self.logger.info(msg, extra=kwargs)
    
    def warning(self, msg: str, **kwargs):
        """警告日志"""
        self.logger.warning(msg, extra=kwargs)
    
    def error(self, msg: str, **kwargs):
        """错误日志"""
        self.logger.error(msg, extra=kwargs)
    
    def critical(self, msg: str, **kwargs):
        """严重错误日志"""
        self.logger.critical(msg, extra=kwargs)
    
    def exception(self, msg: str, **kwargs):
        """异常日志（自动记录堆栈）"""
        self.logger.exception(msg, extra=kwargs)


# 全局日志实例
_logger_instances = {}


def get_logger(name: str = 'enterprise_report') -> EnterpriseLogger:
    """
    获取日志实例（单例模式）
    
    Args:
        name: 日志器名称
        
    Returns:
        日志实例
    """
    if name not in _logger_instances:
        _logger_instances[name] = EnterpriseLogger(name)
    return _logger_instances[name]


# 便捷导出
logger = get_logger()
