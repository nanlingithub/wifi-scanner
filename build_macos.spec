# -*- mode: python ; coding: utf-8 -*-
"""
WiFi Professional macOS 打包配置文件
使用 PyInstaller 将程序打包成 macOS .app 应用

使用方法:
    pyinstaller build_macos.spec

生成文件:
    dist/WiFi专业工具.app
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# 收集所有依赖的子模块
hiddenimports = [
    # tkinter 相关
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    'tkinter.filedialog',
    'tkinter.scrolledtext',
    
    # matplotlib 后端
    'matplotlib.backends.backend_tkagg',
    'matplotlib.backends.backend_agg',
    
    # scipy 子模块
    'scipy.special',
    'scipy.special.cython_special',
    'scipy.interpolate',
    'scipy.spatial',
    'scipy.ndimage',
    'scipy._lib',
    'scipy._lib._array_api',
    'scipy._lib.array_api_compat',
    
    # sklearn 子模块
    'sklearn.utils._weight_vector',
    'sklearn.neighbors._partition_nodes',
    
    # 其他依赖
    'psutil',
    'numpy',
    'pandas',
    'networkx',
    'PIL',
    'PIL.Image',
    'reportlab',
    'reportlab.pdfbase.ttfonts',
    'reportlab.pdfbase.pdfmetrics',
    'reportlab.lib.pagesizes',
    'openpyxl',
    
    # YAML 支持
    'yaml',
    'yaml.loader',
    'yaml.dumper',
    'yaml.resolver',
    'yaml.scanner',
    'yaml.parser',
    'yaml.composer',
    'yaml.constructor',
    'yaml.emitter',
    'yaml.serializer',
    'yaml.representer',
    '_yaml',
    
    # 项目模块
    'core',
    'core.admin_utils',
    'core.connectivity',
    'core.memory_monitor',
    'core.utils',
    'core.wifi_analyzer',
    'core.wifi_vendor_detector',
    
    'wifi_modules',
    'wifi_modules.config_loader',
    'wifi_modules.config_manager',
    'wifi_modules.language',
    'wifi_modules.logger',
    'wifi_modules.theme',
    'wifi_modules.font_config',
    'wifi_modules.icon_system',
    'wifi_modules.cache_manager',
    
    # 功能模块
    'wifi_modules.network_overview',
    'wifi_modules.channel_analysis',
    'wifi_modules.realtime_monitor_optimized',
    'wifi_modules.heatmap',
    'wifi_modules.deployment',
    'wifi_modules.security_tab',
    'wifi_modules.enterprise_report_tab',
    'wifi_modules.interference_locator_tab',
    'wifi_modules.wifi6_analyzer_tab',
    
    # 子模块
    'wifi_modules.security',
    'wifi_modules.security.vulnerability_detector',
    'wifi_modules.security.password_analyzer',
    'wifi_modules.security.dns_detector',
    'wifi_modules.security.evil_twin_detector',
    'wifi_modules.security.ssid_spoof_detector',
    'wifi_modules.security.pmf_detector',
    'wifi_modules.security.krack_detector',
    'wifi_modules.security.wps_detector',
    'wifi_modules.security.security_scoring',
    'wifi_modules.security.dns_enhanced',
    'wifi_modules.security.dynamic_scoring',
    
    'wifi_modules.analytics',
    'wifi_modules.analytics.channel_utilization',
    
    'wifi_modules.alerts',
    'wifi_modules.alerts.signal_alert',
    
    'wifi_modules.enterprise_reports',
]

# 收集数据文件
datas = []

# 添加图标文件
if os.path.exists('wifi_icon.icns'):
    datas.append(('wifi_icon.icns', '.'))
elif os.path.exists('wifi_icon.ico'):
    datas.append(('wifi_icon.ico', '.'))

# 添加配置文件
if os.path.exists('config.json'):
    datas.append(('config.json', '.'))

# 添加配置目录
if os.path.exists('config'):
    datas.append(('config', 'config'))

# 分析主程序
a = Analysis(
    ['wifi_professional.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        'pytest_cov',
        'sphinx',
        'setuptools',
        'pip',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# PYZ 打包
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# EXE 打包（对于 macOS，这实际上是一个可执行文件）
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='WiFi专业工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# 收集依赖
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WiFi专业工具',
)

# 创建 macOS .app 包
app = BUNDLE(
    coll,
    name='WiFi专业工具.app',
    icon='wifi_icon.icns' if os.path.exists('wifi_icon.icns') else None,
    bundle_identifier='com.wifiprofessional.app',
    info_plist={
        'CFBundleName': 'WiFi专业工具',
        'CFBundleDisplayName': 'WiFi Professional',
        'CFBundleVersion': '1.7.2',
        'CFBundleShortVersionString': '1.7.2',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.13.0',  # macOS High Sierra or later
        'NSLocationWhenInUseUsageDescription': '需要访问WiFi功能以扫描网络',
    },
)
