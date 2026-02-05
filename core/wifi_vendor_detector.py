"""
WiFi网卡厂商识别模块
支持主流无线网卡厂家的设备识别
"""

class WiFiVendorDetector:
    """WiFi网卡厂商识别器"""
    
    # 主流WiFi网卡厂商关键词映射（按优先级排序）
    VENDOR_KEYWORDS = {
        'MediaTek': {
            'keywords': ['MediaTek', 'MT7', 'MT79', 'Ralink'],
            'icon': '🟠',
            'full_name': 'MediaTek Inc.',
            'type': '主流'
        },
        'Intel': {
            'keywords': ['Intel', 'Centrino', 'Wireless-AC', 'Wireless-N', 'Wi-Fi 6', 'Wi-Fi 6E', 'AX200', 'AX201', 'AX210', 'AX211', 'AC9560'],
            'icon': '🔵',
            'full_name': 'Intel Corporation',
            'type': '高端'
        },
        'Realtek': {
            'keywords': ['Realtek', 'RTL', 'RTW'],
            'icon': '🟡',
            'full_name': 'Realtek Semiconductor',
            'type': '主流'
        },
        'Qualcomm': {
            'keywords': ['Qualcomm', 'Atheros', 'QCA', 'Killer'],
            'icon': '🔴',
            'full_name': 'Qualcomm Atheros',
            'type': '高端'
        },
        'Broadcom': {
            'keywords': ['Broadcom', 'BCM'],
            'icon': '🟢',
            'full_name': 'Broadcom Corporation',
            'type': '高端'
        },
        'Marvell': {
            'keywords': ['Marvell', 'AVASTAR'],
            'icon': '🟣',
            'full_name': 'Marvell Technology',
            'type': '高端'
        },
        'TP-Link': {
            'keywords': ['TP-Link', 'TL-'],
            'icon': '🔷',
            'full_name': 'TP-Link Technologies',
            'type': '消费级'
        },
        'D-Link': {
            'keywords': ['D-Link', 'DWA-'],
            'icon': '🔶',
            'full_name': 'D-Link Corporation',
            'type': '消费级'
        },
        'ASUS': {
            'keywords': ['ASUS', 'ASUSTeK'],
            'icon': '⚫',
            'full_name': 'ASUS Computer',
            'type': '高端'
        },
        'NetGear': {
            'keywords': ['NetGear', 'NETGEAR'],
            'icon': '⚪',
            'full_name': 'NetGear Inc.',
            'type': '消费级'
        }
    }
    
    # WiFi标准识别
    WIFI_STANDARDS = {
        'Wi-Fi 6E': {'standard': '802.11ax (6GHz)', 'speed': '最高9.6Gbps', 'generation': 'WiFi 6E'},
        'Wi-Fi 6': {'standard': '802.11ax', 'speed': '最高9.6Gbps', 'generation': 'WiFi 6'},
        'AX': {'standard': '802.11ax', 'speed': '最高9.6Gbps', 'generation': 'WiFi 6'},
        'Wi-Fi 5': {'standard': '802.11ac', 'speed': '最高3.5Gbps', 'generation': 'WiFi 5'},
        'AC': {'standard': '802.11ac', 'speed': '最高3.5Gbps', 'generation': 'WiFi 5'},
        'Wi-Fi 4': {'standard': '802.11n', 'speed': '最高600Mbps', 'generation': 'WiFi 4'},
        'N': {'standard': '802.11n', 'speed': '最高600Mbps', 'generation': 'WiFi 4'},
        'G': {'standard': '802.11g', 'speed': '最高54Mbps', 'generation': 'WiFi 3'},
        'B': {'standard': '802.11b', 'speed': '最高11Mbps', 'generation': 'WiFi 1'}
    }
    
    @classmethod
    def detect_vendor(cls, description: str) -> dict:
        """
        检测WiFi网卡厂商
        
        Args:
            description: 网卡描述字符串
            
        Returns:
            包含厂商信息的字典
        """
        if not description:
            return {
                'vendor': 'Unknown',
                'icon': '❓',
                'full_name': '未知厂商',
                'type': '未知'
            }
        
        # 遍历厂商关键词
        for vendor_name, vendor_info in cls.VENDOR_KEYWORDS.items():
            for keyword in vendor_info['keywords']:
                if keyword.lower() in description.lower():
                    return {
                        'vendor': vendor_name,
                        'icon': vendor_info['icon'],
                        'full_name': vendor_info['full_name'],
                        'type': vendor_info['type']
                    }
        
        # 未识别的厂商
        return {
            'vendor': 'Generic',
            'icon': '⚪',
            'full_name': '通用设备',
            'type': '其他'
        }
    
    @classmethod
    def detect_wifi_standard(cls, description: str) -> dict:
        """
        检测WiFi标准
        
        Args:
            description: 网卡描述字符串
            
        Returns:
            包含WiFi标准信息的字典
        """
        if not description:
            return {
                'standard': 'Unknown',
                'speed': '未知',
                'generation': '未知'
            }
        
        # 按优先级检测（从新到旧）
        for keyword, standard_info in cls.WIFI_STANDARDS.items():
            if keyword in description:
                return standard_info.copy()
        
        return {
            'standard': 'Unknown',
            'speed': '未知',
            'generation': '未知'
        }
    
    @classmethod
    def get_enhanced_display(cls, name: str, description: str, state: str = '', 
                            ssid: str = '', signal: str = '') -> str:
        """
        生成增强显示字符串（带厂商图标和优化格式）
        
        Args:
            name: 网卡名称
            description: 网卡描述
            state: 连接状态
            ssid: WiFi名称
            signal: 信号强度
            
        Returns:
            优化后的显示字符串
        """
        vendor_info = cls.detect_vendor(description)
        wifi_standard = cls.detect_wifi_standard(description)
        
        # 构建显示部分
        parts = []
        
        # 1. 厂商图标 + 网卡名称
        parts.append(f"{vendor_info['icon']}[{name}]")
        
        # 2. 简化的网卡型号（移除厂商名称，避免重复）
        if description:
            # 移除厂商名称和商标符号
            desc = description
            for vendor_name in cls.VENDOR_KEYWORDS.keys():
                desc = desc.replace(vendor_name, '').replace('(R)', '').replace('(TM)', '')
            desc = desc.strip()
            
            # 如果描述太长，截取关键部分
            if len(desc) > 35:
                # 提取型号核心部分
                if 'Wi-Fi' in desc:
                    desc = desc[desc.index('Wi-Fi'):]
                desc = desc[:35] + '...'
            
            parts.append(desc)
        
        # 3. WiFi标准徽章
        if wifi_standard['generation'] != '未知':
            parts.append(f"[{wifi_standard['generation']}]")
        
        # 4. 状态信息
        status_parts = []
        if state:
            status_parts.append(state)
        if ssid:
            status_parts.append(f"连接:{ssid}")
        if signal:
            status_parts.append(f"信号:{signal}")
        
        if status_parts:
            parts.append(f"({', '.join(status_parts)})")
        
        return " ".join(parts)
    
    @classmethod
    def get_vendor_statistics(cls, interfaces: list) -> dict:
        """
        统计网卡厂商分布
        
        Args:
            interfaces: 接口信息列表
            
        Returns:
            厂商统计字典
        """
        stats = {}
        
        for iface in interfaces:
            if isinstance(iface, dict) and 'description' in iface:
                vendor_info = cls.detect_vendor(iface['description'])
                vendor_name = vendor_info['vendor']
                
                if vendor_name not in stats:
                    stats[vendor_name] = {
                        'count': 0,
                        'icon': vendor_info['icon'],
                        'full_name': vendor_info['full_name'],
                        'type': vendor_info['type']
                    }
                
                stats[vendor_name]['count'] += 1
        
        return stats
