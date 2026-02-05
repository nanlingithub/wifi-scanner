#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基础连通性诊断模块
"""

import subprocess
import platform
import socket
import re
from core.utils import LoggerConfig, SocketManager

# Windows下隐藏cmd窗口
if platform.system().lower() == "windows":
    CREATE_NO_WINDOW = 0x08000000
else:
    CREATE_NO_WINDOW = 0


class ConnectivityDiagnostic:
    """基础连通性诊断类"""
    
    def __init__(self):
        self.system = platform.system().lower()
        # 设置默认socket超时
        socket.setdefaulttimeout(5)
        self.logger = LoggerConfig.get_logger()
    
    def check_network_adapters(self):
        """检查网络适通配器状态"""
        try:
            if self.system == "windows":
                cmd = ["netsh", "interface", "show", "interface"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, creationflags=CREATE_NO_WINDOW)
                # 检查是否有启用且已连接的接口
                lines = result.stdout.split('\n')
                for line in lines:
                    if "已连接" in line or "connected" in line.lower():
                        if "启用" in line or "enabled" in line.lower():
                            return True
                return False
            else:
                # 对于Linux/Mac系统，检查是否有UP状态的接口
                cmd = ["ifconfig"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, creationflags=CREATE_NO_WINDOW)
                return "UP" in result.stdout or "RUNNING" in result.stdout
        except subprocess.TimeoutExpired:
            print("检查网络适配器超时")
            return False
        except Exception as e:
            print(f"检查网络适配器时出错: {e}")
            return False
    
    def check_ip_configuration(self):
        """检查IP地址配置"""
        try:
            if self.system == "windows":
                cmd = ["ipconfig"]
            else:
                cmd = ["ip", "addr", "show"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, creationflags=CREATE_NO_WINDOW)
            # 检查是否有有效的IPv4地址
            if self.system == "windows":
                # Windows上查找IPv4地址模式
                ipv4_pattern = r"IPv4.*?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
                match = re.search(ipv4_pattern, result.stdout)
                return match is not None
            else:
                # Linux/Mac上查找inet地址
                inet_pattern = r"inet (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
                matches = re.findall(inet_pattern, result.stdout)
                # 排除回环地址
                for ip in matches:
                    if not ip.startswith("127."):
                        return True
                return False
        except subprocess.TimeoutExpired:
            print("检查IP配置超时")
            return False
        except Exception as e:
            print(f"检查IP配置时出错: {e}")
            return False
    
    def test_loopback_address(self):
        """测试本地环回地址"""
        return self._ping_host("127.0.0.1", count=2, timeout=3)
    
    def test_gateway_connectivity(self):
        """测试网关连通性"""
        gateway = self._get_default_gateway()
        if gateway:
            # 首先尝试ping网关
            ping_result = self._ping_host(gateway, count=3, timeout=5)
            if ping_result:
                return True
            
            # 如果ping失败，尝试TCP连接到常见端口
            common_ports = [80, 443, 53, 22, 23]
            for port in common_ports:
                try:
                    with SocketManager(timeout=3) as sock:
                        result = sock.connect_ex((gateway, port))
                        if result == 0:
                            self.logger.info(f"网关 {gateway}:{port} 连接成功")
                            return True
                except Exception as e:
                    self.logger.debug(f"连接网关 {gateway}:{port} 失败: {e}")
                    continue
            
            # 如果所有方法都失败，返回False
            self.logger.warning(f"无法连接到网关 {gateway}")
            return False
        return False
    
    def _get_default_gateway(self):
        """获取默认网关"""
        try:
            if self.system == "windows":
                cmd = ["ipconfig"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, creationflags=CREATE_NO_WINDOW)
                lines = result.stdout.split('\n')
                gateways = []
                for line in lines:
                    # 匹配中文或英文的默认网关
                    if "默认网关" in line or "Default Gateway" in line:
                        # 提取IP地址
                        ip_pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
                        matches = re.findall(ip_pattern, line)
                        gateways.extend(matches)
                
                # 返回第一个找到的网关
                if gateways:
                    return gateways[0]
            else:
                cmd = ["ip", "route", "show", "default"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, creationflags=CREATE_NO_WINDOW)
                if result.returncode == 0 and result.stdout:
                    # 查找via后面的IP地址
                    parts = result.stdout.split()
                    for i, part in enumerate(parts):
                        if part == "via" and i + 1 < len(parts):
                            return parts[i + 1]
                        
                # 如果没有默认路由，尝试获取所有网关
                cmd = ["ip", "route", "show"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, creationflags=CREATE_NO_WINDOW)
                if result.returncode == 0 and result.stdout:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if "default" in line and "via" in line:
                            parts = line.split()
                            for i, part in enumerate(parts):
                                if part == "via" and i + 1 < len(parts):
                                    return parts[i + 1]
        except subprocess.TimeoutExpired:
            print("获取默认网关超时")
        except Exception as e:
            print(f"获取默认网关时出错: {e}")
        
        return None
    
    def _ping_host(self, host, count=1, timeout=5):
        """Ping主机"""
        try:
            if self.system == "windows":
                cmd = ["ping", "-n", str(count), "-w", str(timeout * 1000), host]
            else:
                cmd = ["ping", "-c", str(count), "-W", str(timeout), host]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5, creationflags=CREATE_NO_WINDOW)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print(f"Ping {host} 超时")
            return False
        except Exception as e:
            print(f"Ping {host} 时出错: {e}")
            return False
    
    def get_network_interfaces(self):
        """获取网络接口信息（IP和MAC地址）"""
        interfaces = []
        try:
            if self.system == "windows":
                # 获取IP配置信息
                ipconfig_result = subprocess.run(["ipconfig", "/all"], capture_output=True, text=True, timeout=15, creationflags=CREATE_NO_WINDOW)
                if ipconfig_result.returncode == 0:
                    output = ipconfig_result.stdout
                    # 分割不同适配器的信息
                    adapters = re.split(r'\r?\n\r?\n', output)
                    for adapter in adapters:
                        if "IPv4" in adapter or "IP Address" in adapter or "物理地址" in adapter or "Physical Address" in adapter:
                            # 提取适配器名称
                            name_match = re.search(r'(以太网适配器|无线局域网适配器|Ethernet adapter|Wireless LAN adapter)\s+([^\r\n:]+)', adapter)
                            if name_match:
                                interface_name = name_match.group(2).strip()
                                
                                # 提取IPv4地址
                                ip_match = re.search(r'IPv4[^\d]+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', adapter)
                                ip_address = ip_match.group(1) if ip_match else "未获取到IP地址"
                                
                                # 提取MAC地址（物理地址）
                                mac_match = re.search(r'(物理地址|Physical Address)[^\w]+([0-9A-F\-]+)', adapter)
                                mac_address = mac_match.group(2) if mac_match else "未获取到MAC地址"
                                
                                # 检查是否已连接
                                if "已连接" in adapter or "Media disconnected" not in adapter:
                                    interfaces.append({
                                        "name": interface_name,
                                        "ip": ip_address,
                                        "mac": mac_address
                                    })
            else:
                # Linux/Mac系统
                # 获取网络接口列表
                ifconfig_result = subprocess.run(["ifconfig"], capture_output=True, text=True, timeout=10, creationflags=CREATE_NO_WINDOW)
                if ifconfig_result.returncode == 0:
                    output = ifconfig_result.stdout
                    # 分割不同接口的信息
                    interface_blocks = re.split(r'\n(?=\w)', output)
                    for block in interface_blocks:
                        # 提取接口名称
                        name_match = re.match(r'^(\w+)', block)
                        if name_match:
                            interface_name = name_match.group(1)
                            # 提取IPv4地址
                            ip_match = re.search(r'inet (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', block)
                            ip_address = ip_match.group(1) if ip_match and not ip_match.group(1).startswith("127.") else "未获取到IP地址"
                            
                            # 提取MAC地址
                            mac_match = re.search(r'(ether|hwaddr) ([0-9a-fA-F:]+)', block)
                            mac_address = mac_match.group(2) if mac_match else "未获取到MAC地址"
                            
                            # 检查接口是否启用
                            if "UP" in block and "LOOPBACK" not in block:
                                interfaces.append({
                                    "name": interface_name,
                                    "ip": ip_address,
                                    "mac": mac_address
                                })
        except subprocess.TimeoutExpired:
            print("获取网络接口信息超时")
        except Exception as e:
            print(f"获取网络接口信息时出错: {e}")
        
        return interfaces
    
    def test_datacenter_connectivity(self, datacenter_ip):
        """测试到数据中心的连通性"""
        return self._ping_host(datacenter_ip, count=3, timeout=5)


def main():
    """测试函数"""
    diagnostic = ConnectivityDiagnostic()
    print("网络适配器状态:", diagnostic.check_network_adapters())
    print("IP配置:", diagnostic.check_ip_configuration())
    print("环回地址测试:", diagnostic.test_loopback_address())
    print("网关连通性:", diagnostic.test_gateway_connectivity())


if __name__ == "__main__":
    main()