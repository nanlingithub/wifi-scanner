"""
WiFi性能基准测试模块
提供网速测试、延迟测试、历史记录等功能
"""
import subprocess
import json
import os
import sys
import platform
from datetime import datetime
from typing import Dict, List, Optional
import threading
import io

# 修复PyInstaller打包后的stdout/stderr问题
if getattr(sys, 'frozen', False):
    # 如果是打包后的exe，重定向stdout和stderr
    if sys.stdout is None:
        sys.stdout = io.StringIO()
    if sys.stderr is None:
        sys.stderr = io.StringIO()

# 导入speedtest模块
try:
    import speedtest
    SPEEDTEST_AVAILABLE = True
except (ImportError, AttributeError, Exception) as e:
    SPEEDTEST_AVAILABLE = False
    print(f"⚠️ speedtest-cli模块加载失败: {e}，性能测试功能将不可用")

class WiFiPerformanceBenchmark:
    """WiFi性能基准测试器"""
    
    def __init__(self, history_file: str = "wifi_speed_history.json"):
        """
        初始化性能测试器
        
        Args:
            history_file: 历史记录文件路径
        """
        self.history_file = history_file
        self.history_data = self._load_history()
        self.is_testing = False
        self.current_test_result = None
        
        # P1修复: 添加线程锁保护共享数据
        self._data_lock = threading.Lock()
        
        # Windows隐藏控制台窗口
        if platform.system().lower() == "windows":
            self.CREATE_NO_WINDOW = 0x08000000
        else:
            self.CREATE_NO_WINDOW = 0
    
    def _load_history(self) -> List[Dict]:
        """加载历史测试记录"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except FileNotFoundError:
                print(f"[警告] 历史文件不存在: {self.history_file}")
                return []
            except json.JSONDecodeError as e:
                print(f"[错误] JSON解析失败: {e}")
                return []
            except Exception as e:
                print(f"[错误] 加载历史记录时发生错误: {e}")
                return []
        return []
    
    def _network_precheck(self, callback=None) -> Dict:
        """网络预检测
        
        检查网络连接状态、DNS可用性、基础延迟
        
        Args:
            callback: 进度回调函数
            
        Returns:
            预检测结果字典
        """
        result = {
            'status': True,
            'message': '',
            'dns_ok': False,
            'ping_ok': False,
            'avg_ping': 0
        }
        
        try:
            # 1. DNS解析测试
            import socket
            try:
                socket.gethostbyname('www.speedtest.net')
                result['dns_ok'] = True
            except Exception as e:
                result['status'] = False
                result['message'] = f'DNS解析失败: {str(e)}'
                return result
            
            # 2. 基础Ping测试（3次快速测试）
            if callback:
                callback("🏓 正在测试基础延迟...")
            
            # P0修复: 使用列表形式避免shell=True的命令注入风险
            ping_cmd = ["ping", "-n", "3", "-w", "2000", "8.8.8.8"]
            ping_result = subprocess.run(
                ping_cmd,
                shell=False,
                capture_output=True,
                text=True,
                creationflags=self.CREATE_NO_WINDOW,
                encoding='gbk',
                errors='ignore'
            )
            
            if ping_result.returncode == 0:
                # 解析平均延迟
                import re
                avg_match = re.search(r'平均 = (\d+)ms', ping_result.stdout)
                if avg_match:
                    result['avg_ping'] = int(avg_match.group(1))
                    result['ping_ok'] = True
                    
                    # 如果延迟过高，给出警告但不阻止测试
                    if result['avg_ping'] > 500:
                        result['message'] = f'网络延迟较高({result["avg_ping"]}ms)，测试可能需要更长时间'
                else:
                    result['ping_ok'] = True  # Ping成功但无法解析延迟
            else:
                result['status'] = False
                result['message'] = 'Ping测试失败，请检查网络连接'
                return result
            
            result['message'] = 'OK'
            return result
            
        except Exception as e:
            result['status'] = False
            result['message'] = f'预检测异常: {str(e)}'
            return result
    
    def _detect_current_wifi_protocol(self) -> str:
        """检测当前WiFi协议版本"""
        try:
            import subprocess
            result = subprocess.run(
                ['netsh', 'wlan', 'show', 'interfaces'],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=self.CREATE_NO_WINDOW,
                encoding='gbk'
            )
            
            if result.returncode == 0:
                output = result.stdout
                # 检测频道
                import re
                channel_match = re.search(r'频道.*?[:：]\s*(\d+)', output)
                radio_match = re.search(r'无线电类型.*?[:：]\s*(.+)', output)
                
                if channel_match:
                    channel = int(channel_match.group(1))
                    # 判断频段
                    if channel <= 14:
                        band = '2.4GHz'
                    elif channel >= 36 and channel <= 165:
                        band = '5GHz'
                    elif channel >= 1 and channel <= 233 and channel % 4 in [1, 5, 9]:
                        band = '6GHz'
                    else:
                        return 'N/A'
                    
                    # 根据频段判断协议
                    if band == '6GHz':
                        return 'WiFi 6E/7 (802.11ax/be)'
                    elif band == '5GHz':
                        if radio_match and '802.11ax' in radio_match.group(1):
                            return 'WiFi 6 (802.11ax)'
                        elif radio_match and '802.11ac' in radio_match.group(1):
                            return 'WiFi 5 (802.11ac)'
                        else:
                            return 'WiFi 5/6 (802.11ac/ax)'
                    else:  # 2.4GHz
                        return 'WiFi 4+ (802.11n/ax/be)'
        except Exception as e:
            print(f"[警告] 检测WiFi协议失败: {e}")
        
        return 'N/A'
    
    def _save_history(self):
        """保存历史记录"""
        try:
            # P1修复: 使用锁保护共享数据
            with self._data_lock:
                # P1修复: 限制历史记录大小防止内存泄漏
                MAX_HISTORY = 100
                if len(self.history_data) > MAX_HISTORY:
                    self.history_data = self.history_data[-MAX_HISTORY:]
                
                with open(self.history_file, 'w', encoding='utf-8') as f:
                    json.dump(self.history_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史记录失败: {e}")
    
    def check_speedtest_installed(self) -> bool:
        """
        检查speedtest模块是否可用
        
        Returns:
            是否可用
        """
        return SPEEDTEST_AVAILABLE
    
    def run_speed_test(self, callback=None) -> Dict:
        """
        运行网速测试（阻塞式）
        
        Args:
            callback: 进度回调函数 callback(status_message)
        
        Returns:
            测试结果字典
        """
        if self.is_testing:
            return {'error': '测试正在进行中'}
        
        self.is_testing = True
        self.current_test_result = None
        
        try:
            # 网络预检测
            if callback:
                callback("🔍 正在检测网络连接状态...")
            
            precheck_result = self._network_precheck(callback)
            if not precheck_result['status']:
                self.is_testing = False
                return {
                    'error': f'网络预检测失败: {precheck_result["message"]}',
                    'precheck': precheck_result
                }
            
            # 检查模块是否可用
            if not self.check_speedtest_installed():
                self.is_testing = False
                return {'error': 'speedtest-cli模块不可用，请确保已正确安装'}
            
            if callback:
                callback("正在初始化speedtest...")
            
            # 使用Python speedtest模块进行测试
            st = speedtest.Speedtest()
            
            if callback:
                callback("正在获取最佳服务器...")
            st.get_best_server()
            
            if callback:
                callback("正在测试下载速度...")
            download_speed = round(st.download() / 1_000_000, 2)  # 转换为Mbps
            
            if callback:
                callback("正在测试上传速度...")
            upload_speed = round(st.upload() / 1_000_000, 2)  # 转换为Mbps
            
            if callback:
                callback("正在解析测试结果...")
            
            # 获取测试结果
            results_dict = st.results.dict()
            
            # 提取关键指标
            ping = round(results_dict.get('ping', 0), 2)
            
            # 构建测试结果
            test_result = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'download': download_speed,
                'upload': upload_speed,
                'ping': ping,
                'jitter': 0,  # speedtest模块不直接提供抖动
                'packet_loss': 0,  # speedtest模块不直接提供丢包率
                'server': {
                    'name': results_dict.get('server', {}).get('sponsor', 'Unknown'),
                    'country': results_dict.get('server', {}).get('country', 'Unknown'),
                    'host': results_dict.get('server', {}).get('host', 'Unknown')
                },
                'client': {
                    'ip': results_dict.get('client', {}).get('ip', 'Unknown'),
                    'isp': results_dict.get('client', {}).get('isp', 'Unknown')
                },
                'wifi_protocol': self._detect_current_wifi_protocol()
            }
            
            # P1修复: 使用锁保护共享数据
            with self._data_lock:
                # 保存到历史记录
                self.history_data.append(test_result)
            self._save_history()
            
            self.current_test_result = test_result
            self.is_testing = False
            
            if callback:
                callback("测试完成！")
            
            return test_result
            
        except speedtest.ConfigRetrievalError:
            self.is_testing = False
            return {'error': '无法获取speedtest配置，请检查网络连接'}
        except speedtest.NoMatchedServers:
            self.is_testing = False
            return {'error': '未找到可用的测试服务器'}
        except speedtest.SpeedtestException as e:
            self.is_testing = False
            return {'error': f'speedtest测试失败: {str(e)}'}
        except Exception as e:
            self.is_testing = False
            return {'error': f'测试异常: {str(e)}'}
    
    def run_speed_test_async(self, callback_progress=None, callback_complete=None):
        """
        异步运行网速测试
        
        Args:
            callback_progress: 进度回调 callback(status_message)
            callback_complete: 完成回调 callback(result_dict)
        """
        def test_thread():
            result = self.run_speed_test(callback=callback_progress)
            if callback_complete:
                callback_complete(result)
        
        thread = threading.Thread(target=test_thread, daemon=True)
        thread.start()
    
    def get_history(self, limit: int = 10) -> List[Dict]:
        """
        获取历史测试记录
        
        Args:
            limit: 返回最近N条记录
        
        Returns:
            历史记录列表
        """
        # P1修复: 使用锁保护共享数据读取
        with self._data_lock:
            return self.history_data[-limit:] if self.history_data else []
    
    def get_statistics(self) -> Dict:
        """
        获取统计信息
        
        Returns:
            统计数据字典
        """
        # P1修复: 使用锁保护共享数据读取
        with self._data_lock:
            if not self.history_data:
                return {
                    'total_tests': 0,
                    'avg_download': 0,
                    'avg_upload': 0,
                    'avg_ping': 0,
                    'max_download': 0,
                    'max_upload': 0,
                    'min_ping': 0
                }
            
            downloads = [d['download'] for d in self.history_data]
            uploads = [d['upload'] for d in self.history_data]
            pings = [d['ping'] for d in self.history_data]
            
            return {
            'total_tests': len(self.history_data),
            'avg_download': round(sum(downloads) / len(downloads), 2),
            'avg_upload': round(sum(uploads) / len(uploads), 2),
            'avg_ping': round(sum(pings) / len(pings), 2),
            'max_download': round(max(downloads), 2),
            'max_upload': round(max(uploads), 2),
            'min_ping': round(min(pings), 2),
            'max_ping': round(max(pings), 2)
        }
    
    def clear_history(self):
        """清空历史记录"""
        # P1修复: 使用锁保护共享数据修改
        with self._data_lock:
            self.history_data = []
        self._save_history()
    
    def export_history_csv(self, filename: str = None) -> str:
        """
        导出历史记录为CSV
        
        Args:
            filename: 文件名，默认自动生成
        
        Returns:
            导出的文件路径
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"wifi_speed_history_{timestamp}.csv"
        
        try:
            with open(filename, 'w', encoding='utf-8-sig') as f:
                # 写入表头
                f.write("时间,下载速度(Mbps),上传速度(Mbps),延迟(ms),服务器,ISP\n")
                
                # 写入数据
                for record in self.history_data:
                    f.write(f"{record['timestamp']},")
                    f.write(f"{record['download']},")
                    f.write(f"{record['upload']},")
                    f.write(f"{record['ping']},")
                    f.write(f"{record['server']['name']},")
                    f.write(f"{record['client']['isp']}\n")
            
            return filename
        except Exception as e:
            raise Exception(f"导出CSV失败: {str(e)}")
    
    def get_quality_rating(self, download: float, upload: float, ping: float) -> Dict:
        """
        评估网络质量等级
        
        Args:
            download: 下载速度 (Mbps)
            upload: 上传速度 (Mbps)
            ping: 延迟 (ms)
        
        Returns:
            评级信息字典
        """
        # 检测WiFi协议，根据不同标准设置评分基准
        wifi_protocol = self._detect_current_wifi_protocol()
        
        # 2026年WiFi标准基准速度 (Mbps)
        if 'WiFi 7' in wifi_protocol or '802.11be' in wifi_protocol:
            # WiFi 7: 理论最高46Gbps
            download_thresholds = [500, 300, 150, 50]
            upload_thresholds = [200, 100, 50, 20]
        elif 'WiFi 6E' in wifi_protocol or '6 GHz' in wifi_protocol:
            # WiFi 6E: 理论最高9.6Gbps (6GHz频段)
            download_thresholds = [300, 200, 100, 30]
            upload_thresholds = [150, 80, 40, 15]
        elif 'WiFi 6' in wifi_protocol or '802.11ax' in wifi_protocol:
            # WiFi 6: 理论最高9.6Gbps
            download_thresholds = [200, 120, 60, 25]
            upload_thresholds = [100, 60, 30, 10]
        elif 'WiFi 5' in wifi_protocol or '802.11ac' in wifi_protocol:
            # WiFi 5: 理论最高6.9Gbps
            download_thresholds = [100, 50, 25, 10]
            upload_thresholds = [50, 20, 10, 5]
        else:
            # WiFi 4及以下或未知协议
            download_thresholds = [50, 25, 10, 5]
            upload_thresholds = [25, 10, 5, 2]
        
        # 下载速度评级（根据WiFi协议动态标准）
        if download >= download_thresholds[0]:
            download_rating = "优秀"
            download_score = 100
        elif download >= download_thresholds[1]:
            download_rating = "良好"
            download_score = 80
        elif download >= download_thresholds[2]:
            download_rating = "中等"
            download_score = 60
        elif download >= download_thresholds[3]:
            download_rating = "较差"
            download_score = 40
        else:
            download_rating = "很差"
            download_score = 20
        
        # 上传速度评级（根据WiFi协议动态标准）
        if upload >= upload_thresholds[0]:
            upload_rating = "优秀"
            upload_score = 100
        elif upload >= upload_thresholds[1]:
            upload_rating = "良好"
            upload_score = 80
        elif upload >= upload_thresholds[2]:
            upload_rating = "中等"
            upload_score = 60
        elif upload >= upload_thresholds[3]:
            upload_rating = "较差"
            upload_score = 40
        else:
            upload_rating = "很差"
            upload_score = 20
        
        # 延迟评级（通用标准，适用于所有WiFi协议）
        if ping <= 20:
            ping_rating = "优秀"
            ping_score = 100
        elif ping <= 50:
            ping_rating = "良好"
            ping_score = 80
        elif ping <= 100:
            ping_rating = "中等"
            ping_score = 60
        elif ping <= 200:
            ping_rating = "较差"
            ping_score = 40
        else:
            ping_rating = "很差"
            ping_score = 20
        
        # 综合评分（延迟权重提升，更重视网络质量）
        overall_score = (download_score * 0.35 + upload_score * 0.25 + ping_score * 0.4)
        
        if overall_score >= 90:
            overall_rating = "优秀"
        elif overall_score >= 70:
            overall_rating = "良好"
        elif overall_score >= 50:
            overall_rating = "中等"
        elif overall_score >= 30:
            overall_rating = "较差"
        else:
            overall_rating = "很差"
        
        return {
            'download_rating': download_rating,
            'upload_rating': upload_rating,
            'ping_rating': ping_rating,
            'overall_rating': overall_rating,
            'overall_score': round(overall_score, 1)
        }
