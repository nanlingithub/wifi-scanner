#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WiFi分析模块 - 用于分析WiFi信号强度、网络质量等信息
"""

import subprocess
import platform
import re
import time
import threading
from core.connectivity import ConnectivityDiagnostic
from core.utils import LoggerConfig
from core.wifi_vendor_detector import WiFiVendorDetector

# Windows下隐藏cmd窗口
if platform.system().lower() == "windows":
    CREATE_NO_WINDOW = 0x08000000
else:
    CREATE_NO_WINDOW = 0

# 编码常量
ENCODING_GBK = 'gbk'
ENCODING_UTF8 = 'utf-8'

# 超时常量
DEFAULT_TIMEOUT = 10
INTERFACE_TIMEOUT = 5
QUICK_SCAN_TIMEOUT = 8
STANDARD_SCAN_TIMEOUT = 15

# 缓存常量
DEFAULT_CACHE_TIMEOUT = 2.0
MAX_HISTORY_POINTS = 100


class WiFiAnalyzer:
    """WiFi分析类 - 增强版（支持主流网卡厂商）"""
    
    # 主流网卡厂商OUI前缀（MAC地址前3字节）
    VENDOR_OUI = {
        'Intel': ['00:13:E8', '00:1E:64', '00:21:6A', '00:22:FB', '00:24:D7', 
                  'A0:88:B4', 'AC:72:89', 'D0:DF:9A', 'E4:02:9B', 'F0:D5:BF'],
        'Qualcomm': ['00:03:7F', '00:0A:F5', '00:26:08', '04:F0:21', '98:FA:E3'],
        'Broadcom': ['00:10:18', '00:14:A5', '00:17:C2', '00:90:4C', 'B4:F0:AB'],
        'Realtek': ['00:E0:4C', '00:E0:92', '18:4F:32', '50:3E:AA', 'E8:4E:06'],
        'MediaTek': ['00:0C:43', '58:D5:6E', '7C:10:C9', 'FC:34:97'],
        'Marvell': ['00:50:43', '00:11:88', '88:32:9B'],
        'Ralink': ['00:0C:43', '00:0E:2E', '08:86:3B'],
    }
    
    def __init__(self):
        self.system = platform.system().lower()
        self.connectivity_diag = ConnectivityDiagnostic()
        self.is_scanning = False
        self.scan_results = []
        self.logger = LoggerConfig.get_logger()
        
        # 网卡识别与适配
        self.adapter_vendor = None
        self.adapter_model = None
        self.adapter_capabilities = {}
        self._detect_adapter_info()
        
        # 性能优化：缓存机制
        self._cache_enabled = True
        self._cache_timeout = 2.0  # 缓存2秒
        self._last_scan_time = 0
        self._cached_networks = []
        self._scan_lock = threading.Lock()  # 线程安全
        
        # 快速模式：减少超时时间（启动时快速扫描）
        self._quick_mode = True
        self._scan_timeout = 5 if self._quick_mode else 15  # 从8秒减少到5秒
        
        # 稳定性增强：重试机制（减少重试次数以加快启动）
        self._max_retries = 2  # 从3次减少到2次
        self._retry_delay = 0.3  # 从0.5秒减少到0.3秒
        
        # MAC地址厂商数据库 - 主流WiFi设备厂商（400+条记录）
        self._oui_database = None  # 延迟初始化
        self.vendor_cache = {}  # 在线查询缓存
        
        # OUI查询LRU缓存 - 性能优化
        self._oui_lru_cache = {}
        self._oui_cache_max_size = 100  # 缓存最多100个最近查询
        self._oui_cache_order = []  # 用于LRU淘汰
    
    @property
    def oui_database(self):
        """OUI数据库属性 - 延迟加载"""
        if self._oui_database is None:
            self._oui_database = self._init_oui_database()
        return self._oui_database
    
    def _init_oui_database(self):
        """初始化OUI数据库 - 主流WiFi设备厂商"""
        return {
            # 华为 (Huawei) - 扩展到35条
            '00:1E:58': '华为', '0C:37:DC': '华为', '18:66:63': '华为',
            '28:6E:D4': '华为', '34:6B:D3': '华为', '4C:54:99': '华为',
            '58:2A:F7': '华为', '68:3E:34': '华为', '84:A8:E4': '华为',
            'D0:7A:B5': '华为', '9C:28:EF': '华为', '00:25:9E': '华为',
            '00:46:4B': '华为', '00:66:4B': '华为', '00:E0:FC': '华为',
            '18:4F:32': '华为', 'AC:85:3D': '华为', 'B0:91:34': '华为',
            'C8:14:79': '华为', 'E0:19:1D': '华为',
            # 新增华为常见OUI - 15条
            '00:18:82': '华为', '00:25:68': '华为', '00:5A:13': '华为',
            '10:47:80': '华为', '14:75:90': '华为', '1C:1D:67': '华为',
            '24:69:68': '华为', '30:D1:7E': '华为', '38:BC:1A': '华为',
            '54:25:EA': '华为', '6C:E8:73': '华为', '70:F9:6D': '华为',
            'A4:C4:94': '华为', 'BC:25:E0': '华为', 'D4:6E:0E': '华为',
            
            # 小米 (Xiaomi) - 扩展到35条
            '0C:72:2C': '小米', '14:F6:5A': '小米', '18:59:36': '小米',
            '28:6C:07': '小米', '34:80:B3': '小米', '3C:BD:3E': '小米',
            '64:09:80': '小米', '68:DF:DD': '小米', '78:02:F8': '小米',
            '7C:1D:D9': '小米', '8C:BE:BE': '小米', '98:FA:E3': '小米',
            'A0:86:C6': '小米', 'F8:8F:CA': '小米', '04:CF:4B': '小米',
            '10:2A:B3': '小米', '34:CE:00': '小米', '58:44:98': '小米',
            '74:51:BA': '小米', '88:C3:97': '小米', 'D0:D8:79': '小米',
            'F0:B4:29': '小米', 'F4:8E:92': '小米', '00:9E:C8': '小米',
            # 新增小米常见OUI - 11条
            '08:EB:ED': '小米', '40:31:3C': '小米', '50:64:2B': '小米',
            '54:83:3A': '小米', '74:23:44': '小米', '78:11:DC': '小米',
            '90:17:AC': '小米', 'C4:0B:CB': '小米', 'D0:AB:D5': '小米',
            'E0:B9:4D': '小米', 'F4:F5:DB': '小米',
            
            # TP-Link - 扩展到30条
            '14:CF:92': 'TP-Link', '18:A6:F7': 'TP-Link', '1C:3B:F3': 'TP-Link',
            '50:C7:BF': 'TP-Link', '54:A7:03': 'TP-Link', '60:32:B1': 'TP-Link',
            '98:DE:D0': 'TP-Link', 'A0:F3:C1': 'TP-Link', 'C0:4A:00': 'TP-Link',
            'D8:07:B6': 'TP-Link', 'E8:48:B8': 'TP-Link', 'EC:08:6B': 'TP-Link',
            '00:27:19': 'TP-Link', 'B0:48:7A': 'TP-Link', 'C4:6E:1F': 'TP-Link',
            '4C:ED:FB': 'TP-Link', '64:70:02': 'TP-Link', '90:F6:52': 'TP-Link',
            'AC:84:C6': 'TP-Link', 'E4:95:6E': 'TP-Link',
            # 新增TP-Link常见OUI - 10条
            '08:57:00': 'TP-Link', '0C:80:63': 'TP-Link', '1C:61:B4': 'TP-Link',
            '3C:84:6A': 'TP-Link', '50:3A:A0': 'TP-Link', '74:DA:38': 'TP-Link',
            '84:16:F9': 'TP-Link', '98:48:27': 'TP-Link', 'A8:40:41': 'TP-Link',
            'F4:EC:38': 'TP-Link',
            
            # 新华三(H3C) - 合并华三和新华三，统一命名为新华三(H3C) - 共36条
            '00:1E:0B': '新华三(H3C)', '24:0B:0A': '新华三(H3C)', '38:22:D6': '新华三(H3C)',
            '6C:92:BF': '新华三(H3C)', '70:7B:E8': '新华三(H3C)', '88:3F:4A': '新华三(H3C)',
            'D4:6D:6D': '新华三(H3C)', '00:01:7A': '新华三(H3C)', '00:25:B3': '新华三(H3C)',
            '3C:DF:A9': '新华三(H3C)', '58:69:6C': '新华三(H3C)', '84:B5:9C': '新华三(H3C)',
            'B8:AF:67': '新华三(H3C)', '00:19:E0': '新华三(H3C)', '00:1F:C6': '新华三(H3C)',
            '24:29:3E': '新华三(H3C)', 'A0:48:1C': '新华三(H3C)',
            '00:24:A1': '新华三(H3C)', '00:E0:FC': '新华三(H3C)', '18:03:73': '新华三(H3C)',
            '54:89:98': '新华三(H3C)', '68:BD:AB': '新华三(H3C)', '78:CD:8E': '新华三(H3C)',
            '98:03:D8': '新华三(H3C)', 'A4:4C:11': '新华三(H3C)', 'AC:E2:D3': '新华三(H3C)',
            'C8:7F:54': '新华三(H3C)', 'CC:3E:5F': '新华三(H3C)', 'E4:AF:A1': '新华三(H3C)',
            'F0:7D:68': '新华三(H3C)',
            'F4:03:21': '新华三(H3C)', '00:23:89': '新华三(H3C)',
            '00:25:84': '新华三(H3C)', '34:96:72': '新华三(H3C)', '54:E0:19': '新华三(H3C)',
            '88:1D:FC': '新华三(H3C)', '9C:8E:CD': '新华三(H3C)', 'F8:0B:CB': '新华三(H3C)',
            
            # Aruba (企业级无线AP) - 扩展到40条（从华三/新华三修正过来3条）
            '00:0B:86': 'Aruba', '20:4C:03': 'Aruba', '6C:F3:7F': 'Aruba',
            '94:B4:0F': 'Aruba', 'D8:C7:C8': 'Aruba', '00:1A:1E': 'Aruba',
            '24:DE:C6': 'Aruba', '70:3A:0E': 'Aruba', '9C:1C:12': 'Aruba',
            'D4:8C:B5': 'Aruba',
            # 以下3条从华三/新华三修正过来
            '38:17:C3': 'Aruba', '48:B4:C3': 'Aruba', '7C:57:3C': 'Aruba',
            # 新增Aruba常见OUI - 27条
            '00:24:6C': 'Aruba', '04:BD:88': 'Aruba', '0C:85:25': 'Aruba',
            '18:64:72': 'Aruba', '24:F2:7F': 'Aruba', '40:E3:D6': 'Aruba',
            '6C:C7:EC': 'Aruba', '84:D4:7E': 'Aruba', '90:48:9A': 'Aruba',
            'A0:5C:36': 'Aruba', 'B4:5D:50': 'Aruba', 'C4:65:16': 'Aruba',
            'D8:76:8F': 'Aruba', 'E0:5F:B9': 'Aruba', 'F0:61:C8': 'Aruba',
            '00:1A:6B': 'Aruba', '20:4C:9E': 'Aruba', '6C:8B:2F': 'Aruba',
            '88:DC:96': 'Aruba', 'AC:A3:1E': 'Aruba', 'BC:9F:E4': 'Aruba',
            'D0:81:7A': 'Aruba', 'E8:ED:F3': 'Aruba', 'F4:DB:E6': 'Aruba',
            '0C:F4:D5': 'Aruba', '8C:0C:90': 'Aruba', 'A8:BD:27': 'Aruba',
            
            # 锐捷 (Ruijie) - 扩展到25条
            '00:1D:23': '锐捷', '2C:D0:2D': '锐捷', '54:E6:FC': '锐捷',
            'B0:D5:9D': '锐捷', 'D0:C2:82': '锐捷', 'F0:B4:D2': '锐捷',
            '00:24:81': '锐捷', '1C:8E:5C': '锐捷', '94:A9:A8': '锐捷',
            'C8:9C:1D': '锐捷', '00:74:9C': '锐捷', '18:AD:C2': '锐捷',
            '20:76:93': '锐捷', '4C:1F:CC': '锐捷', 'D4:6A:A8': '锐捷',
            # 新增Ruijie常见OUI - 10条
            '08:9E:08': '锐捷', '0C:82:68': '锐捷', '1C:6F:65': '锐捷',
            '24:3F:DB': '锐捷', '60:38:E0': '锐捷', '68:ED:A4': '锐捷',
            '88:25:93': '锐捷', 'A4:56:30': '锐捷', 'CC:D3:1E': '锐捷',
            'E0:05:C5': '锐捷',
            
            # OPPO - 扩展到10条
            '00:0E:C6': 'OPPO', '3C:A9:F4': 'OPPO', '78:C5:E5': 'OPPO',
            'A4:50:46': 'OPPO', 'C4:07:2F': 'OPPO', 'FC:83:C6': 'OPPO',
            '08:00:28': 'OPPO', '2C:AB:25': 'OPPO', '74:23:44': 'OPPO',
            'D0:C5:D3': 'OPPO',
            
            # vivo - 8条
            '28:C6:3F': 'vivo', '44:00:10': 'vivo', '5C:0A:5B': 'vivo',
            '68:DF:DD': 'vivo', '98:90:65': 'vivo', 'B4:EF:39': 'vivo',
            'E8:9F:80': 'vivo', 'F4:7B:5E': 'vivo',
            
            # OnePlus（一加） - 6条
            '08:EA:40': 'OnePlus', '5C:C6:D4': 'OnePlus', 'A0:8E:78': 'OnePlus',
            'AC:37:43': 'OnePlus', 'E8:B2:AC': 'OnePlus', '94:65:2D': 'OnePlus',
            
            # 荣耀 (Honor) - 6条
            '00:5A:13': '荣耀', '34:2E:B6': '荣耀', '50:8F:4C': '荣耀',
            '9C:28:EF': '荣耀', 'C0:9F:05': '荣耀', 'E4:12:1D': '荣耀',
            
            # 中兴 (ZTE) - 扩展到12条
            '00:19:CB': '中兴', '08:6A:0A': '中兴', '38:83:45': '中兴',
            '48:7D:2E': '中兴', '68:DB:F5': '中兴', '84:B8:02': '中兴',
            'CC:B1:1A': '中兴', 'E8:65:49': '中兴', '70:79:B3': '中兴',
            '00:1E:3A': '中兴', '54:92:BE': '中兴', 'AC:5A:EE': '中兴',
            
            # Apple - 扩展到15条
            '00:03:93': 'Apple', '00:1F:5B': 'Apple', '00:23:DF': 'Apple',
            '04:26:65': 'Apple', '28:E1:4C': 'Apple', '3C:2E:FF': 'Apple',
            '68:9C:70': 'Apple', '98:F0:AB': 'Apple', 'AC:BC:32': 'Apple',
            'F4:37:B7': 'Apple', 'A8:86:DD': 'Apple', 'BC:52:B7': 'Apple',
            'E0:C7:67': 'Apple', 'F0:98:9D': 'Apple', '5C:95:AE': 'Apple',
            
            # Cisco (企业级网络设备) - 扩展到30条
            '00:0B:45': 'Cisco', '00:17:DF': 'Cisco', '00:1C:58': 'Cisco',
            '00:21:55': 'Cisco', '20:AA:4B': 'Cisco', '58:97:BD': 'Cisco',
            '6C:50:4D': 'Cisco', 'F8:66:F2': 'Cisco', '00:09:43': 'Cisco',
            '00:40:96': 'Cisco', '68:BC:0C': 'Cisco', '88:F0:31': 'Cisco',
            'B0:AA:77': 'Cisco', 'E4:AA:5D': 'Cisco', 'F0:25:72': 'Cisco',
            # 新增Cisco常见OUI - 15条
            '00:01:42': 'Cisco', '00:01:63': 'Cisco', '00:01:64': 'Cisco',
            '00:01:96': 'Cisco', '00:01:C7': 'Cisco', '00:02:16': 'Cisco',
            '00:02:17': 'Cisco', '00:02:3D': 'Cisco', '00:02:4A': 'Cisco',
            '00:02:4B': 'Cisco', '00:02:7D': 'Cisco', '00:02:7E': 'Cisco',
            '00:02:B9': 'Cisco', '00:02:BA': 'Cisco', '00:02:FC': 'Cisco',
            
            # D-Link - 扩展到10条
            '00:05:5D': 'D-Link', '00:17:9A': 'D-Link', '1C:7E:E5': 'D-Link',
            '28:10:7B': 'D-Link', 'C8:BE:19': 'D-Link', 'F0:7D:68': 'D-Link',
            '14:D6:4D': 'D-Link', '5C:F9:DD': 'D-Link', '90:94:E4': 'D-Link',
            'B8:A3:86': 'D-Link',
            
            # Netgear - 扩展到8条
            '00:09:5B': 'Netgear', '00:14:6C': 'Netgear', '20:E5:2A': 'Netgear',
            '84:1B:5E': 'Netgear', 'A0:63:91': 'Netgear', '2C:30:33': 'Netgear',
            '44:94:FC': 'Netgear', '9C:D3:6D': 'Netgear',
            
            # ASUS (华硕) - 扩展到10条
            '00:1E:8C': '华硕', '04:D4:C4': '华硕', '08:60:6E': '华硕',
            '2C:56:DC': '华硕', '70:4D:7B': '华硕', 'AC:9E:17': '华硕',
            '1C:87:2C': '华硕', '38:D5:47': '华硕', '50:46:5D': '华硕',
            'F8:32:E4': '华硕',
            
            # Samsung (三星) - 扩展到12条
            '00:12:FB': '三星', '00:1A:8A': '三星', '34:23:BA': '三星',
            '38:AA:3C': '三星', 'A0:0B:BA': '三星', 'B8:5E:7B': '三星',
            'CC:07:AB': '三星', 'F4:7B:5E': '三星', 'E8:50:8B': '三星',
            '08:D4:2B': '三星', '44:4E:6D': '三星', 'D0:17:C2': '三星',
            
            # 腾达 (Tenda) - 扩展到6条
            'C8:3A:35': '腾达', 'E8:61:1F': '腾达', 'FC:E7:57': '腾达',
            '08:10:76': '腾达', '00:B0:0C': '腾达', 'D8:15:0D': '腾达',
            
            # 水星 (Mercury) - 扩展到5条
            '00:B0:0C': '水星', 'D4:6E:5C': '水星', 'DC:D3:A2': '水星',
            '98:2C:BC': '水星', 'A4:2B:B0': '水星',
            
            # 迅捷 (Fast) - 扩展到5条
            '00:90:F7': '迅捷', 'E4:D3:32': '迅捷', 'FC:D7:33': '迅捷',
            '00:46:9A': '迅捷', '98:25:4A': '迅捷',
            
            # Ubiquiti - 扩展到8条
            '00:15:6D': 'Ubiquiti', '04:18:D6': 'Ubiquiti', 
            '68:72:51': 'Ubiquiti', 'F0:9F:C2': 'Ubiquiti',
            '24:A4:3C': 'Ubiquiti', '74:83:C2': 'Ubiquiti',
            'B4:FB:E4': 'Ubiquiti', 'DC:9F:DB': 'Ubiquiti',
            
            # Fortinet (企业防火墙/UTM) - 8条
            '00:09:0F': 'Fortinet', '08:5B:0E': 'Fortinet', '0C:F0:4E': 'Fortinet',
            '70:4C:A5': 'Fortinet', '90:6C:AC': 'Fortinet', 'A8:5B:78': 'Fortinet',
            'F0:1C:2D': 'Fortinet', 'F8:0B:BE': 'Fortinet',
            
            # Juniper Networks (企业级交换机/路由器) - 8条
            '00:05:85': 'Juniper', '00:10:DB': 'Juniper', '00:12:1E': 'Juniper',
            '00:19:E2': 'Juniper', '00:1F:12': 'Juniper', '2C:6B:F5': 'Juniper',
            '40:B4:F0': 'Juniper', '84:18:88': 'Juniper',
            
            # 深信服 (Sangfor) - 企业安全设备 - 6条
            '00:1C:BF': '深信服', '70:7B:E8': '深信服', '88:25:2C': '深信服',
            'D0:67:26': '深信服', 'E0:05:C5': '深信服', 'F4:8C:50': '深信服',
            
            # Google - 扩展到5条
            '3C:5A:B4': 'Google', '68:C6:3A': 'Google', 'F4:F5:D8': 'Google',
            '6C:AD:F8': 'Google', 'A4:77:33': 'Google',
            
            # Amazon - 扩展到4条
            '74:75:48': 'Amazon', 'F0:27:2D': 'Amazon', '00:FC:8B': 'Amazon',
            '44:65:0D': 'Amazon',
            
            # Motorola - 5条
            '00:26:BA': 'Motorola', '00:90:9C': 'Motorola', '38:CA:DA': 'Motorola',
            'A4:C0:E1': 'Motorola', 'D4:01:C3': 'Motorola',
            
            # LG - 5条
            '00:1C:62': 'LG', '10:68:3F': 'LG', '64:BC:0C': 'LG',
            'A0:39:F7': 'LG', 'E8:5B:5B': 'LG',
            
            # Sony - 4条
            '00:0A:D9': 'Sony', '00:1D:BA': 'Sony', '54:42:49': 'Sony',
            'FC:0F:E6': 'Sony',
            
            # Lenovo - 5条
            '00:21:CC': 'Lenovo', '54:EE:75': 'Lenovo', '68:F7:28': 'Lenovo',
            'DC:41:A9': 'Lenovo', 'E4:70:B8': 'Lenovo',
            
            # HP - 5条
            '00:17:08': 'HP', '00:1F:29': 'HP', '70:5A:0F': 'HP',
            'B4:39:D6': 'HP', 'EC:9A:74': 'HP',
            
            # Intel (WiFi芯片/网卡) - 扩展到15条，包含WiFi 6/6E AX系列
            '00:13:E8': 'Intel', '00:1E:64': 'Intel', '00:21:6A': 'Intel',
            '00:24:D7': 'Intel', 'A0:88:B4': 'Intel', 'AC:72:89': 'Intel',
            'D0:DF:9A': 'Intel', 'E4:02:9B': 'Intel', 'F0:D5:BF': 'Intel',
            '7C:7A:91': 'Intel',
            # WiFi 6/6E AX系列新增OUI - 5条
            '48:2A:E3': 'Intel', '5C:80:B6': 'Intel', '70:C9:4E': 'Intel',
            '88:D2:74': 'Intel', 'E0:2E:0B': 'Intel',
            
            # Murata (村田制作所) - WiFi模块厂商 - 8条
            '64:05:E9': 'Murata', '00:37:6D': 'Murata', '58:7F:66': 'Murata',
            '00:1F:1F': 'Murata', '00:26:E8': 'Murata', '10:BF:48': 'Murata',
            '34:13:E8': 'Murata', '40:4E:36': 'Murata',
            
            # Espressif (乐鑫) - IoT WiFi芯片 - 12条
            'DC:FE:18': 'Espressif', 'EC:62:60': 'Espressif', '24:0A:C4': 'Espressif',
            '30:AE:A4': 'Espressif', '84:F3:EB': 'Espressif', 'A4:CF:12': 'Espressif',
            'B4:E6:2D': 'Espressif', 'C8:C9:A3': 'Espressif', 'D8:BF:C0': 'Espressif',
            'E8:68:E7': 'Espressif', 'F0:08:D1': 'Espressif', 'CC:50:E3': 'Espressif',
            
            # Realtek (瑞昱) - WiFi芯片 - 15条
            'EC:6C:9F': 'Realtek', '00:E0:4C': 'Realtek', '00:E0:92': 'Realtek',
            '18:4F:32': 'Realtek', '50:3E:AA': 'Realtek', 'E8:4E:06': 'Realtek',
            '00:26:82': 'Realtek', '10:FE:ED': 'Realtek', '28:EE:52': 'Realtek',
            '4C:11:AE': 'Realtek', '74:DA:88': 'Realtek', '94:E3:6D': 'Realtek',
            'B0:25:AA': 'Realtek', 'C8:02:8F': 'Realtek', 'E0:94:67': 'Realtek',
            
            # Ralink (雷凌科技) - WiFi芯片 - 8条
            'CC:08:FB': 'Ralink', '00:0C:43': 'Ralink', '00:0E:2E': 'Ralink',
            '08:86:3B': 'Ralink', '00:18:E7': 'Ralink', 'F8:1A:67': 'Ralink',
            '00:22:75': 'Ralink', '00:24:7F': 'Ralink',
            
            # Broadcom (博通) - WiFi芯片 - 20条
            'B8:D4:BC': 'Broadcom', '00:10:18': 'Broadcom', '00:14:A5': 'Broadcom',
            '00:17:C2': 'Broadcom', '00:90:4C': 'Broadcom', 'B4:F0:AB': 'Broadcom',
            '20:AA:4B': 'Broadcom', '58:B0:35': 'Broadcom', '64:A2:F9': 'Broadcom',
            '6C:40:08': 'Broadcom', '90:B1:1C': 'Broadcom', 'A8:9D:21': 'Broadcom',
            # 新增Broadcom常见OUI - 8条
            '00:0A:F7': 'Broadcom', '00:0F:66': 'Broadcom', '00:13:D4': 'Broadcom',
            '00:1A:2B': 'Broadcom', '28:C6:8E': 'Broadcom', 'B8:27:EB': 'Broadcom',
            'CC:61:E5': 'Broadcom', 'DC:A6:32': 'Broadcom',
            
            # Qualcomm (高通) - WiFi芯片 - 10条
            '00:03:7F': 'Qualcomm', '00:0A:F5': 'Qualcomm', '00:26:08': 'Qualcomm',
            '04:F0:21': 'Qualcomm', '98:FA:E3': 'Qualcomm', '00:1D:0F': 'Qualcomm',
            '5C:0A:5B': 'Qualcomm', '88:E3:AB': 'Qualcomm', 'C4:93:00': 'Qualcomm',
            'E0:55:3D': 'Qualcomm',
            
            # MediaTek (联发科) - WiFi芯片 - 8条
            '00:0C:43': 'MediaTek', '58:D5:6E': 'MediaTek', '7C:10:C9': 'MediaTek',
            'FC:34:97': 'MediaTek', '0C:9D:92': 'MediaTek', '34:97:F6': 'MediaTek',
            '48:E7:DA': 'MediaTek', '70:4F:57': 'MediaTek',
            
            # Marvell (美满电子) - WiFi芯片 - 6条
            '00:50:43': 'Marvell', '00:11:88': 'Marvell', '88:32:9B': 'Marvell',
            '00:1D:7E': 'Marvell', '00:50:BA': 'Marvell', '00:C0:EE': 'Marvell',
            
            # Sagemcom - 运营商设备 - 8条
            'B8:F8:83': 'Sagemcom', '00:1D:7E': 'Sagemcom', '00:1F:9F': 'Sagemcom',
            '00:1F:CD': 'Sagemcom', '0C:D2:92': 'Sagemcom', '44:23:7C': 'Sagemcom',
            '8C:97:EA': 'Sagemcom', 'F4:CA:E5': 'Sagemcom',
            
            # 随机MAC地址（LAA - Locally Administered Address）
            # 这些通常是移动设备使用的随机MAC地址，无法识别具体厂商
            # 特征：第二位是 2, 6, A, E (二进制第7位为1)
            # 例如: 0A:XX:XX, 16:XX:XX, E6:XX:XX 等
        }
    
    def _detect_wifi_protocol(self, channel, band, bandwidth=20):
        """根据信道、频段、带宽精确检测WiFi协议
        
        Args:
            channel: 信道号
            band: 频段 (2.4GHz/5GHz/6GHz)
            bandwidth: 信道宽度(MHz)
            
        Returns:
            str: WiFi协议版本
        """
        try:
            # 如果band为N/A，尝试从信道推断频段
            if band == 'N/A' or not band:
                if channel:
                    try:
                        ch = int(channel) if isinstance(channel, str) else channel
                        if ch <= 14:
                            band = '2.4GHz'
                        elif 36 <= ch <= 165:
                            band = '5GHz'
                        elif 1 <= ch <= 233 and ch % 4 in [1, 5, 9]:
                            band = '6GHz'
                    except:
                        # 无法推断频段，返回通用标准
                        return 'WiFi 4+ (802.11n/ac/ax)'
            
            # 6GHz频段：WiFi 6E或WiFi 7
            if band == '6GHz':
                if bandwidth >= 320:
                    return 'WiFi 7 (802.11be)'
                else:
                    return 'WiFi 6E (802.11ax)'
            
            # 5GHz频段：WiFi 4/5/6
            elif band == '5GHz':
                if bandwidth >= 160:
                    return 'WiFi 6 (802.11ax)'  # 160MHz主要是WiFi 6
                elif bandwidth >= 80:
                    return 'WiFi 5/6 (802.11ac/ax)'  # 80MHz可能是WiFi 5或6
                elif bandwidth >= 40:
                    return 'WiFi 4/5 (802.11n/ac)'  # 40MHz可能是WiFi 4或5
                else:
                    return 'WiFi 4+ (802.11n/ac/ax)'  # 20MHz各标准都支持
            
            # 2.4GHz频段：WiFi 4/6/7
            elif band == '2.4GHz':
                if bandwidth >= 40:
                    return 'WiFi 4+ (802.11n/ax/be)'  # 40MHz主要是WiFi 4及以上
                else:
                    return 'WiFi 4+ (802.11n/ax/be)'  # 20MHz各标准都支持
            
            # 如果仍无法确定，返回通用标准
            return 'WiFi 4+ (802.11n/ac/ax)'
        except Exception:
            return 'WiFi 4+ (802.11n/ac/ax)'
    
    def _get_vendor_from_mac(self, mac_address):
        """根据MAC地址查询厂商信息（优化版：LRU缓存 + 三级查询）
        
        Args:
            mac_address: MAC地址 (格式: XX:XX:XX:XX:XX:XX)
            
        Returns:
            str: 厂商名称，未找到返回'未知'
        """
        if not mac_address or mac_address == 'N/A':
            return '未知'
        
        try:
            # 检查是否为随机MAC地址（LAA - Locally Administered Address）
            # LAA的特征：第一字节的第二位（bit 1）为1
            # 在十六进制中，第二个字符为 2, 3, 6, 7, A, B, E, F
            first_byte = mac_address.upper().split(':')[0]
            if len(first_byte) == 2:
                second_char = first_byte[1]
                if second_char in ['2', '3', '6', '7', 'A', 'B', 'E', 'F']:
                    # 这是随机MAC地址，用于隐私保护
                    return '随机MAC'
            
            # 提取OUI（前3字节，转大写）
            oui = ':'.join(mac_address.upper().split(':')[:3])
            
            # Level 0: LRU缓存查询（最快，O(1)）
            if oui in self._oui_lru_cache:
                # 更新LRU顺序
                self._oui_cache_order.remove(oui)
                self._oui_cache_order.append(oui)
                return self._oui_lru_cache[oui]
            
            # Level 1: 本地数据库查询（快速，O(1)字典查询）
            vendor = self.oui_database.get(oui)
            if vendor:
                self._update_lru_cache(oui, vendor)
                return vendor
            
            # Level 2: 在线查询缓存
            if oui in self.vendor_cache:
                vendor = self.vendor_cache[oui]
                self._update_lru_cache(oui, vendor)
                return vendor
            
            # Level 3: 在线API查询（可选，默认不启用以提高速度）
            # 如果需要在线查询，取消下面的注释
            # vendor = self._query_vendor_online(mac_address)
            # if vendor != '未知':
            #     self.vendor_cache[oui] = vendor
            #     self._update_lru_cache(oui, vendor)
            #     return vendor
            
            # 未找到，缓存'未知'结果避免重复查询
            self._update_lru_cache(oui, '未知')
            return '未知'
            
        except Exception as e:
            self.logger.debug(f"厂商查询失败: {mac_address}, 错误: {e}")
            return '未知'
    
    def _update_lru_cache(self, oui, vendor):
        """更新LRU缓存
        
        Args:
            oui: MAC地址前缀
            vendor: 厂商名称
        """
        # 添加到LRU缓存
        if oui in self._oui_lru_cache:
            # 已存在，更新顺序
            self._oui_cache_order.remove(oui)
        else:
            # 新增，检查是否超过容量
            if len(self._oui_lru_cache) >= self._oui_cache_max_size:
                # 移除最少使用的项（队列头部）
                oldest_oui = self._oui_cache_order.pop(0)
                del self._oui_lru_cache[oldest_oui]
        
        # 添加到缓存和顺序列表
        self._oui_lru_cache[oui] = vendor
        self._oui_cache_order.append(oui)
    
    def _query_vendor_online(self, mac_address):
        """在线查询MAC地址厂商（使用macvendors.com API）
        
        Args:
            mac_address: MAC地址
            
        Returns:
            str: 厂商名称，失败返回'未知'
        """
        try:
            import urllib.request
            import urllib.error
            
            # 清理MAC地址格式
            mac_clean = mac_address.replace(':', '').replace('-', '').upper()
            
            # macvendors.com 免费API (每分钟2次请求限制)
            api_url = f'https://api.macvendors.com/{mac_clean}'
            
            req = urllib.request.Request(
                api_url,
                headers={'User-Agent': 'WiFi-Diagnostic-Tool/1.0'}
            )
            
            with urllib.request.urlopen(req, timeout=3) as response:
                vendor = response.read().decode('utf-8').strip()
                if vendor:
                    return vendor
                    
        except urllib.error.HTTPError as e:
            if e.code == 404:
                self.logger.debug(f"MAC地址未在数据库中: {mac_address}")
            else:
                self.logger.debug(f"在线查询失败 (HTTP {e.code}): {mac_address}")
        except Exception as e:
            self.logger.debug(f"在线查询异常: {mac_address}, {e}")
        
        return '未知'
    
    def _normalize_authentication(self, auth_string):
        """标准化认证方式字符串
        
        将netsh输出的中文认证方式标准化为统一格式,方便后续判断
        
        输入示例:
        - "WPA2 - 企业" -> "WPA2-Enterprise"
        - "WPA2 - 个人" -> "WPA2-Personal"
        - "WPA3 - 企业" -> "WPA3-Enterprise"
        - "开放式" -> "Open"
        
        Args:
            auth_string: 原始认证方式字符串
            
        Returns:
            标准化后的认证方式字符串
        """
        if not auth_string or auth_string == '未知' or auth_string == 'N/A':
            return '未知'
        
        auth = auth_string.strip()
        
        # WPA2/WPA3 企业认证
        if '企业' in auth or 'Enterprise' in auth or '802.1X' in auth:
            if 'WPA3' in auth:
                return 'WPA3-Enterprise'
            elif 'WPA2' in auth:
                return 'WPA2-Enterprise'
            elif 'WPA' in auth:
                return 'WPA-Enterprise'
            else:
                return f'{auth} (企业级)'
        
        # WPA2/WPA3 个人认证
        elif '个人' in auth or 'Personal' in auth or 'PSK' in auth:
            if 'WPA3' in auth:
                return 'WPA3-Personal'
            elif 'WPA2' in auth:
                return 'WPA2-Personal'
            elif 'WPA' in auth:
                return 'WPA-Personal'
            else:
                return f'{auth} (个人)'
        
        # 开放式网络
        elif '开放' in auth or 'Open' in auth:
            return 'Open'
        
        # WEP
        elif 'WEP' in auth:
            return 'WEP'
        
        # 其他情况保持原样
        return auth
    
    def _detect_adapter_info(self):
        """检测无线网卡信息和厂商"""
        try:
            if self.system == "windows":
                # 获取网卡描述信息
                cmd = ["netsh", "wlan", "show", "interfaces"]
                result = subprocess.run(cmd, capture_output=True, timeout=5, creationflags=CREATE_NO_WINDOW)
                if result.returncode == 0:
                    try:
                        output = result.stdout.decode('gbk', errors='ignore')
                    except (UnicodeDecodeError, AttributeError):
                        output = result.stdout.decode('utf-8', errors='ignore')
                    
                    # 提取网卡描述
                    desc_match = re.search(r'(描述|Description)\s*[:：]\s*(.+)', output, re.IGNORECASE)
                    if desc_match:
                        desc = desc_match.group(2).strip()
                        self.adapter_model = desc
                        
                        # 识别厂商
                        desc_lower = desc.lower()
                        if 'intel' in desc_lower:
                            self.adapter_vendor = 'Intel'
                        elif 'qualcomm' in desc_lower or 'atheros' in desc_lower:
                            self.adapter_vendor = 'Qualcomm'
                        elif 'broadcom' in desc_lower:
                            self.adapter_vendor = 'Broadcom'
                        elif 'realtek' in desc_lower or 'rtl' in desc_lower:
                            self.adapter_vendor = 'Realtek'
                        elif 'mediatek' in desc_lower or 'mtk' in desc_lower:
                            self.adapter_vendor = 'MediaTek'
                        elif 'marvell' in desc_lower:
                            self.adapter_vendor = 'Marvell'
                        elif 'ralink' in desc_lower:
                            self.adapter_vendor = 'Ralink'
                        else:
                            self.adapter_vendor = 'Unknown'
                        
                        # 检测支持的WiFi标准
                        radio_match = re.search(r'(无线电类型|Radio type)\s*[:：]\s*(.+)', output)
                        if radio_match:
                            radio_type = radio_match.group(2).strip()
                            self.adapter_capabilities['radio_type'] = radio_type
                            
                            # 判断WiFi标准支持（从最新到最旧）
                            if '802.11be' in radio_type or 'Wi-Fi 7' in radio_type:
                                self.adapter_capabilities['wifi7'] = True
                                self.adapter_capabilities['wifi_standard'] = 'WiFi 7 (802.11be)'
                            elif '802.11ax' in radio_type or 'Wi-Fi 6E' in radio_type or 'Wi-Fi 6' in radio_type:
                                # 通过频段判断是WiFi 6还是WiFi 6E
                                if '6GHz' in radio_type or '6 GHz' in radio_type:
                                    self.adapter_capabilities['wifi6e'] = True
                                    self.adapter_capabilities['wifi_standard'] = 'WiFi 6E (802.11ax)'
                                else:
                                    self.adapter_capabilities['wifi6'] = True
                                    self.adapter_capabilities['wifi_standard'] = 'WiFi 6 (802.11ax)'
                            elif '802.11ac' in radio_type or 'Wi-Fi 5' in radio_type:
                                self.adapter_capabilities['wifi5'] = True
                                self.adapter_capabilities['wifi_standard'] = 'WiFi 5 (802.11ac)'
                            elif '802.11n' in radio_type or 'Wi-Fi 4' in radio_type:
                                self.adapter_capabilities['wifi4'] = True
                                self.adapter_capabilities['wifi_standard'] = 'WiFi 4 (802.11n)'
                            else:
                                self.adapter_capabilities['wifi_standard'] = radio_type
                        
                        self.logger.info(f"检测到网卡: {self.adapter_vendor} - {self.adapter_model}")
                        if self.adapter_capabilities:
                            self.logger.info(f"网卡能力: {self.adapter_capabilities}")
            
        except Exception as e:
            self.logger.warning(f"网卡信息检测失败: {e}")
            self.adapter_vendor = 'Unknown'
    
    def _get_optimized_scan_command(self):
        """根据网卡厂商返回优化的扫描命令
        
        Returns:
            list: 优化后的命令参数
        """
        if self.system == "windows":
            # 基础命令
            cmd = ["netsh", "wlan", "show", "networks", "mode=Bssid"]
            
            # 针对不同厂商的优化（如需要可添加特殊参数）
            # Intel网卡：通常工作良好，使用默认配置
            # Realtek网卡：某些型号扫描较慢，已在超时中考虑
            # Qualcomm/Broadcom：通常支持快速扫描
            
            # 特殊优化：Realtek网卡增加超时时间
            if self.adapter_vendor == 'Realtek' and self._scan_timeout < 10:
                self._scan_timeout = 10
                self.logger.info("Realtek网卡检测到，增加扫描超时时间")
            
            return cmd
        elif self.system == "linux":
            # Linux下根据网卡选择工具
            return ["iwlist", "scan"]
        else:
            # Mac系统
            return ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-s"]
    
    def get_adapter_info(self):
        """获取当前网卡信息
        
        Returns:
            dict: 网卡信息字典
        """
        info = {
            'vendor': self.adapter_vendor,
            'model': self.adapter_model,
            'capabilities': self.adapter_capabilities,
            'system': self.system
        }
        
        # 获取更详细的接口信息
        try:
            interfaces = self.get_wifi_interfaces()
            if interfaces and len(interfaces) > 0:
                # 使用第一个接口的信息
                iface = interfaces[0]
                if isinstance(iface, dict):
                    info['name'] = iface.get('name', 'WLAN')
                    info['description'] = iface.get('description', info['model'])
                    info['state'] = iface.get('state', '未知')
                    info['ssid'] = iface.get('ssid', '')
                    info['signal'] = iface.get('signal', '')
                    info['radio_type'] = iface.get('radio_type', '')
                    info['authentication'] = iface.get('authentication', '')
                    info['guid'] = iface.get('guid', '')
                    info['wifi_standard'] = iface.get('wifi_standard', '')
                    info['vendor_icon'] = iface.get('vendor_icon', '⚪')
                    info['max_speed'] = iface.get('max_speed', '')
        except Exception as e:
            # 如果获取失败，使用基本信息
            pass
        
        # 获取MAC地址和驱动版本
        if self.system == "windows":
            try:
                # 获取物理地址
                cmd = ["getmac", "/FO", "CSV", "/V"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5, creationflags=CREATE_NO_WINDOW)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'Wi-Fi' in line or 'WLAN' in line or '无线' in line:
                            # 提取MAC地址
                            mac_match = re.search(r'([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}', line)
                            if mac_match:
                                info['mac_address'] = mac_match.group(0)
                                break
                
                # 获取驱动版本（使用wmic）
                cmd = ["wmic", "nic", "where", "NetConnectionID='Wi-Fi'", "get", "DriverVersion", "/value"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5, creationflags=CREATE_NO_WINDOW)
                if result.returncode == 0:
                    version_match = re.search(r'DriverVersion=(.+)', result.stdout)
                    if version_match:
                        info['driver_version'] = version_match.group(1).strip()
            except Exception as e:
                pass
        
        return info
    
    def get_wifi_interfaces(self):
        """获取WiFi接口信息"""
        try:
            if self.system == "windows":
                # Windows系统获取WiFi接口信息
                cmd = ["netsh", "wlan", "show", "interfaces"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, creationflags=CREATE_NO_WINDOW)
                if result.returncode == 0:
                    output = result.stdout
                    interfaces = []
                    lines = output.split('\n')
                    current_interface = {}
                    
                    for line in lines:
                        line_stripped = line.strip()
                        
                        # 匹配名称行 - 精确匹配行首
                        if line_stripped.startswith("名称") or line_stripped.startswith("Name"):
                            if current_interface:  # 如果已有接口信息，先保存
                                interfaces.append(current_interface)
                                current_interface = {}
                            # 提取接口名称
                            name_match = re.search(r'[:：]\s*(.+)', line)
                            if name_match:
                                current_interface['name'] = name_match.group(1).strip()
                        # 匹配描述行
                        elif line_stripped.startswith("描述") or line_stripped.startswith("Description"):
                            desc_match = re.search(r'[:：]\s*(.+)', line)
                            if desc_match:
                                current_interface['description'] = desc_match.group(1).strip()
                        elif "GUID" in line:
                            guid_match = re.search(r'[:：]\s*(.+)', line)
                            if guid_match:
                                current_interface['guid'] = guid_match.group(1).strip()
                        # 匹配SSID行 - 使用startswith避免匹配BSSID
                        elif line_stripped.startswith("SSID"):
                            ssid_match = re.search(r'[:：]\s*(.+)', line)
                            if ssid_match:
                                ssid_value = ssid_match.group(1).strip()
                                if ssid_value:  # 只保存非空SSID
                                    current_interface['ssid'] = ssid_value
                        elif "信号" in line or "Signal" in line:
                            signal_match = re.search(r'[:：]\s*(\d+%)', line)
                            if signal_match:
                                current_interface['signal'] = signal_match.group(1).strip()
                        # 匹配状态行 - 更精确的匹配
                        elif line_stripped.startswith("状态") or line_stripped.startswith("State"):
                            state_match = re.search(r'[:：]\s*(.+)', line)
                            if state_match:
                                current_interface['state'] = state_match.group(1).strip()
                        elif "无线电类型" in line or "Radio type" in line:
                            radio_match = re.search(r'[:：]\s*(.+)', line)
                            if radio_match:
                                current_interface['radio_type'] = radio_match.group(1).strip()
                        elif "网络类型" in line or "Authentication" in line:
                            auth_match = re.search(r'[:：]\s*(.+)', line)
                            if auth_match:
                                raw_auth = auth_match.group(1).strip()
                                # 标准化认证方式
                                current_interface['authentication'] = self._normalize_authentication(raw_auth)
                        elif "连接模式" in line or "Connection mode" in line:
                            mode_match = re.search(r'[:：]\s*(.+)', line)
                            if mode_match:
                                current_interface['connection_mode'] = mode_match.group(1).strip()
                    
                    # 添加最后一个接口
                    if current_interface:
                        interfaces.append(current_interface)
                    
                    # 使用厂商检测器增强接口信息
                    for iface in interfaces:
                        # 添加厂商信息
                        if 'description' in iface:
                            vendor_info = WiFiVendorDetector.detect_vendor(iface['description'])
                            iface['vendor'] = vendor_info['vendor']
                            iface['vendor_icon'] = vendor_info['icon']
                            iface['vendor_type'] = vendor_info['type']
                            
                            # 添加WiFi标准信息
                            wifi_std = WiFiVendorDetector.detect_wifi_standard(iface['description'])
                            iface['wifi_standard'] = wifi_std['generation']
                            iface['max_speed'] = wifi_std['speed']
                        
                        # 生成友好的显示名称
                        iface['display_name'] = WiFiVendorDetector.get_enhanced_display(
                            name=iface.get('name', 'WLAN'),
                            description=iface.get('description', ''),
                            state=iface.get('state', ''),
                            ssid=iface.get('ssid', ''),
                            signal=iface.get('signal', '')
                        )
                    
                    return interfaces
            else:
                # Linux/Mac系统获取WiFi接口信息
                if self.system == "linux":
                    cmd = ["iwconfig"]
                else:  # Mac
                    cmd = ["networksetup", "-listallhardwareports"]  # Mac示例命令
                    
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, creationflags=CREATE_NO_WINDOW)
                if result.returncode == 0:
                    # 简化处理，实际实现可能需要更复杂的解析
                    return [{"interface": "wireless", "details": result.stdout[:500]}]  # 限制输出长度
                    
        except subprocess.TimeoutExpired:
            print("获取WiFi接口信息超时")
        except Exception as e:
            print(f"获取WiFi接口信息时出错: {e}")
        
        return []
    
    def scan_wifi_networks(self, force_refresh=False):
        """扫描周围的WiFi网络（带缓存优化和重试机制）
        
        Args:
            force_refresh: 强制刷新，忽略缓存
        """
        # 缓存检查
        current_time = time.time()
        if not force_refresh and self._cache_enabled:
            if current_time - self._last_scan_time < self._cache_timeout:
                return self._cached_networks.copy()
        
        # 线程安全：防止并发扫描
        if not self._scan_lock.acquire(blocking=False):
            # 如果正在扫描，返回缓存结果
            return self._cached_networks.copy()
        
        try:
            networks = []
            if self.system == "windows":
                # 带重试机制的扫描
                for retry in range(self._max_retries):
                    try:
                        # 针对不同厂商网卡优化命令
                        cmd = self._get_optimized_scan_command()
                        
                        # 执行扫描
                        result = subprocess.run(cmd, capture_output=True, timeout=self._scan_timeout, creationflags=CREATE_NO_WINDOW)
                        
                        if result.returncode == 0:
                            # 多编码尝试，Windows中文系统首选GBK
                            output = None
                            for encoding in ['gbk', 'gb2312', 'cp936', 'utf-8']:
                                try:
                                    output = result.stdout.decode(encoding)
                                    break
                                except (UnicodeDecodeError, AttributeError):
                                    continue
                            
                            if not output:
                                # 最后尝试GBK并忽略错误（而不是UTF-8）
                                output = result.stdout.decode('gbk', errors='ignore')
                            
                            networks = self._parse_windows_wifi_scan(output)
                            
                            # 成功则退出重试循环
                            if networks or retry == self._max_retries - 1:
                                break
                        else:
                            self.logger.warning(f"扫描返回错误码: {result.returncode}, 重试 {retry+1}/{self._max_retries}")
                    
                    except subprocess.TimeoutExpired:
                        self.logger.warning(f"扫描超时, 重试 {retry+1}/{self._max_retries}")
                        if retry < self._max_retries - 1:
                            time.sleep(self._retry_delay)
                    
                    except Exception as e:
                        self.logger.error(f"扫描异常: {e}, 重试 {retry+1}/{self._max_retries}")
                        if retry < self._max_retries - 1:
                            time.sleep(self._retry_delay)
                
                # 更新缓存
                if networks:
                    self._cached_networks = networks
                    self._last_scan_time = current_time
                    self.logger.info(f"扫描成功: 发现 {len(networks)} 个网络")
                return networks or self._cached_networks.copy()
            elif self.system == "linux":
                # Linux系统使用iwlist命令扫描WiFi网络
                # 首先获取无线接口名称
                interfaces_result = subprocess.run(["iwconfig"], capture_output=True, text=True, timeout=5, creationflags=CREATE_NO_WINDOW)
                wlan_interface = None
                if interfaces_result.stdout:
                    for line in interfaces_result.stdout.split('\n'):
                        if "IEEE 802.11" in line:
                            wlan_interface = line.split()[0]
                            break
                
                if wlan_interface:
                    cmd = ["iwlist", wlan_interface, "scan"]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=self._scan_timeout, creationflags=CREATE_NO_WINDOW)
                    if result.returncode == 0:
                        output = result.stdout
                        networks = self._parse_linux_wifi_scan(output)
                        # 更新缓存
                        self._cached_networks = networks
                        self._last_scan_time = current_time
                        return networks
            else:
                # Mac系统
                cmd = ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-s"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=self._scan_timeout, creationflags=CREATE_NO_WINDOW)
                if result.returncode == 0:
                    output = result.stdout
                    networks = self._parse_mac_wifi_scan(output)
                    # 更新缓存
                    self._cached_networks = networks
                    self._last_scan_time = current_time
                    return networks
                    
        except subprocess.TimeoutExpired:
            self.logger.warning("WiFi扫描超时，返回缓存结果")
            return self._cached_networks.copy()  # 超时返回缓存
        except Exception as e:
            self.logger.error(f"WiFi扫描时出错: {e}")
            return self._cached_networks.copy()  # 错误返回缓存
        finally:
            self._scan_lock.release()
        
        return self._cached_networks.copy()
    
    def _parse_windows_wifi_scan(self, output):
        """解析Windows系统的WiFi扫描结果 - 优化版"""
        networks = []
        if not output:
            return networks
        
        # 性能优化：预编译正则表达式（支持中文和各种字符）
        ssid_pattern = re.compile(r'SSID\s+\d+\s*[:：]\s*(.+?)\s*$', re.UNICODE)
        bssid_pattern = re.compile(r'BSSID\s+\d+\s*[:：]\s*([0-9A-Fa-f:-]+)')
        signal_pattern = re.compile(r'信号\s*[:：]\s*(\d+)\s*%')
        channel_pattern = re.compile(r'频道\s*[:：]\s*(\d+)')
        auth_pattern = re.compile(r'身份验证\s*[:：]\s*(.+?)\s*$', re.UNICODE)
        enc_pattern = re.compile(r'加密\s*[:：]\s*(.+?)\s*$', re.UNICODE)
            
        lines = output.split('\n')
        
        current_ssid = None
        current_network = {}
        current_bssid_info = {}
        
        for line in lines:
            line_stripped = line.strip()
            
            # 检测新的SSID（避免匹配到BSSID）
            if line_stripped.startswith("SSID") and (":" in line_stripped or "：" in line_stripped) and not line_stripped.startswith("BSSID"):
                # 保存上一个BSSID的信息
                if current_bssid_info and current_ssid:
                    signal = current_bssid_info.get('signal', '0%')
                    # 将signal从字符串转换为整数
                    signal_int = int(signal.rstrip('%')) if signal.endswith('%') else 0
                    bssid = current_bssid_info.get('bssid', 'N/A')
                    
                    # 根据频段和信道精确推断WiFi标准
                    band = current_bssid_info.get('band', 'N/A')
                    channel = current_bssid_info.get('channel', 0)
                    try:
                        channel_int = int(channel) if channel != 'N/A' else 0
                    except:
                        channel_int = 0
                    
                    # 使用精确检测函数
                    wifi_standard = self._detect_wifi_protocol(channel_int, band)
                    
                    networks.append({
                        'ssid': current_ssid,
                        'signal_strength': signal,
                        'signal_percent': signal_int,  # 修改：使用整数
                        'channel': current_bssid_info.get('channel', 'N/A'),
                        'encryption': current_network.get('encryption', 'N/A'),
                        'authentication': current_network.get('authentication', 'N/A'),
                        'bssid': bssid,
                        'band': current_bssid_info.get('band', 'N/A'),
                        'vendor': self._get_vendor_from_mac(bssid),  # 添加厂商信息
                        'wifi_standard': wifi_standard  # 新增：WiFi标准
                    })
                
                # 重置状态，开始新的SSID
                current_bssid_info = {}
                current_network = {}
                
                # 使用预编译的正则提取SSID
                ssid_match = ssid_pattern.search(line_stripped)
                if ssid_match:
                    current_ssid = ssid_match.group(1).strip()
                    # 清理SSID，确保中文字符正确显示
                    if current_ssid:
                        # 移除可能的零宽字符和控制字符
                        current_ssid = ''.join(c for c in current_ssid if c.isprintable() or ord(c) > 127)
                        current_ssid = current_ssid.strip()
            
            # SSID级别的属性（对所有BSSID通用） - 匹配4个空格开头的行
            elif "身份验证" in line_stripped or "Authentication" in line_stripped:
                auth_match = auth_pattern.search(line_stripped)
                if auth_match:
                    raw_auth = auth_match.group(1).strip()
                    # 标准化认证方式（支持中英文格式）
                    current_network['authentication'] = self._normalize_authentication(raw_auth)
            
            elif "加密" in line_stripped or "Encryption" in line_stripped:
                enc_match = enc_pattern.search(line_stripped)
                if enc_match:
                    current_network['encryption'] = enc_match.group(1).strip()
            
            # 检测新的BSSID
            elif line_stripped.startswith("BSSID"):
                # 保存上一个BSSID的信息
                if current_bssid_info and current_ssid:
                    signal = current_bssid_info.get('signal', '0%')
                    # 将signal从字符串转换为整数
                    signal_int = int(signal.rstrip('%')) if signal.endswith('%') else 0
                    bssid = current_bssid_info.get('bssid', 'N/A')
                    
                    # 根据频段和信道精确推断WiFi标准
                    band = current_bssid_info.get('band', 'N/A')
                    channel = current_bssid_info.get('channel', 0)
                    try:
                        channel_int = int(channel) if channel != 'N/A' else 0
                    except:
                        channel_int = 0
                    
                    # 使用精确检测函数
                    wifi_standard = self._detect_wifi_protocol(channel_int, band)
                    
                    networks.append({
                        'ssid': current_ssid,
                        'signal_strength': signal,
                        'signal_percent': signal_int,  # 修改：使用整数
                        'channel': current_bssid_info.get('channel', 'N/A'),
                        'encryption': current_network.get('encryption', 'N/A'),
                        'authentication': current_network.get('authentication', 'N/A'),
                        'bssid': bssid,
                        'band': current_bssid_info.get('band', 'N/A'),
                        'vendor': self._get_vendor_from_mac(bssid),  # 添加厂商信息
                        'wifi_standard': wifi_standard  # 新增：WiFi标准
                    })
                
                # 开始新的BSSID
                current_bssid_info = {}
                bssid_match = bssid_pattern.search(line_stripped)
                if bssid_match:
                    current_bssid_info['bssid'] = bssid_match.group(1).strip()
            
            # BSSID级别的属性 - 检查信号和频道（这些信息在BSSID之后，有更多缩进）
            elif "信号" in line_stripped or "Signal" in line_stripped:
                signal_match = signal_pattern.search(line_stripped)
                if signal_match:
                    current_bssid_info['signal'] = signal_match.group(1) + '%'
            
            elif "频道" in line_stripped or "Channel" in line_stripped:
                channel_match = channel_pattern.search(line_stripped)
                if channel_match:
                    channel = int(channel_match.group(1))
                    current_bssid_info['channel'] = str(channel)
                    # 快速判断频段（支持WiFi 6E/7的6GHz）
                    if channel <= 14:
                        current_bssid_info['band'] = '2.4GHz'
                    elif channel >= 36 and channel <= 165:
                        # 5GHz频段：36-165（间隔4）
                        current_bssid_info['band'] = '5GHz'
                    elif (channel >= 1 and channel <= 233 and channel % 4 in [1, 5, 9]):
                        # 6GHz频段：1,5,9...229,233（WiFi 6E/7）
                        current_bssid_info['band'] = '6GHz'
                    else:
                        current_bssid_info['band'] = 'N/A'
        
        # 保存最后一个网络
        if current_bssid_info and current_ssid:
            signal = current_bssid_info.get('signal', '0%')
            # 将signal从字符串转换为整数
            signal_int = int(signal.rstrip('%')) if signal.endswith('%') else 0
            bssid = current_bssid_info.get('bssid', 'N/A')
            
            # 根据频段和信道精确推断WiFi标准
            band = current_bssid_info.get('band', 'N/A')
            channel = current_bssid_info.get('channel', 0)
            try:
                channel_int = int(channel) if channel != 'N/A' else 0
            except:
                channel_int = 0
            
            # 使用精确检测函数
            wifi_standard = self._detect_wifi_protocol(channel_int, band)
            
            networks.append({
                'ssid': current_ssid,
                'signal_strength': signal,
                'signal_percent': signal_int,  # 修改：使用整数
                'channel': current_bssid_info.get('channel', 'N/A'),
                'encryption': current_network.get('encryption', 'N/A'),
                'authentication': current_network.get('authentication', 'N/A'),
                'bssid': bssid,
                'band': current_bssid_info.get('band', 'N/A'),
                'vendor': self._get_vendor_from_mac(bssid),  # 添加厂商信息
                'wifi_standard': wifi_standard  # 新增：WiFi标准
            })
        
        return networks
    
    def _parse_linux_wifi_scan(self, output):
        """解析Linux系统的WiFi扫描结果"""
        networks = []
        cells = re.split(r'Cell \d+ - ', output)
        
        for cell in cells[1:]:  # 跳过第一个空元素
            network = {}
            
            # 提取ESSID (SSID)
            ssid_match = re.search(r'ESSID:"([^"]+)"', cell)
            if ssid_match:
                network['ssid'] = ssid_match.group(1)
            
            # 提取信号强度
            signal_match = re.search(r'Quality=([^ ]+)', cell)
            if signal_match:
                quality = signal_match.group(1)
                network['signal_quality'] = quality
                
                # 提取信号强度dBm
                signal_dbm_match = re.search(r'Signal level=(-?\d+) dBm', cell)
                if signal_dbm_match:
                    network['signal_dbm'] = f"{signal_dbm_match.group(1)} dBm"
                    
                    # 计算百分比
                    signal_dbm = int(signal_dbm_match.group(1))
                    # dBm转百分比的近似公式
                    if signal_dbm >= -50:
                        percent = 100
                    elif signal_dbm <= -100:
                        percent = 0
                    else:
                        percent = 2 * (signal_dbm + 100)
                    network['signal_percent'] = max(0, min(100, int(percent)))
            
            # 提取MAC地址
            address_match = re.search(r'Address: ([0-9A-Fa-f:-]+)', cell)
            if address_match:
                network['bssid'] = address_match.group(1)
            
            # 提取频道
            channel_match = re.search(r'Channel:(\d+)', cell)
            if channel_match:
                network['channel'] = channel_match.group(1)
            
            # 提取加密方式
            enc_match = re.search(r'Encryption key:(.+)', cell)
            if enc_match:
                network['encryption'] = enc_match.group(1).strip()
            
            # 提取认证方式
            auth_match = re.search(r'IE: IEEE 802.11i/WPA2 Version 1', cell)
            if auth_match:
                network['authentication'] = "WPA2"
            elif re.search(r'IE: WPA Version 1', cell):
                network['authentication'] = "WPA"
            else:
                if re.search(r'Encryption key:on', cell):
                    network['authentication'] = "WEP"
                else:
                    network['authentication'] = "Open"
            
            if 'ssid' in network:  # 只添加包含SSID的网络
                # 添加厂商信息
                network['vendor'] = self._get_vendor_from_mac(network.get('bssid', 'N/A'))
                networks.append(network)
        
        return networks
    
    def _parse_mac_wifi_scan(self, output):
        """解析Mac系统的WiFi扫描结果"""
        networks = []
        lines = output.split('\n')
        
        for line in lines:
            if line.strip():
                parts = line.split()
                if len(parts) >= 2:
                    bssid = parts[0]
                    network = {
                        'ssid': ' '.join(parts[1:]),  # SSID可能包含空格
                        'bssid': bssid,  # MAC地址
                        'signal_dbm': "未知",  # Mac的airport命令不直接提供信号强度
                        'signal_percent': 0,  # 默认0而非"未知"
                        'channel': "未知",
                        'authentication': "未知",
                        'vendor': self._get_vendor_from_mac(bssid)  # 添加厂商信息
                    }
                    networks.append(network)
        
        return networks
    
    def get_current_wifi_info(self):
        """获取当前连接的WiFi信息（包含适配器详情）"""
        try:
            if self.system == "windows":
                # 获取当前连接的WiFi详细信息
                cmd = ["netsh", "wlan", "show", "interfaces"]
                result = subprocess.run(cmd, capture_output=True, timeout=10, creationflags=CREATE_NO_WINDOW)
                if result.returncode == 0:
                    try:
                        output = result.stdout.decode('gbk', errors='ignore')
                    except (UnicodeDecodeError, AttributeError):
                        output = result.stdout.decode('utf-8', errors='ignore')
                    lines = output.split('\n')
                    
                    current_info = {}
                    for line in lines:
                        line_stripped = line.strip()
                        
                        # 适配器名称
                        if line_stripped.startswith("名称") or line_stripped.startswith("Name"):
                            name_match = re.search(r'[:：]\s*(.+)', line)
                            if name_match:
                                current_info['adapter_name'] = name_match.group(1).strip()
                        # 适配器描述（网卡型号）
                        elif line_stripped.startswith("描述") or line_stripped.startswith("Description"):
                            desc_match = re.search(r'[:：]\s*(.+)', line)
                            if desc_match:
                                current_info['adapter_description'] = desc_match.group(1).strip()
                        # 物理地址（MAC）
                        elif "物理地址" in line or "Physical address" in line:
                            mac_match = re.search(r'[:：]\s*(.+)', line)
                            if mac_match:
                                current_info['mac'] = mac_match.group(1).strip()
                        # 状态
                        elif line_stripped.startswith("状态") or line_stripped.startswith("State"):
                            state_match = re.search(r'[:：]\s*(.+)', line)
                            if state_match:
                                current_info['state'] = state_match.group(1).strip()
                        # SSID
                        elif line_stripped.startswith("SSID") and "BSSID" not in line and ":" in line and "不存在" not in line:
                            ssid_match = re.search(r'[:：]\s*(.+)', line)
                            if ssid_match:
                                current_info['ssid'] = ssid_match.group(1).strip()
                        # BSSID（AP的MAC地址）
                        elif "BSSID" in line and ":" in line:
                            bssid_match = re.search(r'[:：]\s*(.+)', line)
                            if bssid_match:
                                current_info['bssid'] = bssid_match.group(1).strip()
                        # 无线电类型（WiFi标准）
                        elif "无线电类型" in line or "Radio type" in line:
                            radio_match = re.search(r'[:：]\s*(.+)', line)
                            if radio_match:
                                current_info['radio_type'] = radio_match.group(1).strip()
                        # 频道
                        elif "频道" in line or "Channel" in line:
                            channel_match = re.search(r'[:：]\s*(.+)', line)
                            if channel_match:
                                current_info['channel'] = channel_match.group(1).strip()
                        # 信号强度
                        elif "信号" in line and ":" in line:
                            signal_match = re.search(r'[:：]\s*(\d+%)', line)
                            if signal_match:
                                current_info['signal'] = signal_match.group(1).strip()
                        # 接收/发送速率
                        elif "接收速率" in line or "Receive rate" in line:
                            rate_match = re.search(r'[:：]\s*(.+)', line)
                            if rate_match:
                                current_info['receive_rate'] = rate_match.group(1).strip()
                        elif "传输速率" in line or "Transmit rate" in line:
                            rate_match = re.search(r'[:：]\s*(.+)', line)
                            if rate_match:
                                current_info['transmit_rate'] = rate_match.group(1).strip()
                        # 认证
                        elif "认证" in line and ":" in line:
                            auth_match = re.search(r'[:：]\s*(.+)', line)
                            if auth_match:
                                raw_auth = auth_match.group(1).strip()
                                # 标准化认证方式
                                current_info['authentication'] = self._normalize_authentication(raw_auth)
                        # 加密/密码
                        elif "加密" in line or "密码" in line or "Cipher" in line:
                            enc_match = re.search(r'[:：]\s*(.+)', line)
                            if enc_match:
                                current_info['encryption'] = enc_match.group(1).strip()
                        # 连接模式
                        elif "连接模式" in line or "Connection mode" in line:
                            mode_match = re.search(r'[:：]\s*(.+)', line)
                            if mode_match:
                                current_info['mode'] = mode_match.group(1).strip()
                    
                    # 获取IP地址（从网络接口信息）
                    try:
                        interfaces = self.connectivity_diag.get_network_interfaces()
                        for interface in interfaces:
                            if "无线" in interface['name'] or "Wi-Fi" in interface['name'] or "wlan" in interface['name'].lower():
                                if 'ip' in interface and interface['ip']:
                                    current_info['ip'] = interface['ip']
                                # 如果没有从netsh获取到MAC，从这里获取
                                if 'mac' not in current_info and 'mac' in interface:
                                    current_info['mac'] = interface['mac']
                                break
                    except:
                        pass  # 如果获取IP失败，不影响其他信息
                    
                    return current_info
            else:
                # Linux/Mac系统获取当前WiFi信息
                if self.system == "linux":
                    cmd = ["iw", "dev"]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, creationflags=CREATE_NO_WINDOW)
                    if result.returncode == 0:
                        output = result.stdout
                        # 简化的解析，实际实现可能需要更复杂的处理
                        if "Connected" in output:
                            # 找到连接的接口和相关信息
                            lines = output.split('\n')
                            current_info = {"status": "Connected"}
                            for line in lines:
                                if "ssid" in line.lower():
                                    ssid_match = re.search(r'ssid\s+(.+)', line)
                                    if ssid_match:
                                        current_info['ssid'] = ssid_match.group(1).strip()
                                elif "channel" in line.lower():
                                    channel_match = re.search(r'channel\s+(\d+)', line)
                                    if channel_match:
                                        current_info['channel'] = channel_match.group(1)
                            return current_info
                else:  # Mac
                    cmd = ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-I"]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, creationflags=CREATE_NO_WINDOW)
                    if result.returncode == 0:
                        output = result.stdout
                        current_info = {}
                        for line in output.split('\n'):
                            if "SSID:" in line:
                                ssid_match = re.search(r'SSID:\s*(.+)', line)
                                if ssid_match:
                                    current_info['ssid'] = ssid_match.group(1).strip()
                            elif "agrCtlRSSI:" in line:
                                rssi_match = re.search(r'agrCtlRSSI:\s*(-?\d+)', line)
                                if rssi_match:
                                    current_info['signal_dbm'] = f"{rssi_match.group(1)} dBm"
                                    # 转换为百分比
                                    rssi = int(rssi_match.group(1))
                                    if rssi >= -50:
                                        percent = 100
                                    elif rssi <= -100:
                                        percent = 0
                                    else:
                                        percent = 2 * (rssi + 100)
                                    current_info['signal_percent'] = max(0, min(100, int(percent)))
                            elif "channel:" in line:
                                channel_match = re.search(r'channel:\s*(\d+)', line)
                                if channel_match:
                                    current_info['channel'] = channel_match.group(1)
                            elif "BSSID:" in line:
                                bssid_match = re.search(r'BSSID:\s*([0-9A-Fa-f:-]+)', line)
                                if bssid_match:
                                    current_info['bssid'] = bssid_match.group(1).strip()
                        return current_info
        
        except subprocess.TimeoutExpired:
            print("获取当前WiFi信息超时")
        except Exception as e:
            print(f"获取当前WiFi信息时出错: {e}")
        
        return {}
    
    def monitor_wifi_signal(self, duration=60, interval=2):
        """监控WiFi信号强度变化"""
        signal_history = []
        start_time = time.time()
        
        print(f"开始监控WiFi信号强度变化，持续 {duration} 秒...")
        
        while time.time() - start_time < duration:
            current_info = self.get_current_wifi_info()
            if 'signal' in current_info or 'signal_percent' in current_info:
                signal_value = current_info.get('signal', current_info.get('signal_percent', '未知'))
                timestamp = time.strftime("%H:%M:%S")
                signal_history.append({
                    'timestamp': timestamp,
                    'signal': signal_value,
                    'signal_dbm': current_info.get('signal_dbm', '未知')
                })
                print(f"[{timestamp}] 信号强度: {signal_value} ({current_info.get('signal_dbm', '未知')})")
            
            time.sleep(interval)
        
        return signal_history
    
    def analyze_wifi_quality(self, ssid=None):
        """分析WiFi网络质量"""
        if ssid is None:
            # 分析当前连接的WiFi
            current_info = self.get_current_wifi_info()
            if not current_info:
                return {"error": "未连接到任何WiFi网络"}
            
            ssid = current_info.get('ssid', '未知')
            signal_str = current_info.get('signal', current_info.get('signal_percent', '未知'))
            
            # 尝试提取信号强度数值
            signal_value = 0
            if signal_str != '未知':
                try:
                    match = re.search(r'(\d+)', signal_str)
                    if match:
                        signal_value = int(match.group(1))
                except (ValueError, AttributeError, TypeError):
                    pass
        else:
            # 分析指定SSID的WiFi（从扫描结果中查找）
            networks = self.scan_wifi_networks()
            target_network = None
            for network in networks:
                if network.get('ssid') == ssid:
                    target_network = network
                    break
            
            if not target_network:
                return {"error": f"未找到SSID为'{ssid}'的WiFi网络"}
            
            signal_str = target_network.get('signal_percent', '未知')
            signal_dbm_str = target_network.get('signal_dbm', '未知')
            
            # 尝试提取信号强度数值
            signal_value = 0
            if signal_str != '未知':
                try:
                    match = re.search(r'(\d+)', signal_str)
                    if match:
                        signal_value = int(match.group(1))
                except (ValueError, AttributeError, TypeError):
                    pass
        
        # 评估WiFi质量
        quality_assessment = {
            'ssid': ssid,
            'signal_strength': signal_str,
            'quality_level': '',
            'recommendation': ''
        }
        
        if signal_value >= 70:
            quality_assessment['quality_level'] = '优秀'
            quality_assessment['recommendation'] = '信号强度优秀，网络体验良好'
        elif signal_value >= 50:
            quality_assessment['quality_level'] = '良好'
            quality_assessment['recommendation'] = '信号强度良好，可满足日常使用需求'
        elif signal_value >= 30:
            quality_assessment['quality_level'] = '一般'
            quality_assessment['recommendation'] = '信号强度一般，可能影响网络体验，建议靠近路由器'
        else:
            quality_assessment['quality_level'] = '较差'
            quality_assessment['recommendation'] = '信号强度较差，建议调整位置或检查路由器设置'
        
        return quality_assessment
    
    def clear_cache(self):
        """清除缓存数据"""
        with self._scan_lock:
            self._cached_networks = []
            self._last_scan_time = 0
    
    def set_cache_timeout(self, timeout):
        """设置缓存超时时间
        
        Args:
            timeout: 超时时间(秒)，0表示禁用缓存
            
        Raises:
            ValueError: 如果timeout小于0
        """
        if timeout < 0:
            raise ValueError("缓存超时时间不能为负数")
        self._cache_timeout = timeout
        self._cache_enabled = (timeout > 0)
    
    def set_quick_mode(self, enabled):
        """设置快速扫描模式
        
        Args:
            enabled: True启用快速模式(8秒超时), False标准模式(15秒超时)
        """
        self._quick_mode = enabled
        self._scan_timeout = 8 if enabled else 15
    
    def get_scan_stats(self):
        """获取扫描统计信息"""
        return {
            'cache_enabled': self._cache_enabled,
            'cache_timeout': self._cache_timeout,
            'last_scan_time': self._last_scan_time,
            'cached_count': len(self._cached_networks),
            'quick_mode': self._quick_mode,
            'scan_timeout': self._scan_timeout
        }


def main():
    """测试函数"""
    analyzer = WiFiAnalyzer()
    
    print("=== WiFi接口信息 ===")
    interfaces = analyzer.get_wifi_interfaces()
    for interface in interfaces:
        print(interface)
    
    print("\n=== 扫描周围的WiFi网络 ===")
    networks = analyzer.scan_wifi_networks()
    for i, network in enumerate(networks[:10]):  # 只显示前10个网络
        print(f"{i+1}. SSID: {network.get('ssid', '未知')}, 信号: {network.get('signal_percent', '未知')}, 加密: {network.get('encryption', '未知')}")
    
    print("\n=== 当前WiFi连接信息 ===")
    current_info = analyzer.get_current_wifi_info()
    if current_info:
        for key, value in current_info.items():
            print(f"{key}: {value}")
    else:
        print("未连接到WiFi网络或无法获取信息")
    
    print("\n=== WiFi质量分析 ===")
    quality = analyzer.analyze_wifi_quality()
    if 'error' not in quality:
        print(f"SSID: {quality['ssid']}")
        print(f"信号强度: {quality['signal_strength']}")
        print(f"质量等级: {quality['quality_level']}")
        print(f"建议: {quality['recommendation']}")
    else:
        print(quality['error'])


if __name__ == "__main__":
    main()