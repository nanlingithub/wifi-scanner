#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/admin_utils.py 单元测试
覆盖: is_admin, restart_as_admin, check_admin_rights, require_admin, get_admin_status_text
"""

import sys
import pytest
from unittest.mock import patch, MagicMock, call

# 确保导入路径正确
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.admin_utils import (
    is_admin,
    restart_as_admin,
    check_admin_rights,
    require_admin,
    get_admin_status_text,
)


# ============================================================================
# TestIsAdmin
# ============================================================================

class TestIsAdmin:
    """is_admin() 函数测试"""

    def test_is_admin_returns_true_when_elevated(self):
        """IsUserAnAdmin() 返回非零时 is_admin() 应为真值"""
        with patch('ctypes.windll') as mock_windll:
            mock_windll.shell32.IsUserAnAdmin.return_value = 1
            assert is_admin()  # ctypes BOOL: 1 == True（truthy 即可）

    def test_is_admin_returns_false_when_not_elevated(self):
        """IsUserAnAdmin() 返回 0 时 is_admin() 应返回 False"""
        with patch('ctypes.windll') as mock_windll:
            mock_windll.shell32.IsUserAnAdmin.return_value = 0
            result = is_admin()
            assert result == False  # noqa: E712 — 兼容 int 0 / bool False

    def test_is_admin_returns_false_on_exception(self):
        """IsUserAnAdmin() 抛出异常时 is_admin() 应安全返回 False"""
        with patch('ctypes.windll') as mock_windll:
            mock_windll.shell32.IsUserAnAdmin.side_effect = AttributeError("windll unavailable")
            assert is_admin() is False

    def test_is_admin_returns_false_on_oserror(self):
        """OSError 时也应安全返回 False"""
        with patch('ctypes.windll') as mock_windll:
            mock_windll.shell32.IsUserAnAdmin.side_effect = OSError("No windll")
            assert is_admin() is False


# ============================================================================
# TestRestartAsAdmin
# ============================================================================

class TestRestartAsAdmin:
    """restart_as_admin() 函数测试"""

    def test_restart_as_admin_python_mode(self):
        """以 .py 脚本模式重启时调用 ShellExecuteW"""
        with patch('ctypes.windll') as mock_windll, \
             patch('sys.argv', ['test_script.py']), \
             patch('sys.executable', 'python.exe'):
            mock_windll.shell32.ShellExecuteW.return_value = 42  # > 32 表示成功
            result = restart_as_admin()
            assert result is True
            mock_windll.shell32.ShellExecuteW.assert_called_once()
            # 验证 runas 动词被传入
            args = mock_windll.shell32.ShellExecuteW.call_args[0]
            assert 'runas' in args

    def test_restart_as_admin_exe_mode(self):
        """以 .exe 模式重启时调用 ShellExecuteW"""
        with patch('ctypes.windll') as mock_windll, \
             patch('sys.argv', ['wifi_professional.exe']), \
             patch('sys.executable', 'wifi_professional.exe'):
            mock_windll.shell32.ShellExecuteW.return_value = 42
            result = restart_as_admin()
            assert result is True

    def test_restart_as_admin_returns_false_on_exception(self):
        """ShellExecuteW 抛出异常时返回 False"""
        with patch('ctypes.windll') as mock_windll, \
             patch('sys.argv', ['script.py']), \
             patch('sys.executable', 'python.exe'):
            mock_windll.shell32.ShellExecuteW.side_effect = Exception("UAC denied")
            result = restart_as_admin()
            assert result is False


# ============================================================================
# TestCheckAdminRights
# ============================================================================

class TestCheckAdminRights:
    """check_admin_rights() 函数测试"""

    def test_check_admin_rights_already_admin(self):
        """已有管理员权限时直接返回 True，不显示对话框"""
        with patch('core.admin_utils.is_admin', return_value=True), \
             patch('core.admin_utils.messagebox') as mock_mb:
            result = check_admin_rights("测试功能")
            assert result is True
            mock_mb.askyesno.assert_not_called()

    def test_check_admin_rights_no_prompt(self):
        """show_prompt=False 时不显示对话框，直接返回 False"""
        with patch('core.admin_utils.is_admin', return_value=False), \
             patch('core.admin_utils.messagebox') as mock_mb:
            result = check_admin_rights("测试功能", show_prompt=False)
            assert result is False
            mock_mb.askyesno.assert_not_called()

    def test_check_admin_rights_user_declines(self):
        """用户点击'否'时返回 False"""
        with patch('core.admin_utils.is_admin', return_value=False), \
             patch('core.admin_utils.messagebox') as mock_mb:
            mock_mb.askyesno.return_value = False
            result = check_admin_rights("测试功能", show_prompt=True)
            assert result is False
            mock_mb.askyesno.assert_called_once()

    def test_check_admin_rights_user_accepts_restart_success(self):
        """用户点击'是'且重启成功时调用 sys.exit(0)"""
        with patch('core.admin_utils.is_admin', return_value=False), \
             patch('core.admin_utils.messagebox') as mock_mb, \
             patch('core.admin_utils.restart_as_admin', return_value=True), \
             patch('sys.exit') as mock_exit:
            mock_mb.askyesno.return_value = True
            check_admin_rights("测试功能", show_prompt=True)
            mock_exit.assert_called_once_with(0)

    def test_check_admin_rights_user_accepts_restart_fails(self):
        """用户点击'是'但重启失败时显示错误提示并返回 False"""
        with patch('core.admin_utils.is_admin', return_value=False), \
             patch('core.admin_utils.messagebox') as mock_mb, \
             patch('core.admin_utils.restart_as_admin', return_value=False):
            mock_mb.askyesno.return_value = True
            result = check_admin_rights("测试功能", show_prompt=True)
            assert result is False
            mock_mb.showerror.assert_called_once()

    def test_check_admin_rights_default_feature_name(self):
        """默认 feature_name 为 '此功能'"""
        with patch('core.admin_utils.is_admin', return_value=False), \
             patch('core.admin_utils.messagebox') as mock_mb:
            mock_mb.askyesno.return_value = False
            check_admin_rights()  # 使用默认参数
            call_args = mock_mb.askyesno.call_args[0]
            # 提示文本应包含"此功能"
            assert '此功能' in call_args[1]


# ============================================================================
# TestRequireAdmin
# ============================================================================

class TestRequireAdmin:
    """require_admin 装饰器测试"""

    def test_require_admin_allows_when_elevated(self):
        """有管理员权限时正常执行函数"""
        @require_admin
        def privileged_func():
            return "success"

        with patch('core.admin_utils.is_admin', return_value=True):
            result = privileged_func()
        assert result == "success"

    def test_require_admin_blocks_when_not_elevated(self):
        """无管理员权限时返回 None 并显示警告"""
        @require_admin
        def privileged_func():
            return "success"

        with patch('core.admin_utils.is_admin', return_value=False), \
             patch('core.admin_utils.messagebox') as mock_mb:
            result = privileged_func()
        assert result is None
        mock_mb.showwarning.assert_called_once()

    def test_require_admin_preserves_function_name(self):
        """装饰器应保留原函数的 __name__"""
        @require_admin
        def my_special_function():
            pass

        assert my_special_function.__name__ == 'my_special_function'

    def test_require_admin_preserves_docstring(self):
        """装饰器应保留原函数的 __doc__"""
        @require_admin
        def documented_func():
            """这是文档字符串"""
            pass

        assert documented_func.__doc__ == "这是文档字符串"

    def test_require_admin_passes_args_when_elevated(self):
        """有权限时，参数应正确传递给原函数"""
        @require_admin
        def func_with_args(a, b, c=10):
            return a + b + c

        with patch('core.admin_utils.is_admin', return_value=True):
            result = func_with_args(1, 2, c=3)
        assert result == 6

    def test_require_admin_with_self_method(self):
        """装饰器作用于类方法时 self 参数正常传递"""
        class MyService:
            @require_admin
            def admin_action(self):
                return f"action by {self.__class__.__name__}"

        svc = MyService()
        with patch('core.admin_utils.is_admin', return_value=True):
            result = svc.admin_action()
        assert result == "action by MyService"


# ============================================================================
# TestGetAdminStatusText
# ============================================================================

class TestGetAdminStatusText:
    """get_admin_status_text() 函数测试"""

    def test_returns_admin_text_when_elevated(self):
        """有管理员权限时返回包含'管理员'的文本"""
        with patch('core.admin_utils.is_admin', return_value=True):
            text = get_admin_status_text()
        assert '管理员' in text

    def test_returns_restricted_text_when_not_elevated(self):
        """无管理员权限时返回包含'受限'的文本"""
        with patch('core.admin_utils.is_admin', return_value=False):
            text = get_admin_status_text()
        assert '受限' in text

    def test_return_type_is_string(self):
        """返回值应为字符串"""
        with patch('core.admin_utils.is_admin', return_value=True):
            assert isinstance(get_admin_status_text(), str)

    def test_admin_and_restricted_texts_differ(self):
        """管理员模式与受限模式的文本应不同"""
        with patch('core.admin_utils.is_admin', return_value=True):
            admin_text = get_admin_status_text()
        with patch('core.admin_utils.is_admin', return_value=False):
            restricted_text = get_admin_status_text()
        assert admin_text != restricted_text
