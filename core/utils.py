#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
工具函数模块 - 提供输入验证、日志配置等通用功能
"""

import re
import socket
import logging
import os
import math
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


# =====================================================
# WiFi 频率/信道转换工具 (v2.0新增)
# =====================================================

def channel_to_frequency(channel: int) -> int:
    """将WiFi信道号转换为频率(MHz)
    
    支持2.4GHz、5GHz和6GHz频段
    
    Args:
        channel: 信道号
        
    Returns:
        int: 频率(MHz)，无效信道返回0
        
    Examples:
        >>> channel_to_frequency(1)    # 2.4GHz
        2412
        >>> channel_to_frequency(36)   # 5GHz
        5180
        >>> channel_to_frequency(233)  # 6GHz (WiFi 6E)
        7115
    """
    # 确保channel是整数类型
    try:
        channel = int(channel)
    except (ValueError, TypeError):
        return 0
    
    # 2.4GHz频段 (信道1-13)
    if 1 <= channel <= 13:
        return 2412 + (channel - 1) * 5
    
    # 2.4GHz频段 (信道14，仅日本)
    elif channel == 14:
        return 2484
    
    # 5GHz频段 (信道32-173)
    elif 32 <= channel <= 173:
        return 5160 + (channel - 32) * 5
    
    # 6GHz频段 (信道1-233, WiFi 6E)
    elif 1 <= channel <= 233:
        # 6GHz使用不同的起始频率
        return 5955 + channel * 5
    
    return 0


def frequency_to_channel(frequency: int) -> int:
    """将频率(MHz)转换为WiFi信道号
    
    支持2.4GHz、5GHz和6GHz频段
    
    Args:
        frequency: 频率(MHz)
        
    Returns:
        int: 信道号，无效频率返回0
        
    Examples:
        >>> frequency_to_channel(2412)  # 2.4GHz
        1
        >>> frequency_to_channel(5180)  # 5GHz
        36
        >>> frequency_to_channel(5975)  # 6GHz (WiFi 6E)
        4
    """
    # 确保frequency是整数类型
    try:
        frequency = int(frequency)
    except (ValueError, TypeError):
        return 0
    
    # 2.4GHz频段 (2412-2472 MHz)
    if 2412 <= frequency <= 2472:
        return (frequency - 2412) // 5 + 1
    
    # 2.4GHz频段 (信道14)
    elif frequency == 2484:
        return 14
    
    # 5GHz频段 (5160-5865 MHz)
    elif 5160 <= frequency <= 5865:
        return (frequency - 5160) // 5 + 32
    
    # 6GHz频段 (5955-7115 MHz, WiFi 6E)
    elif 5955 <= frequency <= 7115:
        return (frequency - 5955) // 5
    
    return 0


def get_frequency_band(channel: int = None, frequency: int = None) -> str:
    """获取频段标识
    
    可以通过信道号或频率获取频段
    
    Args:
        channel: 信道号（可选）
        frequency: 频率MHz（可选）
        
    Returns:
        str: '2.4GHz', '5GHz', '6GHz' 或 'Unknown'
        
    Examples:
        >>> get_frequency_band(channel=6)
        '2.4GHz'
        >>> get_frequency_band(frequency=5180)
        '5GHz'
        >>> get_frequency_band(channel=100)
        '6GHz'
    """
    # 优先使用频率判断
    if frequency:
        if 2400 <= frequency <= 2500:
            return '2.4GHz'
        elif 5000 <= frequency <= 5900:
            return '5GHz'
        elif 5900 <= frequency <= 7200:
            return '6GHz'
    
    # 使用信道判断
    elif channel:
        if 1 <= channel <= 14:
            return '2.4GHz'
        elif 32 <= channel <= 173:
            return '5GHz'
        elif channel > 173:
            return '6GHz'
    
    return 'Unknown'


def percent_to_dbm(percent: int) -> int:
    """将信号百分比转换为dBm值
    
    使用分段线性转换算法
    
    Args:
        percent: 信号百分比 (0-100)
        
    Returns:
        int: 信号强度dBm值
        
    Examples:
        >>> percent_to_dbm(100)
        -30
        >>> percent_to_dbm(50)
        -60
        >>> percent_to_dbm(0)
        -100
    """
    if percent >= 80:
        return -30 - (100 - percent) * 2
    elif percent >= 60:
        return -50 - (80 - percent) * 1
    elif percent >= 40:
        return -60 - (60 - percent) * 1
    elif percent >= 20:
        return -70 - (40 - percent) * 1
    else:
        return -80 - (20 - percent) * 1


def dbm_to_percent(dbm: int) -> int:
    """将dBm值转换为信号百分比
    
    Args:
        dbm: 信号强度dBm值
        
    Returns:
        int: 信号百分比 (0-100)
        
    Examples:
        >>> dbm_to_percent(-30)
        100
        >>> dbm_to_percent(-60)
        50
        >>> dbm_to_percent(-90)
        0
    """
    if dbm >= -30:
        return 100
    elif dbm >= -50:
        return 80 + (dbm + 50) // 1
    elif dbm >= -60:
        return 60 + (dbm + 60) // 1
    elif dbm >= -70:
        return 40 + (dbm + 70) // 1
    elif dbm >= -80:
        return 20 + (dbm + 80) // 1
    else:
        return max(0, 20 + (dbm + 80) // 1)


def get_signal_quality(signal_dbm):
    """
    根据信号强度(dBm)获取信号质量评级
    
    Args:
        signal_dbm: 信号强度（dBm），如 -45, -60, -80
    
    Returns:
        str: 质量评级 ('excellent'|'good'|'fair'|'poor'|'very_poor')
    
    Examples:
        >>> get_signal_quality(-40)
        'excellent'
        >>> get_signal_quality(-70)
        'fair'
    """
    if signal_dbm >= -50:
        return 'excellent'
    elif signal_dbm >= -60:
        return 'good'
    elif signal_dbm >= -70:
        return 'fair'
    elif signal_dbm >= -80:
        return 'poor'
    else:
        return 'very_poor'


def format_mac_address(mac, separator=':'):
    """
    格式化MAC地址
    
    Args:
        mac: MAC地址字符串（可能是各种格式）
        separator: 分隔符 (':' 或 '-')
    
    Returns:
        str: 格式化后的MAC地址
    
    Examples:
        >>> format_mac_address('aabbccddeeff', ':')
        'AA:BB:CC:DD:EE:FF'
        >>> format_mac_address('AA-BB-CC-DD-EE-FF', ':')
        'AA:BB:CC:DD:EE:FF'
    """
    # 移除所有分隔符
    mac_clean = re.sub(r'[:-]', '', mac.upper())
    
    # 验证长度
    if len(mac_clean) != 12:
        return mac
    
    # 每两个字符添加分隔符
    return separator.join(mac_clean[i:i+2] for i in range(0, 12, 2))


def validate_mac_address(mac):
    """
    验证MAC地址格式
    
    Args:
        mac: MAC地址字符串
    
    Returns:
        bool: 是否有效
    
    Examples:
        >>> validate_mac_address('AA:BB:CC:DD:EE:FF')
        True
        >>> validate_mac_address('invalid')
        False
    """
    # 移除分隔符
    mac_clean = re.sub(r'[:-]', '', mac)
    
    # 检查是否为12位十六进制
    if len(mac_clean) != 12:
        return False
    
    try:
        int(mac_clean, 16)
        return True
    except ValueError:
        return False


def is_dfs_channel(channel):
    """
    检查是否为DFS信道（动态频率选择）
    
    Args:
        channel: 信道号
    
    Returns:
        bool: 是否为DFS信道
    
    Examples:
        >>> is_dfs_channel(52)
        True
        >>> is_dfs_channel(36)
        False
    """
    # 5GHz DFS信道范围
    dfs_channels = list(range(52, 65)) + list(range(100, 145))
    return channel in dfs_channels


def calculate_distance_from_rssi(rssi, frequency=2.4, n=2.0):
    """
    根据RSSI计算大致距离
    
    Args:
        rssi: 接收信号强度指示（dBm）
        frequency: 频率（GHz）, 默认2.4GHz
        n: 路径损耗指数，默认2.0（自由空间）
    
    Returns:
        float: 估算距离（米）
    
    Examples:
        >>> calculate_distance_from_rssi(-50, 2.4)
        3.16
    """
    # 自由空间路径损耗公式
    # FSPL = 20*log10(d) + 20*log10(f) + 32.44
    # d = 10^((FSPL - 20*log10(f) - 32.44) / 20)
    
    # 1米处的参考RSSI（经验值）
    rssi_at_1m = -30 if frequency < 3 else -40
    
    # 路径损耗模型: RSSI = RSSI_1m - 10*n*log10(d)
    # d = 10^((RSSI_1m - RSSI) / (10*n))
    
    distance = 10 ** ((rssi_at_1m - rssi) / (10 * n))
    return round(distance, 2)


def format_bytes(bytes_value, precision=2):
    """
    格式化字节大小为人类可读格式
    
    Args:
        bytes_value: 字节数
        precision: 小数精度
    
    Returns:
        str: 格式化后的字符串
    
    Examples:
        >>> format_bytes(1024)
        '1.00 KB'
        >>> format_bytes(1048576)
        '1.00 MB'
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.{precision}f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.{precision}f} PB"
