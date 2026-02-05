"""
修复matplotlib中文显示问题的辅助模块
"""

import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager
import platform

def configure_chinese_font():
    """配置matplotlib中文字体"""
    system = platform.system()
    
    if system == 'Windows':
        # Windows系统使用微软雅黑
        fonts = ['Microsoft YaHei', 'SimHei', 'KaiTi', 'FangSong']
    elif system == 'Darwin':  # macOS
        fonts = ['PingFang SC', 'STHeiti', 'STSong']
    else:  # Linux
        fonts = ['WenQuanYi Micro Hei', 'Droid Sans Fallback', 'AR PL UMing CN']
    
    # 尝试设置字体
    for font in fonts:
        try:
            # 检查字体是否可用
            available_fonts = [f.name for f in font_manager.fontManager.ttflist]
            if font in available_fonts:
                matplotlib.rcParams['font.sans-serif'] = [font]
                matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
                return True
        except Exception as e:
            continue
    
    # 如果都不可用，使用默认字体（静默处理）
    matplotlib.rcParams['axes.unicode_minus'] = False
    return False

# 自动配置
configure_chinese_font()
