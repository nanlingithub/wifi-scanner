# -*- mode: python ; coding: utf-8 -*-
"""
WiFi Professional macOS 打包配置文件
使用 PyInstaller 将程序打包成 macOS .app 包

使用方法:
    pyinstaller wifi_professional_macos.spec --clean

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

# 收集数据文件
datas = [
    ('config.json', '.'),
    ('wifi_icon.ico', '.'),
    *collect_data_files('matplotlib'),
    *collect_data_files('reportlab'),
    *collect_data_files('sklearn'),
]

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
        'IPython',
        'jupyter',
        'notebook',
        'sphinx',
        'pytest',
        'test',
        'tests',
    ],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='WiFiProfessional',          # ASCII 名称，供 .app 内部二进制使用
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                        # macOS CI 环境通常不含 UPX
    console=False,                    # 无终端窗口（GUI 模式）
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,                        # 无 .icns 文件时使用系统默认图标
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='WiFiProfessional',
)

# 将 COLLECT 打包为标准 macOS .app Bundle
app = BUNDLE(
    coll,
    name='WiFi专业工具.app',
    icon=None,
    bundle_identifier='com.nanling.wifi-professional',
    info_plist={
        'CFBundleShortVersionString': '1.6.3',
        'CFBundleVersion': '1.6.3',
        'CFBundleDisplayName': 'WiFi专业工具',
        'CFBundleName': 'WiFi专业工具',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,   # 支持深色模式
        'LSUIElement': False,
        'NSHumanReadableCopyright': 'Copyright © 2024 NL@China_SZ',
    },
)
