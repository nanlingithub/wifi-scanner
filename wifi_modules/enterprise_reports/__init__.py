"""
企业报告生成系统 v2.0
统一的PDF/Excel/JSON报告生成框架

主要组件：
- PDFGenerator: 统一PDF生成器
- ReportCache: 智能缓存系统
- ChartManager: 图表资源管理
- Templates: 报告模板（信号分析、安全评估、PCI-DSS）
"""

from .pdf_generator import PDFGenerator, PDFGeneratorAsync
from .report_cache import ReportCache
from .chart_manager import ChartManager

__all__ = [
    'PDFGenerator',
    'PDFGeneratorAsync',
    'ReportCache',
    'ChartManager'
]

__version__ = '2.0.0'
