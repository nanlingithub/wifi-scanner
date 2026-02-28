# -*- mode: python ; coding: utf-8 -*-
"""
WiFi Professional 打包配置文件
使用 PyInstaller 将程序打包成独立的 exe 文件

使用方法:
    pyinstaller wifi_professional.spec

生成文件:
    dist/WiFi专业工具.exe
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
    
    # YAML 支持（必需）
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
    
    # 安全模块
    'wifi_modules.security',
    'wifi_modules.security.scoring',
    'wifi_modules.security.vulnerability',
    'wifi_modules.security.dns_enhanced',
    'wifi_modules.security.password',
    'wifi_modules.security.dynamic_scoring',
    
    # 分析模块
    'wifi_modules.analytics',
    'wifi_modules.analytics.channel_utilization',
    'wifi_modules.analytics.signal_trend',
    
    # 告警模块
    'wifi_modules.alerts',
    'wifi_modules.alerts.signal_alert',
]

# 收集所有数据文件
datas = [
    # 配置文件
    ('config.json', '.'),
    
    # 程序图标文件
    ('wifi_icon.ico', '.'),
    
    # matplotlib 数据文件
    *collect_data_files('matplotlib'),
    
    # reportlab 数据文件
    *collect_data_files('reportlab'),
    
    # sklearn 数据文件
    *collect_data_files('sklearn'),
]

# 需要打包的二进制文件
binaries = []

a = Analysis(
    ['wifi_professional.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的模块以减小文件大小
        'IPython',
        'jupyter',
        'notebook',
        'sphinx',
        'pytest',
        # 注意：不要排除 unittest，它是 numpy/scipy 需要的标准库
        # 'unittest',  # 已移除 - numpy.testing 需要
        'test',
        'tests',
        # 'distutils',  # 已移除 - setuptools 需要
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure, 
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='WiFi专业工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # 使用 UPX 压缩
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='wifi_icon.ico',  # WiFi专业工具图标
    version_file=None,  # 可以添加版本信息文件
)

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
