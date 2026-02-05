#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
工具函数模块 - 提供输入验证、日志配置等通用功能
"""

import re
import socket
import logging
import os
from datetime import datetime


class InputValidator:
    """输入验证类"""
    
    @staticmethod
    def is_valid_ip(ip_address):
        """验证IP地址格式
        
        Args:
            ip_address: IP地址字符串
            
        Returns:
            bool: 是否为有效的IPv4地址
        """
        if not ip_address:
            return False
        
        # IPv4 正则表达式
        ipv4_pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        match = re.match(ipv4_pattern, ip_address)
        
        if not match:
            return False
        
        # 检查每个部分是否在0-255范围内
        try:
            parts = [int(x) for x in match.groups()]
            return all(0 <= part <= 255 for part in parts)
        except ValueError:
            return False
    
    @staticmethod
    def is_valid_domain(domain):
        """验证域名格式
        
        Args:
            domain: 域名字符串
            
        Returns:
            bool: 是否为有效的域名
        """
        if not domain:
            return False
        
        # 域名正则表达式（简化版）
        domain_pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
        
        # 也接受不带顶级域名的主机名
        hostname_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$'
        
        return bool(re.match(domain_pattern, domain) or re.match(hostname_pattern, domain))
    
    @staticmethod
    def is_valid_host(host):
        """验证主机地址（IP或域名）
        
        Args:
            host: 主机地址字符串
            
        Returns:
            bool: 是否为有效的主机地址
        """
        return InputValidator.is_valid_ip(host) or InputValidator.is_valid_domain(host)
    
    @staticmethod
    def is_valid_port(port):
        """验证端口号
        
        Args:
            port: 端口号（整数或字符串）
            
        Returns:
            bool: 是否为有效的端口号(1-65535)
        """
        try:
            port_num = int(port)
            return 1 <= port_num <= 65535
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def normalize_host(host):
        """规范化主机地址
        
        Args:
            host: 主机地址
            
        Returns:
            str: 规范化后的主机地址，如果无效则返回None
        """
        if not host:
            return None
        
        host = host.strip().lower()
        
        # 移除协议前缀
        if host.startswith('http://'):
            host = host[7:]
        elif host.startswith('https://'):
            host = host[8:]
        
        # 移除路径
        if '/' in host:
            host = host.split('/')[0]
        
        # 移除端口号
        if ':' in host and not InputValidator.is_valid_ip(host):
            host = host.split(':')[0]
        
        return host if InputValidator.is_valid_host(host) else None


class LoggerConfig:
    """日志配置类"""
    
    _logger = None
    
    @classmethod
    def setup_logger(cls, name='NetworkDiagnostic', log_dir='logs', level=logging.INFO):
        """配置日志系统
        
        Args:
            name: 日志名称
            log_dir: 日志目录
            level: 日志级别
            
        Returns:
            logging.Logger: 配置好的日志对象
        """
        if cls._logger is not None:
            return cls._logger
        
        # 创建日志目录
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 创建logger
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # 避免重复添加handler
        if logger.handlers:
            cls._logger = logger
            return cls._logger
        
        # 创建文件handler
        log_file = os.path.join(log_dir, f'{name}_{datetime.now().strftime("%Y%m%d")}.log')
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        
        # 创建控制台handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)  # 控制台只显示警告及以上
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加handler到logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        cls._logger = logger
        return cls._logger
    
    @classmethod
    def get_logger(cls):
        """获取logger实例"""
        if cls._logger is None:
            return cls.setup_logger()
        return cls._logger


class SocketManager:
    """Socket资源管理器 - 使用上下文管理器确保资源正确释放"""
    
    def __init__(self, family=socket.AF_INET, sock_type=socket.SOCK_STREAM, timeout=5):
        """初始化Socket管理器
        
        Args:
            family: socket类型（AF_INET或AF_INET6）
            sock_type: socket类型（SOCK_STREAM或SOCK_DGRAM）
            timeout: 超时时间（秒）
        """
        self.family = family
        self.sock_type = sock_type
        self.timeout = timeout
        self.sock = None
    
    def __enter__(self):
        """进入上下文，创建socket"""
        self.sock = socket.socket(self.family, self.sock_type)
        self.sock.settimeout(self.timeout)
        return self.sock
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文，确保socket被关闭"""
        if self.sock:
            try:
                self.sock.close()
            except Exception as e:
                logger = LoggerConfig.get_logger()
                logger.warning(f"关闭socket时出错: {e}")
        return False  # 不抑制异常


def safe_int_conversion(value, default=0, min_val=None, max_val=None):
    """安全的整数转换
    
    Args:
        value: 要转换的值
        default: 转换失败时的默认值
        min_val: 最小值限制
        max_val: 最大值限制
        
    Returns:
        int: 转换后的整数值
    """
    try:
        result = int(value)
        
        if min_val is not None and result < min_val:
            return default
        if max_val is not None and result > max_val:
            return default
        
        return result
    except (ValueError, TypeError):
        return default
