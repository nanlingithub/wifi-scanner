"""
内存监控模块
用于定期记录应用程序内存使用情况
P2-3优化: 添加内存监控日志
"""

import psutil
import logging
import threading
import time
from datetime import datetime

class MemoryMonitor:
    """内存监控器
    
    功能:
    - 定期记录内存使用情况
    - 自动垃圾回收
    - 内存泄漏警告
    """
    
    def __init__(self, interval_minutes=60, log_file='logs/memory_monitor.log'):
        """初始化内存监控器
        
        Args:
            interval_minutes: 监控间隔（分钟）
            log_file: 日志文件路径
        """
        self.interval = interval_minutes * 60  # 转换为秒
        self.log_file = log_file
        self.running = False
        self.monitor_thread = None
        
        # 配置日志
        self.logger = logging.getLogger('MemoryMonitor')
        self.logger.setLevel(logging.INFO)
        
        # 文件处理器
        import os
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        handler = logging.FileHandler(log_file, encoding='utf-8')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        self.logger.addHandler(handler)
        
        # 基线内存（首次记录）
        self.baseline_memory = None
        
    def start(self):
        """启动内存监控"""
        if not self.running:
            self.running = True
            self.monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True,
                name="MemoryMonitor"
            )
            self.monitor_thread.start()
            self.logger.info("✅ 内存监控已启动")
    
    def stop(self):
        """停止内存监控"""
        self.running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=3)
        self.logger.info("🛑 内存监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                self._log_memory_usage()
                time.sleep(self.interval)
            except Exception as e:
                self.logger.error(f"内存监控出错: {e}")
    
    def _log_memory_usage(self):
        """记录内存使用情况"""
        try:
            import gc
            import sys
            
            # 获取进程内存信息
            process = psutil.Process()
            mem_info = process.memory_info()
            
            # RSS: 实际物理内存
            rss_mb = mem_info.rss / 1024 / 1024
            
            # VMS: 虚拟内存
            vms_mb = mem_info.vms / 1024 / 1024
            
            # 系统内存使用率
            system_mem = psutil.virtual_memory()
            system_percent = system_mem.percent
            
            # Python对象数量
            gc.collect()  # 强制垃圾回收
            obj_count = len(gc.get_objects())
            
            # 记录基线
            if self.baseline_memory is None:
                self.baseline_memory = rss_mb
                self.logger.info(f"📊 内存基线: {rss_mb:.1f} MB")
            
            # 内存增长
            growth_mb = rss_mb - self.baseline_memory
            growth_percent = (growth_mb / self.baseline_memory * 100) if self.baseline_memory > 0 else 0
            
            # 日志记录
            log_msg = (
                f"内存使用: RSS={rss_mb:.1f}MB, VMS={vms_mb:.1f}MB, "
                f"增长={growth_mb:+.1f}MB({growth_percent:+.1f}%), "
                f"系统={system_percent:.1f}%, "
                f"对象数={obj_count:,}"
            )
            
            # 根据增长情况调整日志级别
            if growth_percent > 50:
                self.logger.warning(f"⚠️ {log_msg}")
                self.logger.warning("内存增长超过50%，可能存在内存泄漏")
            elif growth_percent > 30:
                self.logger.warning(f"🟡 {log_msg}")
            else:
                self.logger.info(f"✅ {log_msg}")
            
        except Exception as e:
            self.logger.error(f"记录内存失败: {e}")
    
    def get_current_memory(self):
        """获取当前内存使用（MB）"""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0


# 全局单例
_memory_monitor = None

def get_memory_monitor(interval_minutes=60):
    """获取内存监控器实例
    
    Args:
        interval_minutes: 监控间隔（分钟），默认60分钟
    
    Returns:
        MemoryMonitor实例
    """
    global _memory_monitor
    if _memory_monitor is None:
        _memory_monitor = MemoryMonitor(interval_minutes=interval_minutes)
    return _memory_monitor


if __name__ == '__main__':
    # 测试内存监控
    print("测试内存监控模块...")
    
    monitor = get_memory_monitor(interval_minutes=0.1)  # 6秒间隔（测试用）
    monitor.start()
    
    print("内存监控运行中，按Ctrl+C停止...")
    try:
        # 模拟内存增长
        data = []
        for i in range(10):
            time.sleep(10)
            # 每10秒添加1MB数据
            data.append(b'x' * (1024 * 1024))
            print(f"已分配 {len(data)} MB数据")
    except KeyboardInterrupt:
        print("\n停止测试...")
    finally:
        monitor.stop()
        print("测试完成，查看 logs/memory_monitor.log")
