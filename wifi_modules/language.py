#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
应用配置模块
提供版本信息和应用名称
"""

# 版本信息
VERSION = "V26_1.0"
DEVELOPER = "NL@China_SZ"
APP_NAME = "WiFi专业分析工具"


def get_app_title():
    """获取应用标题"""
    return f"{APP_NAME} - v{VERSION}"


def get_about_info():
    """获取关于信息"""
    return {
        'title': '关于',
        'app': APP_NAME,
        'version': f'版本: {VERSION}',
        'developer': f'开发者: {DEVELOPER}',
        'description': '专业的WiFi网络分析工具',
        'features': '''功能特性:
• WiFi网络扫描与信号分析
• 全球8地区信道分析
• 实时频谱监控（含信号警报）
• 信号趋势分析（24小时历史）
• 信道利用率仪表盘
• WiFi性能基准测试（网速测试）
• WiFi信号热力图生成
• 部署优化与AP推荐
• 安全检测与优化建议

技术支持:
• Python 3.11+
• tkinter GUI框架
• matplotlib可视化
• scipy科学计算
• IEEE OUI数据库''',
        'copyright': f'© 2026 {DEVELOPER}. All rights reserved.'
    }
