"""
全工程共享常量
集中定义物理模型参数、合规标准、场景需求，消除多处重复定义。

使用方式:
    from core.constants import WALL_ATTENUATION, ENVIRONMENT_FACTORS, COMPLIANCE_STANDARDS
"""

# ─────────────────────────────────────────────
# 障碍物材料衰减値 (dB) — 信号传播模型
# 原先分散在: deployment.py / heatmap.py
# ─────────────────────────────────────────────
WALL_ATTENUATION: dict = {
    # 重型墙体 (>15 dB)
    '钢筋混凝土': 20,
    '金属板':    30,
    '隔音墙':    25,

    # 中型墙体 (10–15 dB)
    '混凝土墙':  15,
    '承重砖墙':  12,
    '砖墙':      10,

    # 轻型墙体 (5–9 dB)
    '石膏板墙':   5,
    '木质隔断':   4,
    '玻璃幕墙':   3,

    # 轻量障碍 (<5 dB)
    '木门':       3,
    '玻璃门':     2,
    '玻璃':       2,
}

# heatmap.py 用于下拉列表的简化视图（子集，不修改 WALL_ATTENUATION）
WALL_ATTENUATION_BASIC: dict = {
    '木门':      3,
    '石膏板墙':  5,
    '砖墙':     10,
    '混凝土墙': 15,
    '金属':     20,
}

# ─────────────────────────────────────────────
# 环境干扰因子 — 信号路径损耗修正
# 原先定义在: deployment.py SignalPropagationModel
# ─────────────────────────────────────────────
ENVIRONMENT_FACTORS: dict = {
    'office':   1.2,   # 办公室：隔断多
    'home':     1.0,   # 家庭：标准
    'factory':  1.5,   # 工厂：金属设备多
    'hospital': 1.1,   # 医院：轻质隔墙
    'school':   1.3,   # 学校：人群密集
}

# ─────────────────────────────────────────────
# 热力图合规标准（heatmap.py COMPLIANCE_STANDARDS）
# 保留在 heatmap.py 中作为类属性，这里同步一份供跨模块引用
# ─────────────────────────────────────────────
COMPLIANCE_STANDARDS: dict = {
    '办公室': {'min_signal': 70, 'coverage_rate': 95, 'overlap_max': 3},
    '学校':   {'min_signal': 75, 'coverage_rate': 98, 'overlap_max': 2},
    '医院':   {'min_signal': 80, 'coverage_rate': 99, 'overlap_max': 1},
}

# ─────────────────────────────────────────────
# 覆盖分析场景需求（coverage_analyzer.py SCENARIO_REQUIREMENTS）
# 保留在 coverage_analyzer.py 中作为类属性，这里同步一份供跨模块引用
# ─────────────────────────────────────────────
SCENARIO_REQUIREMENTS: dict = {
    '高密度办公': {
        'min_signal':           -60,
        'coverage_rate':         95,
        'max_ap_overlap':         3,
        'channel_bandwidth':     40,
        'recommended_standard': 'WiFi 6',
    },
    '普通办公': {
        'min_signal':           -65,
        'coverage_rate':         90,
        'max_ap_overlap':         2,
        'channel_bandwidth':     40,
        'recommended_standard': 'WiFi 5',
    },
    '教育培训': {
        'min_signal':           -60,
        'coverage_rate':         98,
        'max_ap_overlap':         2,
        'channel_bandwidth':     80,
        'recommended_standard': 'WiFi 6',
    },
    '医疗健康': {
        'min_signal':           -55,
        'coverage_rate':         99,
        'max_ap_overlap':         1,
        'channel_bandwidth':     80,
        'recommended_standard': 'WiFi 6E',
    },
    '工业制造': {
        'min_signal':           -70,
        'coverage_rate':         85,
        'max_ap_overlap':         2,
        'channel_bandwidth':     20,
        'recommended_standard': 'WiFi 4/5',
    },
}
