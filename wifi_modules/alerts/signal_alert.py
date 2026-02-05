"""
WiFi信号声音警报模块
当信号强度低于设定阈值时播放警报音
"""
import winsound
import platform
import threading
import time
from typing import Optional


class SignalAlert:
    """信号声音警报类"""
    
    # 警报类型
    ALERT_WARNING = 'warning'      # 警告（信号弱）
    ALERT_CRITICAL = 'critical'    # 严重（信号很弱）
    ALERT_DISCONNECT = 'disconnect'  # 断开连接
    ALERT_RECOVER = 'recover'      # 信号恢复
    
    def __init__(self):
        self.enabled = True  # 是否启用警报
        self.mute = False    # 静音模式
        
        # 阈值设置（dBm）
        self.warning_threshold = -70    # 警告阈值
        self.critical_threshold = -80   # 严重阈值
        
        # 防止重复播放
        self.last_alert_time = 0
        self.alert_cooldown = 5  # 冷却时间（秒）
        
        # 最后状态
        self.last_status = None
        
        self.system = platform.system().lower()
    
    def set_thresholds(self, warning: int, critical: int):
        """设置警报阈值"""
        self.warning_threshold = warning
        self.critical_threshold = critical
    
    def enable(self):
        """启用警报"""
        self.enabled = True
    
    def disable(self):
        """禁用警报"""
        self.enabled = False
    
    def toggle_mute(self):
        """切换静音模式"""
        self.mute = not self.mute
        return self.mute
    
    def check_signal(self, signal_dbm: float) -> Optional[str]:
        """
        检查信号强度并触发警报
        
        Args:
            signal_dbm: 信号强度（dBm）
            
        Returns:
            警报类型或None
        """
        if not self.enabled or self.mute:
            return None
        
        # 判断信号状态
        current_status = self._get_signal_status(signal_dbm)
        
        # 检查是否需要警报
        alert_type = None
        
        if current_status == 'critical' and self.last_status != 'critical':
            alert_type = self.ALERT_CRITICAL
        elif current_status == 'warning' and self.last_status not in ['warning', 'critical']:
            alert_type = self.ALERT_WARNING
        elif current_status == 'good' and self.last_status in ['warning', 'critical']:
            alert_type = self.ALERT_RECOVER
        
        # 更新最后状态
        self.last_status = current_status
        
        # 触发警报
        if alert_type:
            self._play_alert(alert_type)
        
        return alert_type
    
    def _get_signal_status(self, signal_dbm: float) -> str:
        """获取信号状态"""
        if signal_dbm >= self.warning_threshold:
            return 'good'
        elif signal_dbm >= self.critical_threshold:
            return 'warning'
        else:
            return 'critical'
    
    def _play_alert(self, alert_type: str):
        """播放警报音"""
        # 检查冷却时间
        current_time = time.time()
        if current_time - self.last_alert_time < self.alert_cooldown:
            return
        
        self.last_alert_time = current_time
        
        # 在后台线程播放，避免阻塞
        thread = threading.Thread(target=self._play_sound, args=(alert_type,))
        thread.daemon = True
        thread.start()
    
    def _play_sound(self, alert_type: str):
        """播放声音（后台线程）"""
        try:
            if self.system == "windows":
                if alert_type == self.ALERT_CRITICAL:
                    # 严重警告 - 播放3次短促的警报音
                    for _ in range(3):
                        winsound.MessageBeep(winsound.MB_ICONHAND)
                        time.sleep(0.2)
                elif alert_type == self.ALERT_WARNING:
                    # 一般警告 - 播放1次警告音
                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                elif alert_type == self.ALERT_DISCONNECT:
                    # 断开连接 - 播放错误音
                    winsound.MessageBeep(winsound.MB_ICONHAND)
                elif alert_type == self.ALERT_RECOVER:
                    # 信号恢复 - 播放提示音
                    winsound.MessageBeep(winsound.MB_ICONASTERISK)
            else:
                # Linux/Mac - 使用系统bell
                print('\a')
        except Exception as e:
            print(f"播放警报音失败: {e}")
    
    def test_alert(self, alert_type: str = ALERT_WARNING):
        """测试警报音"""
        self._play_sound(alert_type)


class SignalAlertConfig:
    """警报配置面板"""
    
    def __init__(self, alert_manager: SignalAlert):
        self.alert = alert_manager
    
    def get_config(self) -> dict:
        """获取当前配置"""
        return {
            'enabled': self.alert.enabled,
            'mute': self.alert.mute,
            'warning_threshold': self.alert.warning_threshold,
            'critical_threshold': self.alert.critical_threshold,
            'cooldown': self.alert.alert_cooldown
        }
    
    def update_config(self, config: dict):
        """更新配置"""
        if 'enabled' in config:
            self.alert.enabled = config['enabled']
        if 'mute' in config:
            self.alert.mute = config['mute']
        if 'warning_threshold' in config:
            self.alert.warning_threshold = config['warning_threshold']
        if 'critical_threshold' in config:
            self.alert.critical_threshold = config['critical_threshold']
        if 'cooldown' in config:
            self.alert.alert_cooldown = config['cooldown']
