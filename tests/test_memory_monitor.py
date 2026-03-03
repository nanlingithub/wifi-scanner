#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/memory_monitor.py 单元测试
覆盖: MemoryMonitor 类（init/start/stop/get_current_memory）及 get_memory_monitor 单例
"""

import sys
import os
import time
import threading
import tempfile
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import core.memory_monitor as _mm_module
from core.memory_monitor import MemoryMonitor, get_memory_monitor


# ============================================================================
# Fixture：每个测试前重置全局单例，避免测试互相干扰
# ============================================================================

@pytest.fixture(autouse=True)
def reset_singleton():
    """清除全局 _memory_monitor 单例，保证测试隔离"""
    _mm_module._memory_monitor = None
    yield
    # 测试结束后确保监控器已停止
    if _mm_module._memory_monitor is not None:
        try:
            _mm_module._memory_monitor.stop()
        except Exception:
            pass
    _mm_module._memory_monitor = None


# ============================================================================
# TestMemoryMonitorInit
# ============================================================================

class TestMemoryMonitorInit:
    """MemoryMonitor 初始化测试"""

    def test_default_init(self, tmp_path):
        """默认参数初始化"""
        log_file = str(tmp_path / "test_mem.log")
        monitor = MemoryMonitor(interval_minutes=60, log_file=log_file)

        assert monitor.interval == 60 * 60   # 秒
        assert monitor.running is False
        assert monitor.monitor_thread is None
        assert monitor.baseline_memory is None

    def test_custom_interval(self, tmp_path):
        """自定义间隔"""
        log_file = str(tmp_path / "test_mem.log")
        monitor = MemoryMonitor(interval_minutes=10, log_file=log_file)
        assert monitor.interval == 10 * 60

    def test_log_file_created(self, tmp_path):
        """日志目录应自动创建"""
        log_dir = tmp_path / "sub" / "dir"
        log_file = str(log_dir / "monitor.log")
        monitor = MemoryMonitor(interval_minutes=60, log_file=log_file)
        # 目录应已被创建（__init__ 中 os.makedirs）
        assert log_dir.exists()

    def test_logger_configured(self, tmp_path):
        """logger 应已配置"""
        log_file = str(tmp_path / "test.log")
        monitor = MemoryMonitor(log_file=log_file)
        assert monitor.logger is not None
        assert monitor.logger.name == 'MemoryMonitor'


# ============================================================================
# TestMemoryMonitorStartStop
# ============================================================================

class TestMemoryMonitorStartStop:
    """start() / stop() 方法测试"""

    def test_start_sets_running_true(self, tmp_path):
        """start() 后 running 应为 True"""
        log_file = str(tmp_path / "test.log")
        monitor = MemoryMonitor(interval_minutes=999, log_file=log_file)
        monitor.start()
        assert monitor.running is True
        monitor.stop()

    def test_start_creates_thread(self, tmp_path):
        """start() 应创建并启动 monitor_thread"""
        log_file = str(tmp_path / "test.log")
        monitor = MemoryMonitor(interval_minutes=999, log_file=log_file)
        monitor.start()
        assert monitor.monitor_thread is not None
        assert monitor.monitor_thread.is_alive()
        monitor.stop()

    def test_start_thread_is_daemon(self, tmp_path):
        """监控线程应为 daemon 线程，不阻塞程序退出"""
        log_file = str(tmp_path / "test.log")
        monitor = MemoryMonitor(interval_minutes=999, log_file=log_file)
        monitor.start()
        assert monitor.monitor_thread.daemon is True
        monitor.stop()

    def test_stop_sets_running_false(self, tmp_path):
        """stop() 后 running 应为 False"""
        log_file = str(tmp_path / "test.log")
        monitor = MemoryMonitor(interval_minutes=999, log_file=log_file)
        monitor.start()
        monitor.stop()
        assert monitor.running is False

    def test_stop_terminates_thread(self, tmp_path):
        """stop() 应及时终止监控线程"""
        log_file = str(tmp_path / "test.log")
        monitor = MemoryMonitor(interval_minutes=999, log_file=log_file)
        monitor.start()
        thread = monitor.monitor_thread
        monitor.stop()
        # 等待不超过 3 秒
        thread.join(timeout=3)
        assert not thread.is_alive()

    def test_double_start_safe(self, tmp_path):
        """start() 重复调用不应产生多余线程"""
        log_file = str(tmp_path / "test.log")
        monitor = MemoryMonitor(interval_minutes=999, log_file=log_file)
        monitor.start()
        thread1 = monitor.monitor_thread
        monitor.start()  # 第二次 start
        thread2 = monitor.monitor_thread
        # 如果实现正确，不应重复启动（第二次 start 因 running==True 被跳过）
        assert thread1 is thread2
        monitor.stop()

    def test_stop_without_start_safe(self, tmp_path):
        """未 start 直接 stop 不应报错"""
        log_file = str(tmp_path / "test.log")
        monitor = MemoryMonitor(interval_minutes=999, log_file=log_file)
        monitor.stop()  # 不应抛出异常
        assert monitor.running is False


# ============================================================================
# TestMemoryMonitorGetCurrentMemory
# ============================================================================

class TestMemoryMonitorGetCurrentMemory:
    """get_current_memory() 方法测试"""

    def test_returns_positive_float(self, tmp_path):
        """当前内存使用应为正浮点数（MB）"""
        log_file = str(tmp_path / "test.log")
        monitor = MemoryMonitor(log_file=log_file)
        memory_mb = monitor.get_current_memory()
        assert isinstance(memory_mb, float)
        assert memory_mb > 0

    def test_returns_reasonable_value(self, tmp_path):
        """内存值应在合理范围内（1MB ~ 32GB）"""
        log_file = str(tmp_path / "test.log")
        monitor = MemoryMonitor(log_file=log_file)
        memory_mb = monitor.get_current_memory()
        assert 1 < memory_mb < 32 * 1024  # 1 MB ～ 32 GB

    def test_returns_zero_on_psutil_error(self, tmp_path):
        """psutil 异常时应安全返回 0"""
        log_file = str(tmp_path / "test.log")
        monitor = MemoryMonitor(log_file=log_file)
        with patch('psutil.Process', side_effect=Exception("psutil error")):
            result = monitor.get_current_memory()
        assert result == 0

    def test_multiple_calls_consistent(self, tmp_path):
        """连续调用两次，结果应接近（同一进程）"""
        log_file = str(tmp_path / "test.log")
        monitor = MemoryMonitor(log_file=log_file)
        m1 = monitor.get_current_memory()
        m2 = monitor.get_current_memory()
        # 两次调用间内存波动应在 100 MB 以内
        assert abs(m1 - m2) < 100


# ============================================================================
# TestGetMemoryMonitorSingleton
# ============================================================================

class TestGetMemoryMonitorSingleton:
    """get_memory_monitor() 单例模式测试"""

    def test_returns_memory_monitor_instance(self):
        """返回值应为 MemoryMonitor 实例"""
        monitor = get_memory_monitor()
        assert isinstance(monitor, MemoryMonitor)

    def test_singleton_same_instance(self):
        """多次调用应返回同一实例"""
        m1 = get_memory_monitor()
        m2 = get_memory_monitor()
        assert m1 is m2

    def test_singleton_thread_safety(self):
        """单线程多次调用应返回同一实例（注：当前实现无锁，并发环境下不保证强一致）"""
        # 串行多次调用：保证返回同一实例
        m1 = get_memory_monitor()
        m2 = get_memory_monitor()
        m3 = get_memory_monitor()
        assert m1 is m2
        assert m2 is m3

    def test_custom_interval_first_call(self):
        """第一次调用时可传入自定义间隔"""
        monitor = get_memory_monitor(interval_minutes=30)
        assert monitor.interval == 30 * 60

    def test_second_call_ignores_interval(self):
        """单例已创建后，第二次调用忽略 interval 参数"""
        m1 = get_memory_monitor(interval_minutes=30)
        m2 = get_memory_monitor(interval_minutes=5)  # 不同 interval
        assert m1 is m2
        assert m2.interval == 30 * 60  # 应保持第一次的值


# ============================================================================
# TestMemoryMonitorLoopBehavior
# ============================================================================

class TestMemoryMonitorLoopBehavior:
    """监控循环行为测试（使用快速间隔验证周期性运行）"""

    def test_monitor_loop_calls_log_multiple_times(self, tmp_path):
        """监控线程应多次调用 _log_memory_usage"""
        log_file = str(tmp_path / "test.log")
        monitor = MemoryMonitor(interval_minutes=0.001, log_file=log_file)  # 0.06s

        call_count = [0]
        original_log = monitor._log_memory_usage

        def counting_log():
            call_count[0] += 1
            original_log()

        monitor._log_memory_usage = counting_log
        monitor.start()
        time.sleep(0.3)  # 等待约4-5次循环
        monitor.stop()

        assert call_count[0] >= 2, f"预计至少2次调用，实际 {call_count[0]} 次"

    def test_stop_event_interrupts_sleep(self, tmp_path):
        """stop() 应立即唤醒正在等待中的监控线程，而不是等满 interval"""
        log_file = str(tmp_path / "test.log")
        monitor = MemoryMonitor(interval_minutes=60, log_file=log_file)  # 3600s 间隔
        monitor.start()
        time.sleep(0.1)  # 确保线程进入 wait()

        start_time = time.time()
        monitor.stop()
        elapsed = time.time() - start_time

        # stop() 应在不超过 2 秒内完成（不是等待 3600 秒）
        assert elapsed < 2.0, f"stop() 耗时 {elapsed:.2f}s，超过 2s 阈值"

    def test_baseline_memory_set_on_first_log(self, tmp_path):
        """首次 _log_memory_usage 调用应设置 baseline_memory"""
        log_file = str(tmp_path / "test.log")
        monitor = MemoryMonitor(interval_minutes=999, log_file=log_file)
        assert monitor.baseline_memory is None
        monitor._log_memory_usage()
        assert monitor.baseline_memory is not None
        assert monitor.baseline_memory > 0
