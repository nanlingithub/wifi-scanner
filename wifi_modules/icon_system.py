"""
WiFi专业工具 - 图标美化升级方案
专业图标设计与实施
"""

# 专业图标设计系统
# 基于Unicode Emoji + Segoe UI Symbol混合方案

PROFESSIONAL_ICONS = {
    # === 主导航标签页图标 ===
    'network_overview': '🌐',      # 网络概览
    'channel_analysis': '📊',      # 信道分析
    'realtime_monitor': '📡',      # 实时监控
    'heatmap': '🗺️',               # 信号热力图（更清晰的地图图标）
    'deployment': '📍',            # 部署优化
    'security': '🔒',              # 安全检测
    'performance': '⚡',            # 性能测试
    
    # === 功能操作图标 ===
    'scan': '🔍',                  # 扫描
    'start': '▶️',                 # 开始
    'stop': '⏸️',                  # 停止
    'pause': '⏸️',                 # 暂停
    'refresh': '🔄',               # 刷新
    'export': '📤',                # 导出
    'import': '📥',                # 导入
    'save': '💾',                  # 保存
    'delete': '🗑️',                # 删除
    'clear': '🧹',                 # 清空
    'settings': '⚙️',              # 设置
    'edit': '✏️',                  # 编辑
    'add': '➕',                   # 添加
    'remove': '➖',                # 移除
    'copy': '📋',                  # 复制
    'download': '⬇️',              # 下载
    'upload': '⬆️',                # 上传
    
    # === 数据可视化图标 ===
    'chart_line': '📈',            # 趋势图
    'chart_bar': '📊',             # 柱状图
    'chart_pie': '🥧',             # 饼图
    'chart_area': '📉',            # 面积图
    'table': '📋',                 # 表格
    'list': '📝',                  # 列表
    'grid': '⊞',                   # 网格
    
    # === 状态指示图标 ===
    'success': '✅',               # 成功
    'error': '❌',                 # 错误
    'warning': '⚠️',               # 警告
    'info': 'ℹ️',                  # 信息
    'question': '❓',              # 问题
    'check': '✔️',                 # 勾选
    'cross': '✖️',                 # 叉号
    'star': '⭐',                  # 星标
    'flag': '🚩',                  # 标记
    'bell': '🔔',                  # 通知
    'alert': '🚨',                 # 警报
    
    # === 网络相关图标 ===
    'wifi': '📶',                  # WiFi信号
    'router': '🌐',                # 路由器
    'signal': '📡',                # 信号
    'antenna': '📡',               # 天线
    'network': '🌐',               # 网络
    'cloud': '☁️',                 # 云
    'server': '🖥️',                # 服务器
    'computer': '💻',              # 计算机
    'device': '📱',                # 设备
    
    # === 工具功能图标 ===
    'tool': '🔧',                  # 工具
    'wrench': '🔧',                # 扳手
    'hammer': '🔨',                # 锤子
    'search': '🔎',                # 搜索
    'filter': '🔽',                # 过滤
    'sort': '↕️',                  # 排序
    'zoom_in': '🔍+',              # 放大
    'zoom_out': '🔍-',             # 缩小
    
    # === 文件操作图标 ===
    'file': '📄',                  # 文件
    'folder': '📁',                # 文件夹
    'document': '📃',              # 文档
    'image': '🖼️',                 # 图片
    'pdf': '📕',                   # PDF
    'csv': '📊',                   # CSV
    'json': '📝',                  # JSON
    
    # === 特殊功能图标 ===
    'lock': '🔒',                  # 锁定
    'unlock': '🔓',                # 解锁
    'shield': '🛡️',                # 防护
    'key': '🔑',                   # 密钥
    'lightning': '⚡',             # 闪电/快速
    'rocket': '🚀',                # 火箭/启动
    'target': '🎯',                # 目标
    'compass': '🧭',               # 指南针
    'map': '🗺️',                   # 地图
    'location': '📍',              # 位置
    'pin': '📌',                   # 图钉
    
    # === 时间相关图标 ===
    'clock': '🕐',                 # 时钟
    'timer': '⏱️',                 # 计时器
    'hourglass': '⏳',             # 沙漏
    'calendar': '📅',              # 日历
    
    # === 状态徽章图标 ===
    'online': '🟢',                # 在线（绿点）
    'offline': '🔴',               # 离线（红点）
    'busy': '🟡',                  # 忙碌（黄点）
    'idle': '⚪',                  # 空闲（白点）
    
    # === 质量等级图标 ===
    'excellent': '🌟',             # 优秀
    'good': '👍',                  # 良好
    'average': '👌',               # 中等
    'poor': '👎',                  # 较差
    'bad': '💔',                   # 很差
}

# 图标颜色方案（用于Canvas绘制或HTML）
ICON_COLORS = {
    'primary': '#3498db',          # 主色调-蓝色
    'success': '#2ecc71',          # 成功-绿色
    'warning': '#f39c12',          # 警告-橙色
    'danger': '#e74c3c',           # 危险-红色
    'info': '#3498db',             # 信息-蓝色
    'secondary': '#95a5a6',        # 次要-灰色
}

# 按钮样式配置
BUTTON_ICON_MAP = {
    '开始扫描': ('scan', 'primary'),
    '停止扫描': ('stop', 'danger'),
    '刷新': ('refresh', 'primary'),
    '导出': ('export', 'success'),
    '导入': ('import', 'info'),
    '保存': ('save', 'success'),
    '删除': ('delete', 'danger'),
    '清空': ('clear', 'warning'),
    '设置': ('settings', 'secondary'),
    '编辑': ('edit', 'info'),
    '性能测试': ('performance', 'warning'),
    '安全检测': ('security', 'danger'),
    '信号热力图': ('heatmap', 'success'),
    '部署优化': ('deployment', 'primary'),
}

# 标签页配置
TAB_CONFIG = {
    'overview': {
        'icon': '🌐',
        'text': '网络概览',
        'color': '#3498db'
    },
    'channel': {
        'icon': '📊',
        'text': '信道分析',
        'color': '#9b59b6'
    },
    'monitor': {
        'icon': '📡',
        'text': '实时监控',
        'color': '#e74c3c'
    },
    'heatmap': {
        'icon': '🗺️',
        'text': '信号热力图',
        'color': '#16a085'
    },
    'deployment': {
        'icon': '📍',
        'text': '部署优化',
        'color': '#f39c12'
    },
    'security': {
        'icon': '🔒',
        'text': '安全检测',
        'color': '#c0392b'
    },
}

def get_icon(name, fallback=''):
    """获取图标"""
    return PROFESSIONAL_ICONS.get(name, fallback)

def get_colored_icon(name, color=None):
    """获取彩色图标（用于Canvas）"""
    icon = get_icon(name)
    if color and color in ICON_COLORS:
        return f"{icon} {ICON_COLORS[color]}"
    return icon

def get_button_style(button_text):
    """根据按钮文本获取图标和样式"""
    for key, (icon_name, style) in BUTTON_ICON_MAP.items():
        if key in button_text:
            return get_icon(icon_name), style
    return '', 'secondary'
