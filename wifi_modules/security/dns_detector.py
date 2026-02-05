"""
DNS劫持检测模块
功能：DNS查询验证、中间人攻击检测
版本：V2.0 Enhanced (集成DNS增强检测)
"""

import socket
import subprocess
import platform
from typing import Dict, List, Any, Optional, Tuple

# 导入DNS增强检测模块
try:
    from .dns_enhanced import DNSEnhancedDetector
    HAS_DNS_ENHANCED = True
except ImportError:
    HAS_DNS_ENHANCED = False


class DNSHijackDetector:
    """DNS劫持检测器"""
    
    # 可信DNS服务器列表
    TRUSTED_DNS = {
        'Google': '8.8.8.8',
        'Cloudflare': '1.1.1.1',
        'Quad9': '9.9.9.9',
        'OpenDNS': '208.67.222.222',
        'AliDNS': '223.5.5.5',
        '114DNS': '114.114.114.114'
    }
    
    # 测试域名（用于检测劫持）
    TEST_DOMAINS = [
        'www.google.com',
        'www.baidu.com',
        'www.github.com',
        'www.microsoft.com'
    ]
    
    def __init__(self):
        self.is_windows = platform.system().lower() == "windows"
        
        # 初始化DNS增强检测器
        if HAS_DNS_ENHANCED:
            self.enhanced_detector = DNSEnhancedDetector()
        else:
            self.enhanced_detector = None
        
    def check_dns_hijacking(self) -> Dict[str, Any]:
        """
        检测DNS劫持（增强版）
        
        Returns:
            检测结果字典
        """
        # 优先使用DNS增强检测
        if self.enhanced_detector:
            enhanced_result = self.enhanced_detector.comprehensive_check()
            
            # 转换为兼容格式
            return {
                'hijacked': enhanced_result['hijack_detected'],
                'hijacked_domains': [
                    inc['domain'] for inc in 
                    enhanced_result['consistency_check'].get('inconsistencies', [])
                ],
                'current_dns': self._get_current_dns(),
                'test_results': enhanced_result['consistency_check'].get('test_domains', []),
                'recommendations': enhanced_result['recommendations'],
                'dnssec_support': enhanced_result['dnssec_support'],  # 新增
                'doh_available': enhanced_result['doh_available'],    # 新增
                'details': enhanced_result['details']                 # 新增
            }
        
        # 回退到原有检测逻辑（向后兼容）
        results = {
            'hijacked': False,
            'hijacked_domains': [],
            'current_dns': self._get_current_dns(),
            'test_results': [],
            'recommendations': []
        }
        
        # 对每个测试域名进行检测
        for domain in self.TEST_DOMAINS:
            domain_result = self._test_domain(domain)
            results['test_results'].append(domain_result)
            
            if domain_result['suspicious']:
                results['hijacked'] = True
                results['hijacked_domains'].append(domain)
        
        # 生成建议
        if results['hijacked']:
            results['recommendations'].append('⚠️ 检测到DNS可能被劫持！')
            results['recommendations'].append('🔴 立即检查路由器DNS设置')
            results['recommendations'].append('🔴 更换为可信DNS（如8.8.8.8）')
            results['recommendations'].append('🔴 检查是否有恶意软件')
        else:
            results['recommendations'].append('✅ DNS查询正常，未检测到劫持')
        
        return results
    
    def check_gateway_arp(self) -> Dict[str, Any]:
        """
        检测ARP欺骗（简化版）
        
        Returns:
            检测结果
        """
        result = {
            'suspicious': False,
            'gateway_ip': None,
            'gateway_mac': None,
            'warnings': []
        }
        
        try:
            # 获取网关信息
            gateway_info = self._get_gateway_info()
            result['gateway_ip'] = gateway_info.get('ip')
            result['gateway_mac'] = gateway_info.get('mac')
            
            # 简单检测：多次查询网关MAC是否一致
            if result['gateway_ip']:
                mac_list = []
                for _ in range(3):
                    mac = self._query_mac(result['gateway_ip'])
                    if mac:
                        mac_list.append(mac)
                
                # MAC地址不一致 - 可能ARP欺骗
                if len(set(mac_list)) > 1:
                    result['suspicious'] = True
                    result['warnings'].append('网关MAC地址不稳定，可能存在ARP欺骗')
        
        except Exception as e:
            result['warnings'].append(f'检测失败: {str(e)}')
        
        return result
    
    # ===== 辅助方法 =====
    
    def _test_domain(self, domain: str) -> Dict[str, Any]:
        """
        测试单个域名的DNS解析
        
        Args:
            domain: 域名
            
        Returns:
            测试结果
        """
        result = {
            'domain': domain,
            'current_ip': None,
            'trusted_ips': {},
            'suspicious': False,
            'reason': None
        }
        
        try:
            # 1. 当前DNS解析
            current_ip = socket.gethostbyname(domain)
            result['current_ip'] = current_ip
            
            # 2. 可信DNS解析
            for dns_name, dns_server in list(self.TRUSTED_DNS.items())[:2]:  # 只测试前2个
                trusted_ip = self._query_dns(domain, dns_server)
                if trusted_ip:
                    result['trusted_ips'][dns_name] = trusted_ip
            
            # 3. 对比结果
            if result['trusted_ips']:
                trusted_ip_set = set(result['trusted_ips'].values())
                
                # 当前解析结果不在可信列表中
                if current_ip not in trusted_ip_set:
                    result['suspicious'] = True
                    result['reason'] = f'解析IP({current_ip})与可信DNS不一致'
                
                # 检测是否被解析到私有地址（常见劫持手法）
                if self._is_private_ip(current_ip):
                    result['suspicious'] = True
                    result['reason'] = f'被解析到私有地址({current_ip})'
        
        except Exception as e:
            result['reason'] = f'解析失败: {str(e)}'
        
        return result
    
    def _query_dns(self, domain: str, dns_server: str, timeout: int = 3) -> Optional[str]:
        """
        使用指定DNS服务器查询域名
        
        Args:
            domain: 域名
            dns_server: DNS服务器IP
            timeout: 超时时间
            
        Returns:
            解析得到的IP地址
        """
        try:
            if self.is_windows:
                # Windows使用nslookup
                cmd = f'nslookup {domain} {dns_server}'
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    creationflags=subprocess.CREATE_NO_WINDOW if self.is_windows else 0
                )
                
                if result.returncode == 0:
                    # 解析nslookup输出
                    for line in result.stdout.split('\n'):
                        if 'Address' in line or 'addresses' in line.lower():
                            parts = line.split(':')
                            if len(parts) >= 2:
                                ip = parts[1].strip()
                                # 验证是否为有效IP
                                if self._is_valid_ip(ip) and ip != dns_server:
                                    return ip
            
            return None
            
        except subprocess.TimeoutExpired:
            self.logger.warning(f"DNS查询超时: {domain}")
            return None
        except subprocess.CalledProcessError as e:
            self.logger.error(f"DNS查询命令执行失败: {e}")
            return None
        except Exception as e:
            self.logger.exception(f"DNS查询未知错误: {e}")
            return None
    
    def _get_current_dns(self) -> List[str]:
        """获取当前使用的DNS服务器"""
        dns_servers = []
        
        try:
            if self.is_windows:
                cmd = 'ipconfig /all'
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    encoding='gbk',
                    errors='ignore',
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                if result.returncode == 0:
                    # 解析ipconfig输出
                    for line in result.stdout.split('\n'):
                        if 'DNS' in line and ':' in line:
                            parts = line.split(':')
                            if len(parts) >= 2:
                                ip = parts[1].strip()
                                if self._is_valid_ip(ip):
                                    dns_servers.append(ip)
        
        except subprocess.CalledProcessError as e:
            self.logger.error(f"获取DNS服务器失败: {e}")
        except Exception as e:
            self.logger.exception(f"获取当前DNS未知错误: {e}")
        
        return dns_servers
    
    def _get_gateway_info(self) -> Dict[str, str]:
        """获取网关IP和MAC"""
        gateway_info = {'ip': None, 'mac': None}
        
        try:
            if self.is_windows:
                # 使用ipconfig获取网关
                cmd = 'ipconfig'
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    encoding='gbk',
                    errors='ignore',
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if '默认网关' in line or 'Default Gateway' in line:
                            parts = line.split(':')
                            if len(parts) >= 2:
                                ip = parts[1].strip()
                                if self._is_valid_ip(ip):
                                    gateway_info['ip'] = ip
                                    # 查询MAC
                                    gateway_info['mac'] = self._query_mac(ip)
                                    break
        
        except subprocess.CalledProcessError as e:
            self.logger.error(f"获取网关信息失败: {e}")
        except Exception as e:
            self.logger.exception(f"获取网关未知错误: {e}")
        
        return gateway_info
    
    def _query_mac(self, ip: str) -> Optional[str]:
        """通过ARP查询MAC地址"""
        try:
            if self.is_windows:
                cmd = f'arp -a {ip}'
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    encoding='gbk',
                    errors='ignore',
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if ip in line:
                            # 提取MAC地址
                            parts = line.split()
                            for part in parts:
                                if '-' in part and len(part) == 17:  # XX-XX-XX-XX-XX-XX
                                    return part
        
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"ARP查询失败: {ip}, {e}")
        except Exception as e:
            self.logger.debug(f"查询MAC地址失败: {ip}, {e}")
        
        return None
    
    def _is_valid_ip(self, ip_str: str) -> bool:
        """验证IP地址格式"""
        try:
            parts = ip_str.split('.')
            if len(parts) != 4:
                return False
            for part in parts:
                num = int(part)
                if num < 0 or num > 255:
                    return False
            return True
        except (ValueError, AttributeError):
            return False
    
    def _is_private_ip(self, ip_str: str) -> bool:
        """判断是否为私有IP地址"""
        try:
            parts = [int(x) for x in ip_str.split('.')]
            
            # 10.0.0.0/8
            if parts[0] == 10:
                return True
            
            # 172.16.0.0/12
            if parts[0] == 172 and 16 <= parts[1] <= 31:
                return True
            
            # 192.168.0.0/16
            if parts[0] == 192 and parts[1] == 168:
                return True
            
            # 127.0.0.0/8 (loopback)
            if parts[0] == 127:
                return True
            
            return False
            
        except:
            return False
